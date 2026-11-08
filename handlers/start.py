from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
import asyncio
from database.queries import add_user
from database import get_all_news, get_news_by_id
from utils.logger_utils import log_event
from utils.timezone_utils import get_baku_time_str
from config import ADMIN_ID, APP_VERSION

router = Router()

# Təkrar admin bildirimlərini qarşısını almaq üçün
_recent_admin_notifications = set()

async def _clear_notification_after_delay(user_id: int):
    """5 dəqiqə sonra user_id-ni notification set-indən sil"""
    await asyncio.sleep(300)  # 5 dəqiqə = 300 saniyə
    _recent_admin_notifications.discard(user_id)


# Əsas menyu düymələri
def get_main_buttons():
    rows = [
        [
            InlineKeyboardButton(text="🧠 İnvestisiya testi", callback_data="fast_test_start"),
            InlineKeyboardButton(text="🗞️ İnvestisiya xəbərləri", callback_data="news_menu"),
        ],
        [
            InlineKeyboardButton(text="🪙 RBCron balansı", callback_data="balance_menu"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


# /start komandası
@router.message(F.text == "/start")
async def start_menu(message: Message, state: FSMContext):
    if message.chat.type != "private":
        if message.from_user is not None:
            try:
                me = await message.bot.get_me()
                username = getattr(me, "username", "")
                open_link = f"https://t.me/{username}" if username else "https://t.me/"
            except Exception:
                open_link = "https://t.me/"
            await message.reply(
                "ℹ Botun əsas menyusunu açmaq üçün şəxsi mesajda (/start) yazın.\n\n👉 "
                f"<a href='{open_link}'>Botu aç</a>",
                parse_mode="HTML"
            )
        return

    if message.from_user is not None:
        # 🔹 İstifadəçi əlavə et (lokal JSON-a)
        try:
            add_user(
                user_id=message.from_user.id,
                name=message.from_user.full_name or message.from_user.username or "Unknown",
                lang=message.from_user.language_code or "unknown"
            )
        except Exception as e:
            print(f"[DB ERROR] add_user failed: {e}")

        # 🔹 Aktivlik logu və adminə məlumat
        try:
            user = message.from_user
            display_name = user.full_name or user.username or str(user.id)
            lang = getattr(user, "language_code", None) or "unknown"
            log_event(user.id, display_name, "start", lang)

            # Admin bildirimi - təkrarlanmanın qarşısını al (5 dəqiqə ərzində)
            if ADMIN_ID and user.id not in _recent_admin_notifications:
                _recent_admin_notifications.add(user.id)
                # 5 dəqiqə sonra set-dən sil
                asyncio.create_task(_clear_notification_after_delay(user.id))
                
                now = get_baku_time_str()
                admin_text = (
                    f"🔔 Yeni istifadəçi gəldi — bot işə düşdü!\n"
                    f"👤 {display_name} (id: {user.id})\n"
                    f"🕒 {now} (Bakı vaxtı)\n"
                    f"🌐 Lang: {lang}"
                )
                try:
                    await message.bot.send_message(ADMIN_ID, admin_text)
                except Exception:
                    pass
        except Exception as e:
            print(f"[LOG ERROR] {e}")

    await message.answer("Menyu:", reply_markup=get_main_buttons())


# ✅ YENİLİKLƏR (lokal işlək versiya)
@router.callback_query(F.data == "news_menu")
async def news_menu_callback(callback: CallbackQuery):
    try:
        news_list = get_all_news()
    except Exception as e:
        await callback.message.answer(f"⚠️ Yaxın zamanda:\n{e}")
        await callback.answer()
        return

    if not news_list:
        await callback.message.answer("📭 Təzə xəbər yoxdur.")
        await callback.answer()
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=n['title'], callback_data=f"read_news:{n['id']}")]
            for n in news_list
        ]
    )
    await callback.message.answer("📈 Faydalı xəbər — son paylaşımlar:", reply_markup=kb)
    await callback.answer()


# ✅ Xəbəri oxuma callback
@router.callback_query(F.data.startswith("read_news:"))
async def read_news_callback(callback: CallbackQuery):
    try:
        news_id = int(callback.data.split(":")[1])
        news = get_news_by_id(news_id)
        if not news:
            await callback.message.answer("❌ İnvestisiya xəbəri tapılmadı.")
            return

        await callback.message.answer(
            f"📰 <b>{news['title']}</b>\n\n{news['content']}",
            parse_mode="HTML"
        )
    except Exception as e:
        await callback.message.answer(f"⚠️ Xəbəri oxumaq mümkün olmadı:\n{e}")
    await callback.answer()
main_menu_keyboard = get_main_buttons()


# 💰 RBCron menyusu (qısa yol)
@router.callback_query(F.data == "balance_menu")
async def balance_menu_callback(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👛 Balansı göstər", callback_data="show_balance"),
                InlineKeyboardButton(text="💳 Balansı artır", callback_data="fill_balance"),
            ],
            [InlineKeyboardButton(text="🏠 Əsas menyuya qayıt", callback_data="main_menu")],
        ]
    )
    text = (
        "💡 <b>RBCron balansı</b>\n"
        "Investorlar qrupuna qoşulub real investorların faydalı məlumat və tövsiyələrindən yararlanmaq üçün balansınız olmalıdır.\n\n"
        "👇 Balansınıza baxın və ya artırın."
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()
