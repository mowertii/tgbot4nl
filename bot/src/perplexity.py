import requests
import logging
from database import ProductDatabase

logger = logging.getLogger(__name__)

class PerplexityAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.db = ProductDatabase()
        self.sync_products()

    def sync_products(self):
        """Синхронизация продуктов (заглушка)"""
        try:
            logger.info("Синхронизация продуктов...")
            # В реальной реализации здесь будет запрос к API
            # Сейчас используем демо-данные
            demo_products = [
                {
                    "id": 1,
                    "name": "Коллаген Ультра",
                    "description": "Гидролизованный коллаген с витамином C",
                    "benefits": "Улучшает состояние кожи, волос и ногтей, поддерживает здоровье суставов",
                    "ingredients": "Коллаген гидролизованный (10 г), витамин C (80 мг)",
                    "usage": "Принимать по 1 саше в день, растворив в воде"
                }
            ]
            
            for product in demo_products:
                self.db.add_product(product)
                
        except Exception as e:
            logger.error(f"Ошибка синхронизации: {e}")

    def ask(self, query: str) -> str:
        """Генерация ответа с использованием LLM"""
        try:
            # Поиск релевантных продуктов
            relevant_products = self.db.search_products(query)
            product_context = ""
            
            if relevant_products:
                logger.info(f"Найдено продуктов: {len(relevant_products)}")
                product_context = "\n\n### Информация о продуктах:\n"
                for product in relevant_products:
                    product_context += (
                        f"- {product['name']}: {product['description']}\n"
                        f"  Польза: {product['benefits']}\n"
                    )

            # Формирование промпта
            system_prompt = (
                "Ты - Нутрициолог-эксперт от NL INTERNATIONAL.\n"
                f"{product_context}"
            )
            
            user_prompt = f"""
Инструкции:
- Отвечай на русском
- Будь точным и кратким
- Используй Markdown для ссылок
- При упоминании компании: [NL INTERNATIONAL](https://nlstar.com)
- Для медицинских советов добавляй предупреждение

Вопрос: "{query}"
"""

            payload = {
                "model": "sonar-pro",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 1000,
                "temperature": 0.3,
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            response = requests.post(
                "https://api.perplexity.ai/chat/completions",
                json=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
            
        except Exception as e:
            logger.error(f"Ошибка генерации ответа: {e}")
            return "Произошла ошибка при обработке запроса."

# Синглтон
perplexity_api = None

def ask_perplexity(query: str) -> str:
    try:
        if not perplexity_api:
            return "Ошибка: Perplexity API не инициализирован"
        
        return perplexity_api.ask(query)
    except Exception as e:
        logger.error(f"Критическая ошибка в ask_perplexity: {e}", exc_info=True)
        return "Произошла внутренняя ошибка при обработке запроса."
    
def init_perplexity(api_key):
    global perplexity_api
    perplexity_api = PerplexityAPI(api_key)
