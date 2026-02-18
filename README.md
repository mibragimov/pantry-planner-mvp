# Pantry Planner MVP

A practical Flask web app inspired by recurring Reddit requests for "what can I cook with what I already have" and "how do I avoid food waste".

## Core Features

- Pantry inventory tracking (item, quantity, unit, category, expiry date)
- Expiry warning panel (items expiring within 3 days)
- Recipe library with free-form instructions and ingredient lists
- Recipe match scoring based on current pantry coverage
- Weekly meal planner that picks top 3 best-fit recipes
- Auto-generated shopping list from missing ingredients across selected meals
- Health endpoint: `GET /api/health`

## Tech Stack

- Python 3
- Flask
- SQLite (local file database: `app.db`)
- Server-rendered HTML templates (Jinja2)
- Plain CSS

## Run Locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open: `http://localhost:5050`

## Project Structure

- `app.py` - routes, DB access, planner logic
- `templates/` - HTML pages
- `static/styles.css` - UI styles
- `requirements.txt` - dependencies

## Usage Flow

1. Add pantry items on `/`
2. Add recipes on `/recipes`
3. Open `/plan` to get top meal suggestions and a shopping list

## Notes

- This is an MVP focused on useful workflow, not polished UI.
- SQLite schema auto-initializes on first run.
