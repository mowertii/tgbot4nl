import psycopg2
from psycopg2 import sql
from psycopg2.extras import DictCursor
import os
import logging
import time
import json

logger = logging.getLogger(__name__)

class PostgresDB:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PostgresDB, cls).__new__(cls)
            cls._instance._init_db()
        return cls._instance
    
    def _init_db(self):
        self.conn = None
        self.connect()
        self.create_tables()
    
    def connect(self, retries=5, delay=3):
        for i in range(retries):
            try:
                self.conn = psycopg2.connect(
                    host=os.getenv("DB_HOST", "db"),
                    port=os.getenv("DB_PORT", "5432"),
                    dbname=os.getenv("DB_NAME", "nlstore"),
                    user=os.getenv("DB_USER", "mawr"),
                    password=os.getenv("DB_PASSWORD", "metallica")
                )
                self.conn.autocommit = True
                logger.info("Успешное подключение к PostgreSQL")
                return
            except Exception as e:
                logger.error(f"Ошибка подключения к БД (попытка {i+1}/{retries}): {e}")
                if i < retries - 1:
                    time.sleep(delay)
        
        logger.error("Не удалось подключиться к PostgreSQL после нескольких попыток")
    
    def create_tables(self):
        try:
            with self.conn.cursor() as cursor:
                # Таблица продуктов
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS products (
                        id VARCHAR(50) PRIMARY KEY,
                        name TEXT NOT NULL,
                        short_name TEXT,
                        price FLOAT NOT NULL,
                        category TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Таблица истории цен
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS price_history (
                        id SERIAL PRIMARY KEY,
                        product_id VARCHAR(50) NOT NULL,
                        price FLOAT NOT NULL,
                        recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Таблица состояния
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS bot_state (
                        key VARCHAR(50) PRIMARY KEY,
                        value JSONB NOT NULL
                    )
                """)
                
                logger.info("Таблицы в БД созданы или уже существуют")
        except Exception as e:
            logger.error(f"Ошибка создания таблиц: {e}")

    def save_products(self, products):
        if not products:
            logger.warning("Нет продуктов для сохранения")
            return
        
        logger.info(f"Сохранение {len(products)} товаров в БД...")
        saved_count = 0
        
        try:
            with self.conn.cursor() as cursor:
                for product in products:
                    try:
                        # Сохраняем продукт
                        cursor.execute("""
                            INSERT INTO products (id, name, short_name, price, category)
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT (id) DO UPDATE SET
                                name = EXCLUDED.name,
                                short_name = EXCLUDED.short_name,
                                price = EXCLUDED.price,
                                category = EXCLUDED.category,
                                updated_at = CURRENT_TIMESTAMP
                        """, (
                            product['id'],
                            product.get('name', ''),
                            product.get('short_name', ''),
                            product['price'],
                            product.get('category', '')
                        ))
                        
                        # Сохраняем в историю цен
                        cursor.execute("""
                            INSERT INTO price_history (product_id, price)
                            VALUES (%s, %s)
                        """, (
                            product['id'],
                            product['price']
                        ))
                        
                        saved_count += 1
                    except Exception as e:
                        logger.error(f"Ошибка сохранения продукта {product.get('id')}: {e}")
            
            logger.info(f"Успешно сохранено {saved_count} товаров")
            return saved_count
        except Exception as e:
            logger.error(f"Ошибка при сохранении товаров: {e}")
            return 0