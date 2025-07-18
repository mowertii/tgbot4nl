import requests
import logging
from typing import List, Dict, Optional
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

# --- Настройка логирования ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Демонстрационная "БД" продуктов (можно заменить на реальную) ---
class ProductDatabase:
    def __init__(self):
        self.products = []
    
    def sync_demo_products(self):
        demo_products = [
            {
                "id": 1,
                "name": "Коллаген Ультра",
                "description": "Гидролизованный коллаген с витамином C",
                "benefits": "Улучшает состояние кожи, волос и ногтей, поддерживает здоровье суставов",
                "ingredients": "Коллаген гидролизованный (10 г), витамин C (80 мг)",
                "usage": "Принимать по 1 саше в день, растворив в воде"
            },
            # Можно добавить еще продукты
        ]
        self.products = demo_products
    
    def search_products(self, query: str) -> List[Dict]:
        found = []
        query_l = query.lower()
        for prod in self.products:
            text = (prod['name'] + ' ' + prod['description'] + ' ' + prod['benefits']).lower()
            if query_l in text:
                found.append(prod)
        return found


# --- Главный класc для общения с Perplexity API ---
class PerplexityAPI:
    BASE_URL = "https://api.perplexity.ai/chat/completions"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.db = ProductDatabase()
        self.db.sync_demo_products()

    # Делаем retry: 3 попытки, пауза 3 сек, только если timeout!
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(3),
        retry=retry_if_exception_type(requests.exceptions.Timeout)
    )
    def _ask(self, payload, headers):
        response = requests.post(
            self.BASE_URL,
            json=payload,
            headers=headers,
            timeout=12  # уменьшили до 12 секунд!
        )
        response.raise_for_status()
        return response.json()

    def ask(self, query: str) -> str:
        try:
            relevant = self.db.search_products(query)
            product_context = ""
            if relevant:
                product_context = "\n\n### Информация о продуктах:\n"
                for prod in relevant:
                    product_context += (
                        f"- {prod['name']}: {prod['description']}\n"
                        f"  Польза: {prod['benefits']}\n"
                    )
            system_prompt = (
                "Ты - Нутрициолог-эксперт от NL INTERNATIONAL. "
                "Отвечай строго по теме, не давай прямых медицинских диагнозов.\n"
                f"{product_context}"
            )
            # В методе ask класса PerplexityAPI
            user_prompt = (
                "Инструкции:\n"
                "- Отвечай на русском\n"
                "- Будь точным и кратким\n"
                "- Для источников используй сноски в формате: [1], [2] в тексте\n"
                "- В конце сообщения добавь список источников в формате:\n"
                "      [1]: полный_URL_источника\n"
                "      [2]: полный_URL_источника\n"
                "- При упоминании компании: [NL INTERNATIONAL](https://nlstar.com/ref/aU37in)\n"
                f'Вопрос: "{query}"'
            )
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
            # Используем защищённый вызов с повтором
            resp_json = self._ask(payload, headers)
            return resp_json["choices"][0]["message"]["content"]
        except requests.exceptions.Timeout:
            logger.error("Timeout при обращении к Perplexity API.")
            return "Сервер перегружен, не удалось получить ответ за разумное время. Попробуйте повторить позже."
        except Exception as e:
            logger.error(f"Ошибка при генерации ответа: {e}")
            return "Произошла ошибка при получении консультации. Попробуйте позже."

# --- Синглтон для общего доступа ----
perplexity_api: Optional[PerplexityAPI] = None

def init_perplexity(api_key: str):
    global perplexity_api
    perplexity_api = PerplexityAPI(api_key)
    logger.info("Perplexity API инициализирован.")

def ask_perplexity(query: str) -> str:
    if not perplexity_api:
        return "Perplexity API не инициализирован. Вызовите init_perplexity(api_key)."
    return perplexity_api.ask(query)

# --- Пример использования (для теста запусти этот файл напрямую) ---
if __name__ == "__main__":
    import os
    API_KEY = os.getenv("PERPLEXITY_API_KEY", "your_api_key_here")
    init_perplexity(API_KEY)
    while True:
        q = input("Ваш вопрос по нутрициологии: ")
        print(ask_perplexity(q))
