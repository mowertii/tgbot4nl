import re
import html

def clean_telegram_html(text: str) -> str:
    """Очистка Telegram-специфичных тегов"""
    return re.sub(r"</?think>", "", text)

def clean_llm_answer(answer: str, user_query: str) -> str:
    """Очистка ответа от LLM от лишних фраз"""
    phrases = [
        "Мы получили запрос", "Вы спросили", "Ваш вопрос",
        "Вопрос:", "Запрос:", "Пользователь спросил",
    ]
    for phrase in phrases:
        answer = answer.replace(phrase, "")
    return answer.strip()

def convert_markdown_links_to_html(text: str) -> str:
    """Преобразование Markdown-ссылок в HTML"""
    def replace_link(match):
        link_text = html.escape(match.group(1))
        url = html.escape(match.group(2), quote=True)
        return f'<a href="{url}">{link_text}</a>'
    
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replace_link, text)
    return text