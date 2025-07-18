import os
import asyncio
import logging
from perplexity import init_perplexity, ask_perplexity
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command
from dotenv import load_dotenv
from aiogram.exceptions import TelegramBadRequest

# Исправленные импорты (убраны точки)
from state_utils import load_state, save_state, load_pinned_message_id, save_pinned_message_id
from scraper import fetch_products
from perplexity import ask_perplexity, init_perplexity
from telegram_utils import send_long_message
from text_utils import clean_telegram_html, convert_markdown_links_to_html

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "18000"))



# Инициализация Perplexity API
if PERPLEXITY_API_KEY:
    init_perplexity(PERPLEXITY_API_KEY)
    answer = ask_perplexity("Какая польза у коллагена?")
    
# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
router = Router()


@router.channel_post()
async def channel_post_handler(message: types.Message):
    if not PERPLEXITY_API_KEY:
        await message.reply("Perplexity API ключ не задан.")
        return

    user_query = message.text
    if not user_query:
        return

    try:
        mention = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.full_name}</a>' if message.from_user else None

        await message.reply("Запрос отправлен, ожидайте ответа...")
        logger.info(f"Обработка запроса: {user_query[:50]}...")
        
        loop = asyncio.get_event_loop()
        raw_answer = await loop.run_in_executor(None, ask_perplexity, user_query)
        
        cleaned_answer = clean_telegram_html(raw_answer)
        answer_with_links = convert_markdown_links_to_html(cleaned_answer)

        reply_text = f"{mention}, {answer_with_links}" if mention else answer_with_links
 
        await send_long_message(
            bot=message.bot,
            chat_id=message.chat.id,
            text=reply_text,
            parse_mode="HTML",  # Важно использовать HTML-парсинг
            disable_web_page_preview=True
        )
        logger.info("Ответ успешно отправлен")
        
    except Exception as e:
        logger.error(f"Ошибка обработки запроса: {e}")
        await message.reply("Произошла ошибка при обработке вашего запроса.")

async def price_scraping_loop(bot: Bot):
    await asyncio.sleep(10)
    logger.info("Запущен цикл отслеживания цен")
    
    while True:
        try:
            products = fetch_products()
            old_state = load_state()
            pinned_message_id = load_pinned_message_id()
            new_state = {}
            price_drop_messages = []
            price_increase_detected = False

            for product in products:
                try:
                    product_id = str(product.get('id', ''))
                    product_name = str(product.get('name', 'Без названия'))
                    
                    # Обработка цены
                    new_price = product.get('price', 0)
                    if isinstance(new_price, dict):
                        new_price = new_price.get('current', 0)
                    new_price = float(new_price)
                    
                    # Если товара нет в старом состоянии
                    if product_id not in old_state:
                        new_state[product_id] = {
                            'price': new_price,
                            'last_notified_price': new_price
                        }
                        continue
                    
                    # Получаем данные из старого состояния
                    state_data = old_state.get(product_id, {})
                    old_price = float(state_data.get('price', new_price))
                    last_notified = float(state_data.get('last_notified_price', old_price))
                    
                    # Сохраняем новое состояние
                    new_state[product_id] = {
                        'price': new_price,
                        'last_notified_price': last_notified
                    }

                    # Проверяем изменения цены
                    if new_price < old_price and new_price != last_notified:
                        msg = f"📉 Цена на '{product_name}' снизилась: {old_price} ₽ → {new_price} ₽"
                        price_drop_messages.append(msg)
                        new_state[product_id]['last_notified_price'] = new_price
                    elif new_price > old_price:
                        price_increase_detected = True
                        new_state[product_id]['last_notified_price'] = new_price

                except (KeyError, ValueError, TypeError) as e:
                    logger.warning(f"Пропускаем товар: {e}")

            if price_drop_messages:
                full_message = "🔥 **АКЦИЯ!**\n\n" + "\n".join(price_drop_messages)
                sent_message = await bot.send_message(CHANNEL_ID, full_message, parse_mode="Markdown")
                await bot.pin_chat_message(CHANNEL_ID, sent_message.message_id)
                save_pinned_message_id(sent_message.message_id)
            elif price_increase_detected and pinned_message_id:
                await bot.unpin_chat_message(CHANNEL_ID, pinned_message_id)
                save_pinned_message_id(None)

            save_state(new_state)
            logger.info(f"Обработано {len(products)} товаров, изменений: {len(price_drop_messages)}")

        except Exception as e:
            logger.error(f"Ошибка в цикле отслеживания цен: {e}")

        await asyncio.sleep(CHECK_INTERVAL)
        
@router.message(Command("stats"))
async def send_stats(message: types.Message):
    try:
        stats = "📊 Статистика базы данных:\n"
        stats += f"• Доступ в pgAdmin: http://localhost:6432\n"
        stats += f"  Логин: admin@admin.com\n"
        stats += f"  Пароль: metallica"
        await message.reply(stats)
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        await message.reply("Ошибка получения статистики")

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    asyncio.create_task(price_scraping_loop(bot))
    logger.info("Бот запущен и слушает канал...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())