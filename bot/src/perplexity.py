import requests
import re

def format_links_in_text(text: str) -> str:
    """
    Находит все URL-адреса в тексте и преобразует их в HTML-гиперссылки.
    Например, 'https://google.com' станет '<a href="https://google.com">https://google.com</a>'.
    """
    # Регулярное выражение для поиска URL-адресов
    url_pattern = re.compile(r'https?://\S+')

    # Функция для замены найденного URL на HTML-тег. Эта часть кода работает правильно.
    def replacer(match):
        url = match.group(0)
        # Создается корректный HTML-тег для ссылки
        return f'<a href="{url}">{url}</a>'

    return url_pattern.sub(replacer, text)

def ask_perplexity(query: str, api_key: str, model: str = "sonar-pro") -> str:
    """
    Отправляет запрос к Perplexity API с настроенной ролью нутрициолога.
    """
    url = "https://api.perplexity.ai/chat/completions"

    system_prompt = "Твоя роль — Нутрициолог-эксперт от компании NL INTERNATIONAL, совмещающий науку и народную медицину."
    user_instructions = f"""
Инструкции для ответа:
- Будь честным, точным, кратким, актуальными и структурированным.
- НЕ используй мысли вслух.
- Предоставляй только те рекомендации, которые подтверждены актуальными данными из поисковых систем.
- Предоставь только конечный, практический совет.
- Если есть рекомендация применения витаминов или бадов, то упомяни о соответствующих продуктах из имеющихся в продаже.
- В конце добавь дисклеймер: 'Информация носит ознакомительный характер и не заменяет консультацию врача.'
Вопрос пользователя: "{query}"
- Оформляй ссылки на справочные материалы и источники в формате markdown, например так [Тест](https://test.com).
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
        return data["choices"][0]["message"]["content"]
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP ошибка: {http_err}\nТекст ответа: {response.text}")
        return f"Ошибка API: {response.status_code}. Подробности в логах."
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return "Произошла внутренняя ошибка."
