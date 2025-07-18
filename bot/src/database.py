import psycopg2
import os
import logging
import time
import json

logger = logging.getLogger(__name__)

class Database:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        self.conn = None
        self.connect()
        self.create_tables()
    
    def connect(self, retries=10, delay=2):
        """Подключение к базе данных с улучшенной логикой повторных попыток"""
        for i in range(retries):
            try:
                self.conn = psycopg2.connect(
                    host=os.getenv("DB_HOST", "localhost"),
                    port=os.getenv("DB_PORT", "5432"),
                    dbname=os.getenv("DB_NAME", "nlstore"),
                    user=os.getenv("DB_USER", "mawr"),
                    password=os.getenv("DB_PASSWORD", "metallica"),
                    connect_timeout=10
                )
                self.conn.autocommit = True
                logger.info(f"Успешное подключение к PostgreSQL на {os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}")
                return
            except psycopg2.OperationalError as e:
                logger.warning(f"Ошибка подключения к БД (попытка {i+1}/{retries}): {e}")
                if i < retries - 1:
                    time.sleep(delay)
                else:
                    logger.error("Не удалось подключиться к PostgreSQL после всех попыток")
                    raise
            except Exception as e:
                logger.error(f"Неожиданная ошибка подключения к БД: {e}")
                raise
    
    def reconnect(self):
        """Переподключение к базе данных"""
        if self.conn:
            try:
                self.conn.close()
            except:
                pass
        self.connect()
    
    def execute_with_retry(self, query, params=None, retries=3):
        """Выполнение запроса с повторными попытками при потере соединения"""
        for i in range(retries):
            try:
                with self.conn.cursor() as cursor:
                    cursor.execute(query, params)
                    return cursor.fetchall() if cursor.description else None
            except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
                logger.warning(f"Потеря соединения с БД, попытка переподключения ({i+1}/{retries}): {e}")
                if i < retries - 1:
                    try:
                        self.reconnect()
                    except Exception as reconnect_error:
                        logger.error(f"Ошибка переподключения: {reconnect_error}")
                        time.sleep(2)
                else:
                    logger.error("Не удалось восстановить соединение с БД")
                    raise
    
    def create_tables(self):
        if not self.conn:
            logger.error("Нет подключения к БД для создания таблиц")
            return
            
        try:
            self.execute_with_retry("""
                CREATE TABLE IF NOT EXISTS products (
                    id VARCHAR(50) PRIMARY KEY,
                    name TEXT NOT NULL,
                    short_name TEXT,
                    price FLOAT NOT NULL,
                    category TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.execute_with_retry("""
                CREATE TABLE IF NOT EXISTS price_history (
                    id SERIAL PRIMARY KEY,
                    product_id VARCHAR(50) NOT NULL,
                    price FLOAT NOT NULL,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.execute_with_retry("""
                CREATE TABLE IF NOT EXISTS bot_state (
                    key VARCHAR(50) PRIMARY KEY,
                    value JSONB NOT NULL
                )
            """)
            
            logger.info("Таблицы в БД созданы или уже существуют")
        except Exception as e:
            logger.error(f"Ошибка создания таблиц: {e}")
    
    def save_products(self, products):
        if not self.conn or not products:
            return 0
            
        saved_count = 0
        try:
            for product in products:
                try:
                    # Проверяем и преобразуем данные
                    product_id = str(product.get('id', ''))
                    name = str(product.get('name', ''))
                    short_name = str(product.get('short_name', ''))
                    price = float(product.get('price', 0))
                    category = str(product.get('category', ''))
                    
                    self.execute_with_retry("""
                        INSERT INTO products (id, name, short_name, price, category)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            name = EXCLUDED.name,
                            short_name = EXCLUDED.short_name,
                            price = EXCLUDED.price,
                            category = EXCLUDED.category,
                            updated_at = CURRENT_TIMESTAMP
                    """, (product_id, name, short_name, price, category))
                    
                    self.execute_with_retry("""
                        INSERT INTO price_history (product_id, price)
                        VALUES (%s, %s)
                    """, (product_id, price))
                    
                    saved_count += 1
                except Exception as e:
                    logger.error(f"Ошибка сохранения продукта {product.get('id')}: {e}")
        except Exception as e:
            logger.error(f"Общая ошибка при сохранении товаров: {e}")
        
        return saved_count
    
    def save_state(self, key, state):
        if not self.conn:
            return
            
        try:
            self.execute_with_retry("""
                INSERT INTO bot_state (key, value)
                VALUES (%s, %s)
                ON CONFLICT (key) DO UPDATE SET
                    value = EXCLUDED.value
            """, (key, json.dumps(state)))
        except Exception as e:
            logger.error(f"Ошибка сохранения состояния: {e}")
    
    def load_state(self, key):
        if not self.conn:
            return {}
            
        try:
            result = self.execute_with_retry("SELECT value FROM bot_state WHERE key = %s", (key,))
            return json.loads(result[0][0]) if result else {}
        except Exception as e:
            logger.error(f"Ошибка загрузки состояния: {e}")
            return {}
