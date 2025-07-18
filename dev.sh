#!/bin/bash
# dev.sh - скрипт для разработки

case "$1" in
    "start")
        echo "Запуск инфраструктуры..."
        docker-compose -f docker-compose.infrastructure.yml up -d
        echo "Ожидание запуска БД..."
        sleep 10
        echo "Запуск бота в режиме разработки..."
        docker-compose -f docker-compose.dev.yml up --build
        ;;
    "stop")
        echo "Остановка бота..."
        docker-compose -f docker-compose.dev.yml down
        ;;
    "restart")
        echo "Перезапуск бота..."
        docker-compose -f docker-compose.dev.yml down
        docker-compose -f docker-compose.dev.yml up --build
        ;;
    "infra-stop")
        echo "Остановка инфраструктуры..."
        docker-compose -f docker-compose.infrastructure.yml down
        ;;
    "logs")
        docker-compose -f docker-compose.dev.yml logs -f
        ;;
    "status")
        echo "=== Инфраструктура ==="
        docker-compose -f docker-compose.infrastructure.yml ps
        echo "=== Разработка ==="
        docker-compose -f docker-compose.dev.yml ps
        ;;
    *)
        echo "Использование: $0 {start|stop|restart|infra-stop|logs|status}"
        echo ""
        echo "start       - Запуск инфраструктуры и бота"
        echo "stop        - Остановка только бота"
        echo "restart     - Перезапуск только бота"
        echo "infra-stop  - Остановка инфраструктуры"
        echo "logs        - Просмотр логов бота"
        echo "status      - Статус всех сервисов"
        exit 1
        ;;
esac
