# bot\src\database.py
import sqlite3
import re
from functools import lru_cache
import threading

class ProductDatabase:
    # Используем локальную память потока для хранения соединений
    local = threading.local()
    
    def __init__(self, db_path='products.db'):
        self.db_path = db_path
        # Создаем таблицы при инициализации
        self._init_db()

    def get_connection(self):
        """Возвращает соединение, специфичное для текущего потока"""
        if not hasattr(self.local, 'connection'):
            self.local.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        return self.local.connection

    def _init_db(self):
        """Создает таблицы, если они не существуют"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        try:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    benefits TEXT,
                    ingredients TEXT,
                    usage TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
        finally:
            conn.close()

    def product_exists(self, product_id):
        """Проверяет существование продукта"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM products WHERE id = ?", (product_id,))
        return cursor.fetchone() is not None 

    def add_product(self, product_data):
        """Добавляет новый продукт в базу"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO products (id, name, description, benefits, ingredients, usage)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            product_data.get('id'),
            product_data['name'],
            product_data['description'],
            product_data['benefits'],
            product_data['ingredients'],
            product_data['usage']
        ))
        conn.commit()
        return cursor.lastrowid
    
    def search_products(self, query, top_n=3):
        """Простой текстовый поиск по ключевым словам"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Разбиваем запрос на ключевые слова
        keywords = re.findall(r'\w+', query.lower())
        if not keywords:
            return []
        
        # Создаем условие поиска
        conditions = []
        params = []
        for keyword in keywords:
            conditions.append("(name LIKE ? OR description LIKE ? OR benefits LIKE ?)")
            params.extend([f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'])
        
        where_clause = " OR ".join(conditions)
        
        cursor.execute(f'''
            SELECT id, name, description, benefits, ingredients, usage 
            FROM products 
            WHERE {where_clause}
            LIMIT ?
        ''', (*params, top_n))
        
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

# Пример заполнения БД
if __name__ == "__main__":
    db = ProductDatabase()
    
    sample_product = {
        "id": 1,
        "name": "Коллаген Ультра",
        "description": "Гидролизованный коллаген с витамином C",
        "benefits": "Улучшает состояние кожи, волос и ногтей, поддерживает здоровье суставов",
        "ingredients": "Коллаген гидролизованный (10 г), витамин C (80 мг)",
        "usage": "Принимать по 1 саше в день, растворив в воде"
    }
    
    db.add_product(sample_product)
    print("Демонстрационный продукт добавлен в БД")
    print("Результаты поиска:", db.search_products("коллаген кожа"))