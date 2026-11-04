import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN, ADMIN_ID, APP_VERSION, REPO_NAME
from utils.logging_config import setup_logging, get_logger
import background_tasks
from handlers import (
    start, fast_test, about, admin, quiz, quiz_world,
    order_bot, cert, balance, payment, review, pdf,
    news_handler, game, channel_access, misc
)
from database.db import create_tables
from database.migrations import migrate_legacy_data
from database import get_all_news, add_news_to_db


async def on_startup(bot: Bot):
    """Bot işə düşəndə fon tapşırıqları başladılır."""
    logger = get_logger(__name__)
    logger.info("Bot started successfully ✅")

    try:
        # Build info to admin for verification
        try:
            me = await bot.get_me()
            info = (
                f"✅ Bot start edildi\n"
                f"🤖 @{getattr(me, 'username', 'unknown')}\n"
                f"📦 Repo: {REPO_NAME}\n"
                f"🏷️ Versiya: {APP_VERSION}"
            )
            if ADMIN_ID:
                await bot.send_message(ADMIN_ID, info)
        except Exception:
            pass

        bot_chat_id = ADMIN_ID
        asyncio.create_task(background_tasks.send_regular_message(bot, bot_chat_id, interval=3600))
        logger.info("Background tasks scheduled")
    except Exception as e:
        logger.exception(f"Failed to start background tasks: {e}")


async def main():
    """Botu işə salır."""
    setup_logging()
    logger = get_logger(__name__)
    logger.info("Program başladı")

    # Database inicializasiya
    logger.info("Initializing PostgreSQL database")
    create_tables()
    migrate_legacy_data()
    logger.info("Database tables created successfully ✅")
    # Seed news if empty
    try:
        existing = get_all_news()
        if not existing:
            # Try to load from data/news.json
            seed_items = []
            try:
                import json
                from config import BASE_DIR
                news_path = os.path.join(BASE_DIR, "data", "news.json")
                if os.path.exists(news_path):
                    with open(news_path, "r", encoding="utf-8") as f:
                        seed_items = json.load(f) or []
            except Exception:
                seed_items = []

            if not seed_items:
                seed_items = [
                    {
                        "title": "Yeni: botda dizayn və menyu təkmilləşdi",
                        "content": (
                            "• Baş menyu 2 sütunlu olur\n"
                            "• RBCron qısayolları əlavə olundu\n"
                            "• Köstəbək oyunu info və qrup dəvət düyməsi\n"
                            "• Rəylər siyahısı daha səliqəli"
                        ),
                    }
                ]
            for item in seed_items:
                try:
                    add_news_to_db(item.get("title", "Xəbər"), item.get("content", ""), ADMIN_ID)
                except Exception:
                    pass
    except Exception:
        pass

    # Token yoxlaması
    if not BOT_TOKEN:
        logger.critical("BOT_TOKEN is not set!")
        raise ValueError("BOT_TOKEN is not set!")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Router-lar əlavə olunur
    for router in [
        start.router, fast_test.router, about.router, admin.router,
        quiz.router, quiz_world.router, order_bot.router, cert.router,
        balance.router, payment.payment_router, review.router, pdf.router,
        news_handler.router, game.router, channel_access.router, misc.misc_router
    ]:
        dp.include_router(router)

    logger.info("Router-lar əlavə olundu ✅")
    logger.info("Bot işə düşür...")

    # Aiogram 3.7 üçün startup event
    @dp.startup()
    async def _on_startup():
        await on_startup(bot)

    # Polling start
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        print("🚀 Railway-də bot işə düşür...")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("⚠️ Bot dayandırıldı (Keyboard Interrupt)")
    except Exception as e:
        import traceback
        print(f"❌ Botda xəta baş verdi: {e}")
        print(f"📋 Stack trace:")
        traceback.print_exc()
        raise  # Re-raise to ensure Railway sees the error
