#!/bin/bash

# Ожидаем запуск pgAdmin
while ! curl -s http://localhost:80 > /dev/null; do
  echo "Ожидание запуска pgAdmin..."
  sleep 5
done

# Добавляем сервер
curl -v -X POST "http://localhost:80/browser/server/create" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "NL Store DB",
    "host": "db",
    "port": 5432,
    "username": "'"$POSTGRES_USER"'",
    "password": "'"$POSTGRES_PASSWORD"'",
    "db": "'"$POSTGRES_DB"'",
    "sslmode": "prefer"
  }'

echo "Сервер NL Store DB успешно добавлен в pgAdmin"