import requests
import logging
from database import Database

logger = logging.getLogger(__name__)

def fetch_products():
    try:
        url = "https://ng.nlstar.com/ru/api/store/city/2214/all-products/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        }
        logger.info(f"Запрос данных с {url}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        products = data.get("products", [])
        logger.info(f"Получено {len(products)} товаров")
        
        # Нормализация данных
        normalized = []
        for p in products:
            try:
                # Обработка цены
                price = p.get('price', 0)
                if isinstance(price, dict):
                    # Если цена приходит в виде словаря, берем основное значение
                    price = price.get('current', 0)
                if isinstance(price, str):
                    price = price.replace(' ', '').replace(',', '.')
                
                # Преобразуем в float
                try:
                    price = float(price)
                except (ValueError, TypeError):
                    price = 0.0
                
                normalized.append({
                    'id': str(p.get('id', '')),
                    'name': str(p.get('name') or p.get('short_name') or "Без названия"),
                    'short_name': str(p.get('short_name', '')),
                    'price': price,
                    'category': str(p.get('category', ''))})
            except Exception as e:
                logger.error(f"Ошибка обработки товара: {e}")
        
        # Сохраняем в БД
        db = Database.get_instance()
        saved = db.save_products(normalized)
        logger.info(f"Сохранено {saved} товаров в БД")
        
        return normalized
    except Exception as e:
        logger.error(f"Ошибка получения продуктов: {e}")
        return []