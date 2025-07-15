import json
import os
import logging

logger = logging.getLogger(__name__)

# Файлы состояний
PRICE_STATE_FILE = "price_state.json"
PINNED_STATE_FILE = 'pinned_message_state.json'

def load_state():
    try:
        if os.path.exists(PRICE_STATE_FILE):
            with open(PRICE_STATE_FILE, 'r', encoding='utf-8') as f:
                state = json.load(f)
                
                # Конвертируем все ключи в строки для совместимости
                return {str(k): v for k, v in state.items()}
                
        logger.info("Файл состояния не найден, будет создан новый")
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Ошибка загрузки состояния цен: {e}")
    return {}

def save_state(state):
    try:
        with open(PRICE_STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        logger.info(f"Сохранено состояние для {len(state)} товаров")
    except IOError as e:
        logger.error(f"Ошибка сохранения состояния цен: {e}")

def load_pinned_message_id():
    try:
        if os.path.exists(PINNED_STATE_FILE):
            with open(PINNED_STATE_FILE, 'r') as f:
                data = json.load(f)
            return data.get('pinned_message_id')
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Ошибка загрузки закрепленного сообщения: {e}")
    return None

def save_pinned_message_id(message_id):
    try:
        with open(PINNED_STATE_FILE, 'w') as f:
            json.dump({'pinned_message_id': message_id}, f)
    except IOError as e:
        logger.error(f"Ошибка сохранения закрепленного сообщения: {e}")