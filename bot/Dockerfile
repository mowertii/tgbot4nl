FROM python:3.11-slim

WORKDIR /app

# Установка инструментов для отладки
RUN apt-get update && apt-get install -y \
    procps \
    net-tools \
    vim-tiny \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src

CMD ["python", "-u", "src/bot.py"]