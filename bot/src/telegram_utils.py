import logging
from aiogram import Bot

logger = logging.getLogger(__name__)

async def send_long_message(bot: Bot, chat_id: int, text: str, parse_mode=None, **kwargs):
    limit = 4096
    for i in range(0, len(text), limit):
        part = text[i:i+limit]
        await bot.send_message(chat_id, part, parse_mode=parse_mode, **kwargs)