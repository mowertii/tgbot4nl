##Settings for connect
Host name/address: db
Port: 5432
Maintenance database: nlstore
Username: {your_username}
Password: {your_pass}


#work with db throw query service:
#check catalog
SELECT datname FROM pg_catalog.pg_database WHERE datistemplate = false;

#check tables
SELECT tablename FROM pg_tables WHERE schemaname = 'public';

----
# Makefile для управления проектом (создать файл Makefile в корне проекта, без расширения со следующим содержимым)

# Запуск инфраструктуры (БД + pgAdmin)
infra-up:
	docker-compose -f docker-compose.infrastructure.yml up -d

# Остановка инфраструктуры
infra-down:
	docker-compose -f docker-compose.infrastructure.yml down

# Запуск для разработки (только бот)
dev-up:
	docker-compose -f docker-compose.dev.yml up --build

# Остановка разработки
dev-down:
	docker-compose -f docker-compose.dev.yml down

# Перезапуск только бота
dev-restart:
	docker-compose -f docker-compose.dev.yml down
	docker-compose -f docker-compose.dev.yml up --build

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

----
Управление
Команда	Описание
make infra-up	Запуск БД и pgAdmin
make dev-up	Запуск бота для разработки
make dev-restart	Быстрый перезапуск бота
make dev-logs	Просмотр логов
make infra-down	Остановка инфраструктуры
make status	Статус всех сервисов