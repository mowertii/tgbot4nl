import os
import asyncio
import logging
import logging.config
from aiogram import Bot, Dispatcher, Router, types
from dotenv import load_dotenv
from aiogram.exceptions import TelegramBadRequest

from state_utils import load_state, save_state, load_pinned_message_id, save_pinned_message_id
from scraper import fetch_products
from perplexity import ask_perplexity, init_perplexity
from telegram_utils import send_long_message
from text_utils import clean_telegram_html, clean_llm_answer, convert_markdown_links_to_html

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "18000"))

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} - {name} - {levelname} - {module}:{lineno} - {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} - {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'level': 'DEBUG',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': os.getenv('LOG_LEVEL', 'INFO'),
            'propagate': True,
        },
    },
})

logger = logging.getLogger(__name__)

# Инициализация Perplexity API
if PERPLEXITY_API_KEY:
    init_perplexity(PERPLEXITY_API_KEY)

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
        
        # Исправленный асинхронный вызов
        loop = asyncio.get_event_loop()
        raw_answer = await loop.run_in_executor(
            None, 
            ask_perplexity, 
            user_query
        )
        cleaned_answer = clean_telegram_html(raw_answer)
        answer_with_links = convert_markdown_links_to_html(cleaned_answer)

        reply_text = f"{mention}, {answer_with_links}" if mention else answer_with_links

        await send_long_message(
            bot=message.bot,
            chat_id=message.chat.id,
            text=reply_text,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        logger.info("Ответ успешно отправлен")
        
    except Exception as e:
        logger.error(f"Ошибка обработки запроса: {e}", exc_info=True)
        await message.reply("Произошла ошибка при обработке вашего запроса.")

async def price_scraping_loop(bot: Bot):
    await asyncio.sleep(10)
    logger.info("Запущен цикл отслеживания цен")
    
    while True:
        try:
            products = fetch_products()
            old_state = load_state()
            logger.info(f"Загружено состояние для {len(old_state)} товаров")
            
            pinned_message_id = load_pinned_message_id()
            new_state = {}
            price_drop_messages = []
            price_increase_detected = False
            new_products_count = 0

            for product in products:
                try:
                    product_id = str(product['id'])
                    product_name = product.get('name') or product.get('short_name') or "Без названия"
                    
                    if 'price' not in product or product['price'] is None:
                        logger.warning(f"У товара ID {product_id} отсутствует цена")
                        continue
                        
                    new_price = float(product['price'])
                    
                    # Если товара не было в предыдущем состоянии, добавляем как новый
                    if product_id not in old_state:
                        logger.info(f"Найден новый товар: {product_name} (ID: {product_id})")
                        new_state[product_id] = {
                            'name': product_name, 
                            'price': new_price, 
                            'last_notified_price': new_price
                        }
                        new_products_count += 1
                        continue
                    
                    # Получаем данные из старого состояния
                    current_product_state = old_state.get(product_id, {})
                    old_price = current_product_state.get('price', new_price)
                    last_notified_price = current_product_state.get('last_notified_price', old_price)
                    
                    # Преобразуем значения в числа
                    try:
                        old_price = float(old_price)
                        last_notified_price = float(last_notified_price)
                    except (TypeError, ValueError):
                        logger.warning(f"Некорректные данные в состоянии для товара {product_id}")
                        old_price = new_price
                        last_notified_price = new_price

                    new_state[product_id] = {
                        'name': product_name, 
                        'price': new_price, 
                        'last_notified_price': last_notified_price
                    }

                    # Проверяем изменения цены
                    if new_price < old_price and new_price != last_notified_price:
                        msg = f"📉 Цена на '{product_name}' снизилась: {old_price} ₽ → {new_price} ₽"
                        price_drop_messages.append(msg)
                        new_state[product_id]['last_notified_price'] = new_price
                    elif new_price > old_price:
                        price_increase_detected = True
                        new_state[product_id]['last_notified_price'] = new_price

                except (KeyError, ValueError, TypeError) as e:
                    logger.warning(f"Пропускаем товар ID {product_id}: некорректные данные. Ошибка: {e}")

            logger.info(f"Обработано товаров: {len(products)}, новых: {new_products_count}")

            if price_drop_messages:
                full_message = "🔥 **АКЦИЯ!**\n\n" + "\n".join(price_drop_messages)
                try:
                    sent_message = await bot.send_message(CHANNEL_ID, full_message, parse_mode="Markdown")
                    await bot.pin_chat_message(
                        chat_id=CHANNEL_ID, 
                        message_id=sent_message.message_id,
                        disable_notification=True
                    )
                    save_pinned_message_id(sent_message.message_id)
                    logger.info(f"Отправлено и закреплено сообщение об акции (ID: {sent_message.message_id}).")
                except TelegramBadRequest as e:
                    logger.error(f"Не удалось отправить/закрепить: {e}. Проверьте права бота.")
                except Exception as e:
                    logger.error(f"Ошибка при отправке/закреплении: {e}")

            elif price_increase_detected and pinned_message_id:
                try:
                    await bot.unpin_chat_message(chat_id=CHANNEL_ID, message_id=pinned_message_id)
                    logger.info(f"Сообщение {pinned_message_id} откреплено.")
                    save_pinned_message_id(None)
                except TelegramBadRequest:
                    logger.info("Сообщение уже откреплено")
                    save_pinned_message_id(None)
                except Exception as e:
                    logger.error(f"Ошибка при откреплении: {e}")
            else:
                logger.info("Изменений цен не обнаружено.")

            save_state(new_state)

        except Exception as e:
            logger.error(f"Ошибка в цикле отслеживания цен: {e}", exc_info=True)

        await asyncio.sleep(CHECK_INTERVAL)

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    asyncio.create_task(price_scraping_loop(bot))
    logger.info("Бот запущен и слушает канал...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())