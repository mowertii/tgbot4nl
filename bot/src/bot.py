import os
import asyncio
import logging
import re
import json
import html
from price_state import load_state, save_state
from novelty_price_scraper import fetch_products
from aiogram import Bot, Dispatcher, Router, types
from dotenv import load_dotenv
from aiogram.exceptions import TelegramBadRequest
from perplexity import ask_perplexity

load_dotenv()

PINNED_STATE_FILE = 'pinned_message_state.json'
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
X_AUTH_TOKEN = os.getenv("X_AUTH_TOKEN")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "18000"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
router = Router()

def load_pinned_message_id():
    try:
        if os.path.exists(PINNED_STATE_FILE):
            with open(PINNED_STATE_FILE, 'r') as f:
                data = json.load(f)
            return data.get('pinned_message_id')
    except (json.JSONDecodeError, IOError):
        return None
    return None

def save_pinned_message_id(message_id):
    with open(PINNED_STATE_FILE, 'w') as f:
        json.dump({'pinned_message_id': message_id}, f)

def clean_telegram_html(text: str) -> str:
    text = re.sub(r"</?think>", "", text)
    return text

def clean_llm_answer(answer, user_query):
    answer = answer.replace(user_query, "")
    for phrase in [
        "Мы получили запрос", "Вы спросили", "Ваш вопрос",
        "Вопрос:", "Запрос:", "Пользователь спросил",
    ]:
        answer = answer.replace(phrase, "")
    return answer.strip()

def convert_markdown_links_to_html(text: str) -> str:
    """
    Преобразует Markdown-ссылки [текст](URL) в HTML-теги <a href="URL">текст</a>
    с экранированием HTML-символов.
    """
    def replace_link(match):
        link_text = html.escape(match.group(1))
        url = html.escape(match.group(2), quote=True)
        return f'<a href="{url}">{link_text}</a>'
    
    # Обрабатываем как стандартные Markdown-ссылки, так и сноски [1], [2]
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replace_link, text)
    
    # Дополнительно обрабатываем сноски вида [1]: http://example.com
    footnote_pattern = re.compile(r'^\s*\[(\d+)\]:\s*(\S+)\s*$', re.MULTILINE)
    footnotes = {num: url for num, url in footnote_pattern.findall(text)}
    
    for num, url in footnotes.items():
        safe_url = html.escape(url, quote=True)
        text = text.replace(f'[{num}]', f'<a href="{safe_url}">[{num}]</a>')
    
    # Удаляем блок сносок из текста
    text = re.sub(r'\n\n\[(\d+)\]:\s*\S+\s*(\n\[(\d+)\]:\s*\S+\s*)*', '', text)
    
    return text

async def send_long_message(bot, chat_id, text, parse_mode=None, **kwargs):
    limit = 4096
    for i in range(0, len(text), limit):
        await bot.send_message(chat_id, text[i:i+limit], parse_mode=parse_mode, **kwargs)

@router.channel_post()
async def channel_post_handler(message: types.Message):
    if not PERPLEXITY_API_KEY:
        await message.reply("Perplexity API ключ не задан.")
        return

    user_query = message.text
    if not user_query:
        return

    if message.from_user:
        mention = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.full_name}</a>'
    else:
        mention = None

    await message.reply("Запрос отправлен, ожидайте ответа...")
    loop = asyncio.get_event_loop()

    raw_answer = await loop.run_in_executor(None, ask_perplexity, user_query, PERPLEXITY_API_KEY)
    cleaned_answer = clean_telegram_html(raw_answer)
    answer_with_links = convert_markdown_links_to_html(cleaned_answer)

    if mention:
        reply_text = f"{mention}, {answer_with_links}"
    else:
        reply_text = answer_with_links

    await send_long_message(
        bot=message.bot,
        chat_id=message.chat.id,
        text=reply_text,
        parse_mode="HTML",
        disable_web_page_preview=True
    )

async def price_scraping_loop(bot: Bot):
    await asyncio.sleep(10)
    while True:
        try:
            products = fetch_products()
            old_state = load_state()
            pinned_message_id = load_pinned_message_id()
            new_state = {}
            price_drop_messages = []
            price_increase_detected = False

            for product in products:
                required_keys = ['id', 'name', 'price']
                if not all(key in product for key in required_keys):
                    logger.warning(f"Пропускаем товар: отсутствуют ключи. Данные: {product}")
                    continue

                try:
                    product_id = str(product['id'])
                    new_price = float(product['price'])
                    product_name = product['name']
                except (ValueError, TypeError):
                    logger.warning(f"Пропускаем товар: некорректные данные. Данные: {product}")
                    continue

                if product_id not in old_state:
                    new_state[product_id] = {'name': product_name, 'price': new_price, 'last_notified_price': new_price}
                    continue

                current_product_state = old_state[product_id]
                old_price = float(current_product_state.get('price'))
                last_notified_price = float(current_product_state.get('last_notified_price', old_price))

                new_state[product_id] = {'name': product_name, 'price': new_price, 'last_notified_price': last_notified_price}

                if new_price < old_price and new_price != last_notified_price:
                    msg = f"📉 Цена на '{product_name}' снизилась: {old_price} ₽ → {new_price} ₽"
                    price_drop_messages.append(msg)
                    new_state[product_id]['last_notified_price'] = new_price
                elif new_price > old_price:
                    price_increase_detected = True
                    new_state[product_id]['last_notified_price'] = new_price

            if price_drop_messages:
                full_message = "🔥 **АКЦИЯ!**\n\n" + "\n".join(price_drop_messages)
                try:
                    sent_message = await bot.send_message(CHANNEL_ID, full_message, parse_mode="Markdown")
                    await bot.pin_chat_message(chat_id=CHANNEL_ID, message_id=sent_message.message_id, disable_notification=True)
                    save_pinned_message_id(sent_message.message_id)
                    logger.info(f"Отправлено и закреплено сообщение об акции (ID: {sent_message.message_id}).")
                except TelegramBadRequest as e:
                    logger.error(f"Не удалось отправить или закрепить сообщение: {e}. Проверьте права администратора у бота.")
                except Exception as e:
                    logger.error(f"Непредвиденная ошибка при отправке/закреплении: {e}")

            elif price_increase_detected and pinned_message_id:
                try:
                    await bot.unpin_chat_message(chat_id=CHANNEL_ID, message_id=pinned_message_id)
                    logger.info(f"Сообщение {pinned_message_id} откреплено из-за повышения цен.")
                    save_pinned_message_id(None)
                except TelegramBadRequest as e:
                    logger.warning(f"Не удалось открепить сообщение {pinned_message_id}: {e}. Возможно, оно уже было откреплено.")
                    save_pinned_message_id(None)
                except Exception as e:
                    logger.error(f"Непредвиденная ошибка при откреплении сообщения: {e}")
            else:
                logger.info("Новых снижений цен для закрепления не обнаружено.")

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