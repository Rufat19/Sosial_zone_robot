import asyncio
import logging

from aiogram.types import Message, MessageId

logger = logging.getLogger(__name__)
DELETE_DELAY_SECONDS = 5 * 60
_pending_deletions = set()


def schedule_message_deletion(bot, chat_id: int, message_id: int):
    task = asyncio.create_task(_delete_after_delay(bot, chat_id, message_id))
    _pending_deletions.add(task)
    task.add_done_callback(_pending_deletions.discard)


async def _delete_after_delay(bot, chat_id: int, message_id: int):
    await asyncio.sleep(DELETE_DELAY_SECONDS)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as error:
        logger.debug(
            "Mesajı avtomatik silmək mümkün olmadı (çat=%s, mesaj=%s): %s",
            chat_id,
            message_id,
            error,
        )


async def delete_incoming_messages(handler, event, data):
    if isinstance(event, Message):
        bot = data.get("bot")
        if bot is not None:
            schedule_message_deletion(bot, event.chat.id, event.message_id)
    return await handler(event, data)


async def delete_outgoing_messages(make_request, bot, method):
    result = await make_request(bot, method)

    if isinstance(result, Message):
        schedule_message_deletion(bot, result.chat.id, result.message_id)
    elif isinstance(result, list):
        for item in result:
            if isinstance(item, Message):
                schedule_message_deletion(bot, item.chat.id, item.message_id)
    elif isinstance(result, MessageId):
        chat_id = getattr(method, "chat_id", None)
        if chat_id is not None:
            schedule_message_deletion(bot, chat_id, result.message_id)

    return result
