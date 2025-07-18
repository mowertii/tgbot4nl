# Makefile для управления проектом

# Запуск инфраструктуры (БД + pgAdmin)
infra-up:
	docker-compose -f docker-compose.infrastructure.yml up -d

# Остановка инфраструктуры
infra-down:
	docker-compose -f docker-compose.infrastructure.yml down -v

# Запуск для разработки (только бот)
dev-up:
	docker-compose -f docker-compose.dev.yml up --build -d

# Остановка разработки
dev-down:
	docker-compose -f docker-compose.dev.yml down

# Перезапуск только бота
dev-restart:
	docker-compose -f docker-compose.dev.yml down
	docker-compose -f docker-compose.dev.yml up --build -d

# Запуск продакшена
prod-up:
	docker-compose -f docker-compose.prod.yml up -d

# Логи разработки
dev-logs:
	docker-compose -f docker-compose.dev.yml logs -f

# Подключение к БД
db-connect:
	docker exec -it $$(docker ps -q -f "name=db") psql -U mawr -d nlstore

# Статус всех сервисов
status:
	@echo "=== Инфраструктура ==="
	docker-compose -f docker-compose.infrastructure.yml ps
	@echo "=== Разработка ==="
	docker-compose -f docker-compose.dev.yml ps

.PHONY: infra-up infra-down dev-up dev-down dev-restart prod-up dev-logs db-connect status
