# Patient Registry UI

A minimal web UI to view, edit, and soft-delete patient records from the PostgreSQL database.

## Features

- View all active patients in a table
- Search by name or phone number
- Edit any patient field inline via modal
- Soft-delete patients (sets `deleted_at`, does not remove from DB)
- No create — records are created only via the voice agent

## Tech Stack

- Python + Flask
- Vanilla HTML/CSS/JS (no framework)
- PostgreSQL via psycopg2

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |

## Local Development

```bash
pip install -r requirements.txt
cp .env.example .env   # add your DATABASE_URL
python api/index.py
```

Open http://localhost:5000
