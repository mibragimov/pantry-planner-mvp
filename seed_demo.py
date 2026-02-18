from app import init_db
import sqlite3
from datetime import datetime, timedelta

init_db()
db = sqlite3.connect('app.db')
now = datetime.utcnow().isoformat()

db.executemany(
    'INSERT INTO pantry_items (name, quantity, unit, expires_on, category, created_at) VALUES (?, ?, ?, ?, ?, ?)',
    [
        ('tomato', 4, 'pcs', (datetime.utcnow()+timedelta(days=2)).date().isoformat(), 'produce', now),
        ('pasta', 500, 'g', None, 'dry', now),
        ('egg', 6, 'pcs', (datetime.utcnow()+timedelta(days=5)).date().isoformat(), 'dairy', now),
    ]
)

db.executemany(
    'INSERT INTO recipes (title, ingredients_csv, instructions, created_at) VALUES (?, ?, ?, ?)',
    [
        ('Tomato Pasta', 'tomato,pasta,garlic,olive oil', 'Boil pasta. Saute tomato+garlic. Mix.', now),
        ('Omelette', 'egg,tomato,onion,salt', 'Beat eggs. Cook with chopped veggies.', now),
    ]
)

db.commit()
db.close()
print('Demo data inserted into app.db')
