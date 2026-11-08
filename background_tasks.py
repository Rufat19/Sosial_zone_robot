import asyncio
import logging
from aiogram import Bot
from datetime import time
from utils.timezone_utils import get_baku_time

logger = logging.getLogger(__name__)

async def send_regular_message(bot: Bot, chat_id: int, interval: int = 3600):
    """
    Gündə bir dəfə səhər 7:00-8:00 arası "Bot canlıdır" mesajı göndərir.
    """
    logger.info("send_regular_message background task started (daily at 7-8 AM)")
    
    while True:
        try:
            now = get_baku_time()
            current_time = now.time()
            
            # Səhər 7:00 - 8:00 arasındamı?
            target_start = time(7, 0)  # 07:00
            target_end = time(8, 0)    # 08:00
            
            if target_start <= current_time <= target_end:
                # Bugün artıq göndərdikmi yoxla (hər gün yalnız bir dəfə)
                # Növbəti mesaj üçün sabahın 07:00-na qədər gözlə
                await bot.send_message(chat_id, "✅ Bot canlıdır — gündəlik yoxlama")
                logger.info("Daily heartbeat sent at %s", now)
                
                # Sabahın 07:00-a qədər gözlə (təxminən 23 saat)
                await asyncio.sleep(23 * 3600)
            else:
                # Hələ 07:00 olmayıbsa və ya 08:00-dan keçibsə
                # Növbəti yoxlama üçün 1 saat gözlə
                await asyncio.sleep(3600)
                
        except Exception as e:
            logger.exception("Failed to send regular message: %s", e)
            await asyncio.sleep(3600)  # Xəta zamanı 1 saat gözlə
