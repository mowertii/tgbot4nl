import re
import html

def clean_telegram_html(text: str) -> str:
    return re.sub(r"</?think>", "", text)

def convert_markdown_links_to_html(text: str) -> str:
    # Обработка сносок вида [1], [2] с ссылками в конце
    footnote_refs = {}
    
    # Шаг 1: Собираем все сноски вида [1]: URL
    def collect_footnotes(match):
        num = match.group(1)
        url = match.group(2)
        footnote_refs[num] = url
        return ""  # Удаляем строку сноски из текста
    
    text = re.sub(r'^\[(\d+)\]:\s*(\S+)$', collect_footnotes, text, flags=re.MULTILINE)
    
    # Шаг 2: Заменяем упоминания [1] на ссылки
    if footnote_refs:
        def replace_footnote(match):
            num = match.group(1)
            url = footnote_refs.get(num)
            if url:
                return f'<a href="{html.escape(url, quote=True)}">[{num}]</a>'
            return match.group(0)
        
        text = re.sub(r'\[(\d+)\]', replace_footnote, text)
    
    # Шаг 3: Обработка обычных Markdown ссылок
    def replace_link(match):
        return f'<a href="{html.escape(match.group(2), quote=True)}">{html.escape(match.group(1))}</a>'
    
    return re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replace_link, text)