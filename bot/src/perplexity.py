import requests
import re

def ask_perplexity(query: str, api_key: str, model: str = "sonar-pro") -> str:
    """
    Отправляет запрос к Perplexity API и возвращает ответ с Markdown-разметкой.
    Ссылки возвращаются в формате [текст](URL) или [1], [2] с блоком сносок в конце.
    """
    url = "https://api.perplexity.ai/chat/completions"

    system_prompt = "Твоя роль — Нутрициолог-эксперт от компании NL INTERNATIONAL, совмещающий науку и народную медицину."
    user_instructions = f"""
Инструкции для ответа:
- Отвечай строго на русском языке
- Будь честным, точным, кратким, актуальным и структурированным
- НЕ используй мысли вслух
- Предоставляй только подтвержденные данные
- Давай практические рекомендации
- При упоминании витаминов/БАДов указывай конкретные продукты
- Всегда оформляй ссылки в Markdown:
  - Для обычных ссылок: [текст](https://example.com)
  - Для сносок: в тексте [1], [2], а в конце сообщения добавь блок:
    [1]: https://source1.com
    [2]: https://source2.com
- В конце добавь: 'Информация носит ознакомительный характер и не заменяет консультацию врача.'

Вопрос: "{query}"
"""

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_instructions}
        ],
        "max_tokens": 800,
        "temperature": 0.3,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Получаем чистый текст с Markdown-разметкой
        answer = data["choices"][0]["message"]["content"]
        
        # Удаляем возможные дублирования дисклеймера
        disclaimer = "Информация носит ознакомительный характер"
        if answer.count(disclaimer) > 1:
            answer = answer.replace(disclaimer, "", answer.count(disclaimer)-1)
        
        return answer
        
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP ошибка: {http_err}\nТекст ответа: {response.text}")
        return f"Ошибка API: {response.status_code}. Подробности в логах."
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return "Произошла внутренняя ошибка."