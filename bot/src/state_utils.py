import logging
from database import Database 

logger = logging.getLogger(__name__)

def load_state():
    try:
        db = Database.get_instance()
        return db.load_state('price_state')
    except Exception as e:
        logger.error(f"Ошибка загрузки состояния: {e}")
        return {}

def save_state(state):
    try:
        db = Database.get_instance()
        db.save_state('price_state', state)
    except Exception as e:
        logger.error(f"Ошибка сохранения состояния: {e}")

def load_pinned_message_id():
    try:
        db = Database.get_instance()
        state = db.load_state('pinned_message')
        return state.get('pinned_message_id')
    except Exception as e:
        logger.error(f"Ошибка загрузки закрепленного сообщения: {e}")
        return None

def save_pinned_message_id(message_id):
    try:
        db = Database.get_instance()
        db.save_state('pinned_message', {'pinned_message_id': message_id})
    except Exception as e:
        logger.error(f"Ошибка сохранения закрепленного сообщения: {e}")