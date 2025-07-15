import sqlite3
import re
import logging

logger = logging.getLogger(__name__)

class ProductDatabase:
    def __init__(self, db_path='products.db'):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Инициализация базы данных"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    benefits TEXT,
                    ingredients TEXT,
                    usage TEXT
                )
            ''')

    def add_product(self, product_data):
        """Добавление продукта в БД"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO products 
                (id, name, description, benefits, ingredients, usage)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                product_data['id'],
                product_data['name'],
                product_data.get('description', ''),
                product_data.get('benefits', ''),
                product_data.get('ingredients', ''),
                product_data.get('usage', '')
            ))

    def search_products(self, query, limit=3):
        """Поиск продуктов по ключевым словам"""
        keywords = [k.lower() for k in re.findall(r'\w+', query) if len(k) > 2]
        if not keywords:
            return []

        conditions = " OR ".join(["name LIKE ?"] * len(keywords))
        params = [f'%{k}%' for k in keywords]

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(f'''
                SELECT * FROM products 
                WHERE {conditions}
                LIMIT ?
            ''', (*params, limit))
            
            return [dict(zip([col[0] for col in cursor.description], row)) 
                    for row in cursor.fetchall()]