from datetime import date, datetime
import os
import sqlite3
from flask import Flask, g, redirect, render_template, request, url_for, flash, jsonify

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, 'app.db')

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET', 'dev-secret')


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.executescript('''
    CREATE TABLE IF NOT EXISTS pantry_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        quantity REAL NOT NULL,
        unit TEXT NOT NULL,
        expires_on TEXT,
        category TEXT,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        ingredients_csv TEXT NOT NULL,
        instructions TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    ''')
    db.commit()
    db.close()


def parse_csv(v: str):
    return [x.strip().lower() for x in v.split(',') if x.strip()]


# Ensure DB schema exists in production (e.g., gunicorn on Render)
init_db()


@app.route('/')
def index():
    db = get_db()
    items = db.execute('SELECT * FROM pantry_items ORDER BY expires_on IS NULL, expires_on ASC, name ASC').fetchall()
    soon = []
    today = date.today()
    for i in items:
        if i['expires_on']:
            try:
                days = (datetime.strptime(i['expires_on'], '%Y-%m-%d').date() - today).days
                if days <= 3:
                    soon.append((i, days))
            except ValueError:
                pass
    return render_template('index.html', items=items, soon=soon)


@app.post('/items')
def add_item():
    name = request.form.get('name', '').strip()
    quantity = request.form.get('quantity', '').strip()
    unit = request.form.get('unit', '').strip() or 'pcs'
    expires_on = request.form.get('expires_on', '').strip() or None
    category = request.form.get('category', '').strip() or None

    if not name or not quantity:
        flash('Name and quantity are required.', 'error')
        return redirect(url_for('index'))

    try:
        q = float(quantity)
    except ValueError:
        flash('Quantity must be a number.', 'error')
        return redirect(url_for('index'))

    db = get_db()
    db.execute(
        'INSERT INTO pantry_items (name, quantity, unit, expires_on, category, created_at) VALUES (?, ?, ?, ?, ?, ?)',
        (name.lower(), q, unit, expires_on, category, datetime.utcnow().isoformat())
    )
    db.commit()
    flash('Item added.', 'ok')
    return redirect(url_for('index'))


@app.post('/items/<int:item_id>/delete')
def delete_item(item_id):
    db = get_db()
    db.execute('DELETE FROM pantry_items WHERE id = ?', (item_id,))
    db.commit()
    flash('Item removed.', 'ok')
    return redirect(url_for('index'))


@app.route('/recipes')
def recipes_page():
    db = get_db()
    recipes = db.execute('SELECT * FROM recipes ORDER BY title ASC').fetchall()
    pantry_items = db.execute('SELECT name FROM pantry_items').fetchall()
    pantry_set = {r['name'].lower() for r in pantry_items}

    enriched = []
    for r in recipes:
        needed = parse_csv(r['ingredients_csv'])
        have = [x for x in needed if x in pantry_set]
        missing = [x for x in needed if x not in pantry_set]
        score = int((len(have) / len(needed)) * 100) if needed else 0
        enriched.append({'recipe': r, 'have': have, 'missing': missing, 'score': score})

    enriched.sort(key=lambda x: (-x['score'], x['recipe']['title']))
    return render_template('recipes.html', recipes=enriched)


@app.post('/recipes')
def add_recipe():
    title = request.form.get('title', '').strip()
    ingredients = request.form.get('ingredients', '').strip()
    instructions = request.form.get('instructions', '').strip()
    if not title or not ingredients or not instructions:
        flash('Title, ingredients, instructions are required.', 'error')
        return redirect(url_for('recipes_page'))

    db = get_db()
    db.execute(
        'INSERT INTO recipes (title, ingredients_csv, instructions, created_at) VALUES (?, ?, ?, ?)',
        (title, ','.join(parse_csv(ingredients)), instructions, datetime.utcnow().isoformat())
    )
    db.commit()
    flash('Recipe added.', 'ok')
    return redirect(url_for('recipes_page'))


@app.route('/plan')
def meal_plan():
    db = get_db()
    recipes = db.execute('SELECT * FROM recipes').fetchall()
    pantry = {r['name'].lower() for r in db.execute('SELECT name FROM pantry_items').fetchall()}

    candidates = []
    for r in recipes:
        ing = parse_csv(r['ingredients_csv'])
        if not ing:
            continue
        have = sum(1 for i in ing if i in pantry)
        missing = [i for i in ing if i not in pantry]
        candidates.append({'title': r['title'], 'missing': missing, 'ratio': have/len(ing), 'instructions': r['instructions']})

    candidates.sort(key=lambda x: (-x['ratio'], len(x['missing'])))
    selected = candidates[:3]

    shopping = {}
    for s in selected:
        for m in s['missing']:
            shopping[m] = shopping.get(m, 0) + 1

    return render_template('plan.html', selected=selected, shopping=sorted(shopping.items(), key=lambda x: (-x[1], x[0])))


@app.route('/api/health')
def health():
    return jsonify({'ok': True, 'service': 'pantry-planner-mvp'})


if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5050)
