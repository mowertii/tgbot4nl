# bot\src\perplexity.py
import requests
import re
import threading
import time
import logging
from database import ProductDatabase

# Настройка логирования
logger = logging.getLogger(__name__)

class PerplexityAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.db = ProductDatabase()  # Инициализируем БД
        self.schedule_sync()
 
    def schedule_sync(self):
        """Запускает фоновую задачу для регулярной синхронизации"""
        def sync_task():
            while True:
                logger.info("Запуск синхронизации продуктов...")
                self.sync_products_from_api()
                time.sleep(24 * 3600)  # Синхронизация раз в сутки
                
        thread = threading.Thread(target=sync_task, daemon=True)
        thread.start()

    def sync_products_from_api(self):
        """Синхронизация продуктов с API компании"""
        try:
            logger.info("Синхронизация продуктов с API компании...")
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
                },
                {
                    "id": 2,
                    "name": "Омега-3 Премиум",
                    "description": "Высокоочищенный рыбий жир",
                    "benefits": "Поддержка сердечно-сосудистой системы, улучшение когнитивных функций",
                    "ingredients": "Концентрат Омега-3 (EPA 300 мг, DHA 200 мг), витамин E",
                    "usage": "По 1 капсуле 2 раза в день во время еды"
                }
            ]
            
            added_count = 0
            for product in demo_products:
                self.db.add_product(product)
                added_count += 1
            
            logger.info(f"Добавлено {added_count} демонстрационных продуктов")
        except Exception as e:
            logger.error(f"Ошибка синхронизации продуктов: {e}", exc_info=True)

    def ask(self, query: str, model: str = "sonar-pro") -> str:
        """Генерация ответа с использованием LLM и базы продуктов"""
        try:
            # Поиск релевантных продуктов в БД
            relevant_products = self.db.search_products(query)
            product_context = ""
            
            if relevant_products:
                logger.info(f"Найдено {len(relevant_products)} релевантных продуктов для запроса: {query}")
                product_context = "\n\n### Актуальная информация о продуктах NL:\n"
                for product in relevant_products:
                    product_context += (
                        f"- {product['name']}: {product['description']}\n"
                        f"  Польза: {product['benefits']}\n"
                        f"  Состав: {product['ingredients']}\n"
                        f"  Применение: {product['usage']}\n\n"
                    )
            else:
                logger.info(f"Для запроса '{query}' релевантные продукты не найдены")
            
            # Формируем системный промпт с контекстом продуктов
            system_prompt = (
                "Твоя роль — Нутрициолог-эксперт от компании [NL INTERNATIONAL](https://nlstar.com/ref/Eakkn3/), "
                "совмещающий науку и народную медицину.\n"
                f"{product_context}"
            )
            
            user_instructions = f"""
Инструкции для ответа:
- Основывай ответ на актуальной информации выше (если она есть)
- Отвечай строго на русском языке
- Будь честным, точным, кратким, актуальным и структурированным
- НЕ используй мысли вслух
- Оформляй ссылки в Markdown
- Предоставляй только подтвержденные данные
- Давай практические рекомендации
- При упоминании витаминов/БАДов указывай конкретные продукты
- Всегда оформляй ссылки в Markdown:
  - Для обычных ссылок: [текст](https://example.com)
  - Для сносок: в тексте [1], [2], а в конце сообщения добавь блок:
    [1]: https://source1.com
    [2]: https://source2.com
- Если ответ содержит медицинские рекомендации, то в конце добавь: 'Информация носит ознакомительный характер и не заменяет консультацию врача.'

Вопрос: "{query}"
"""

            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_instructions}
                ],
                "max_tokens": 1000,
                "temperature": 0.3,
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            logger.info(f"Отправка запроса к Perplexity API: {query[:50]}...")
            response = requests.post(
                "https://api.perplexity.ai/chat/completions",
                json=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            logger.info("Успешно получен ответ от Perplexity API")
            return data["choices"][0]["message"]["content"]
            
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP ошибка: {http_err}", exc_info=True)
            return "Ошибка при получении данных. Пожалуйста, попробуйте позже."
        except Exception as e:
            logger.error(f"Ошибка при генерации ответа: {e}", exc_info=True)
            return "Произошла внутренняя ошибка."

# Синглтон для использования в боте
perplexity_api = None

def init_perplexity(api_key):
    global perplexity_api
    perplexity_api = PerplexityAPI(api_key)

def ask_perplexity(query: str, api_key: str) -> str:
    global perplexity_api
    if not perplexity_api:
        init_perplexity(api_key)
    return perplexity_api.ask(query)