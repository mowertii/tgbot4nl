import os
import asyncio
import logging
import re
from price_state import load_state, save_state, compare_prices
from novelty_price_scraper import fetch_products
from aiogram import Bot, Dispatcher, Router, types
from dotenv import load_dotenv
from price_tracker import get_price_changes
from perplexity import ask_perplexity

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
X_AUTH_TOKEN = os.getenv("X_AUTH_TOKEN")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "600"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
router = Router()

def clean_telegram_html(text: str) -> str:
    # Удаляем все теги <think>...</think>
    text = re.sub(r"</?think>", "", text)
    # Можно добавить другие кастомные теги, если появятся
    return text

def clean_llm_answer(answer, user_query):
    answer = answer.replace(user_query, "")
    for phrase in [
        "Мы получили запрос",
        "Вы спросили",
        "Ваш вопрос",
        "Вопрос:",
        "Запрос:",
        "Пользователь спросил",
    ]:
        answer = answer.replace(phrase, "")
    return answer.strip()

async def send_long_message(bot, chat_id, text, parse_mode=None):
    limit = 4096
    for i in range(0, len(text), limit):
        await bot.send_message(chat_id, text[i:i+limit], parse_mode=parse_mode)

@router.channel_post()
async def channel_post_handler(message: types.Message):
    """
    Обрабатывает новые сообщения в канале.
    Отправляет ответ с тегом автора, если это возможно.
    """
    if not PERPLEXITY_API_KEY:
        await message.reply("Perplexity API ключ не задан.")
        return
    user_query = message.text
    if not user_query:
        await message.reply("Пустое сообщение, пожалуйста, отправьте текст.")
        return

    # Формируем тег пользователя, если это возможно
    if message.from_user:
        mention = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.full_name}</a>'
    else:
        mention = None

    await message.reply("Запрос отправлен, ожидайте ответа...")

    loop = asyncio.get_event_loop()
    answer = await loop.run_in_executor(None, ask_perplexity, user_query, PERPLEXITY_API_KEY)
    answer = clean_telegram_html(answer)
    if mention:
        reply_text = f"{mention}, {answer}"
    else:
        reply_text = answer

    # Отправляем ответ в канал с тегом пользователя (если возможно)
    await send_long_message(bot=message.bot, chat_id=message.chat.id, text=reply_text, parse_mode="HTML")


async def price_scraping_loop(bot: Bot):
    await asyncio.sleep(10)
    while True:
        try:
            products = fetch_products()
            old_state = load_state()
            changes, new_state = compare_prices(products, old_state)
            save_state(new_state)
            if changes:
                msg = "Внимание, изменились цены на товары:\n"
                for ch in changes:
                    msg += f"{ch['name']}: {ch['old_price']} → {ch['new_price']}\n"
                await bot.send_message(CHANNEL_ID, msg) # (CHANNEL_ID, f"{len(products)} (новый снимок цен)")
                logger.info(msg) #(f"Собрано товаров: {len(products)}")
            else:
                logger.info("Изменений цен не обнаружено.")
        except Exception as e:
            logger.error(f"Ошибка парсинга цен: {e}")
        await asyncio.sleep(CHECK_INTERVAL)


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    # Запускаем задачу отслеживания цен
    asyncio.create_task(price_scraping_loop(bot))
    logger.info("Бот запущен и слушает канал...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

