import logging
from aiogram import Bot

logger = logging.getLogger(__name__)

async def send_long_message(bot: Bot, chat_id: int, text: str, parse_mode=None, **kwargs):
    """Отправка длинных сообщений с автоматическим разделением"""
    limit = 4096
    for i in range(0, len(text), limit):
        part = text[i:i+limit]
        try:
            await bot.send_message(chat_id, part, parse_mode=parse_mode, **kwargs)
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения: {e}", exc_info=True)