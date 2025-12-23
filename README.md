# HemenYe
Yemek siparis platformu (Flask + MySQL).

## Stack
- Backend: Flask, SQLAlchemy, Flask-Login, Flask-Migrate
- UI: Jinja2 + Bootstrap 5 + custom CSS
- DB: MySQL (default), optional local SQLite file exists for legacy usage

## Prerequisites
- Python 3.11+
- MySQL 8.x (or Docker)

## Local setup (venv)
```powershell
cd C:\Users\Seyit Kaan\Desktop\HemenYe
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### Environment
```powershell
copy .env.example .env
# edit .env for your MySQL credentials
```

### Run
```powershell
python run.py
```

### Seed sample data (optional)
```powershell
python seed_mysql.py
```

Open: http://127.0.0.1:5000

## Docker (one command)
```powershell
docker compose up --build
```
This starts:
- `web` on http://127.0.0.1:5000
- `db` on 3306 with database `hemenye`

## Troubleshooting
- If you see DB connection errors, verify `DATABASE_URL` in `.env`.
- MySQL local default URI can be overridden via `DATABASE_URL`.

## Tests
```powershell
python -m pytest
```

## Data model
- Documentation: `docs/data-model.md`
- Diagram source: `ERdiagram.puml`
