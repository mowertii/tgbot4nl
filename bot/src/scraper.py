import requests
import logging

logger = logging.getLogger(__name__)

def fetch_products():
    """Получение данных о продуктах"""
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
        for product in products:
            # Гарантируем наличие id
            if 'id' not in product:
                product['id'] = hash(product.get('name') or hash(product.get('short_name')))
                
            # Гарантируем строковое представление ID
            product['id'] = str(product['id'])
            
            # Нормализация названия
            if 'name' not in product and 'short_name' in product:
                product['name'] = product['short_name']
                
            # Нормализация цены
            if 'price' in product and product['price'] is None:
                product['price'] = 0.0
        
        return products
    except Exception as e:
        logger.error(f"Ошибка получения продуктов: {e}", exc_info=True)
        return []