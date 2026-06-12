# Household App — Project Context

## What This Is

A shared household web app for two people to manage a to-do list and a groceries list together. Either person can add, complete, delete, and reorder items. Data persists across sessions.

## Stack

- **Frontend**: Vanilla HTML/CSS/JavaScript (no frameworks)
- **Backend**: Python + Flask
- **Database**: PostgreSQL (hosted on Render)
- **Hosting**: Render (free tier, auto-deploys from GitHub on push)

## Repository

- **GitHub**: `git@github.com:Zlacker318/Zlacker318.git`
- **Local path**: `~/Documents/Zlacker318/`
- **App folder**: `household-app/`
- **Branch**: `master`
- **Git user**: Zlacker318 / carlosrosario318@gmail.com
- **SSH auth**: ed25519 key configured at `~/.ssh/id_ed25519`

## File Structure

```
household-app/
├── app.py                  # Flask backend
├── requirements.txt        # flask, flask-cors, gunicorn, psycopg2-binary
├── templates/
│   └── index.html          # Single-page UI
└── static/
    ├── css/
    │   └── style.css
    └── js/
        └── main.js
```

## Backend (app.py)

Flask app with these endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Serves the HTML page |
| GET | `/api/<section>` | Returns all items ordered by position |
| POST | `/api/<section>` | Adds item (appended to end of queue) |
| PATCH | `/api/<section>/<id>` | Toggles done/undone |
| POST | `/api/<section>/reorder` | Saves new order (accepts `{ ids: [...] }`) |
| DELETE | `/api/<section>/<id>` | Deletes item |

`<section>` is either `todos` or `groceries`. Both are validated against an allowlist.

Database is initialized on startup (`init_db()` runs at module level so it works under gunicorn). Uses `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` so existing tables get the `position` column without breaking.

## Database Schema

Both `todos` and `groceries` tables have the same shape:

```sql
CREATE TABLE IF NOT EXISTS todos (
    id       SERIAL PRIMARY KEY,
    text     TEXT NOT NULL,
    done     BOOLEAN DEFAULT FALSE,
    position INTEGER DEFAULT 0
);
```

`position` is an integer used for manual ordering. New items get `MAX(position) + 1`. Items are fetched `ORDER BY position ASC, id ASC`.

## Frontend (main.js)

- On load: fetches and renders both lists
- Add item: via input + button or Enter key
- Toggle done: click on item text (strikes through)
- Delete: click `x` button
- Reorder: drag and drop via the `⠿` grip handle
  - Desktop: uses HTML5 `dragstart/dragover/drop` events
  - Mobile: uses `touchstart/touchmove/touchend` on the grip; uses `pointer-events: none` trick during touchmove so `elementFromPoint` can detect the item underneath the finger
  - On drop/touchend: DOM is updated immediately, then `POST /api/<section>/reorder` syncs positions to DB

## Render Deployment

- **Service type**: Web Service
- **Root directory**: `household-app`
- **Build command**: `pip install -r requirements.txt`
- **Start command**: `gunicorn app:app`
- **Environment variable**: `DATABASE_URL` set to the Render PostgreSQL internal connection string
- Auto-deploys when `master` is pushed to GitHub

## Known Issues Fixed

- macOS quarantine flag on VS Code removed with `xattr -dr com.apple.quarantine`
- `init_db()` was inside `if __name__ == "__main__"` — moved to module level so it runs under gunicorn
- SQLite was used initially but wiped on Render restarts — migrated to PostgreSQL
- HTML5 drag-and-drop doesn't work on mobile — fixed with touch event handlers

## What's Next (Ideas)

- User authentication (so each person has their own identity)
- More sections (e.g. bills, chores)
- Due dates or priorities on to-do items
- Push notifications when items are added
