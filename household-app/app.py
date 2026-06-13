import os
import json
import threading
import urllib.request
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
CORS(app)

DATABASE_URL = os.environ.get("DATABASE_URL")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
EMAIL_TO = os.environ.get("EMAIL_TO", "")

def send_notification(section, text):
    if not RESEND_API_KEY or not EMAIL_TO:
        return
    recipients = [e.strip() for e in EMAIL_TO.split(",") if e.strip()]
    if not recipients:
        return
    section_label = "To-Do List" if section == "todos" else "Groceries"
    payload = json.dumps({
        "from": "Household App <onboarding@resend.dev>",
        "to": recipients,
        "subject": f"[Household] New item added to {section_label}",
        "text": f'"{text}" was added to the {section_label}.'
    }).encode()
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json"
        }
    )
    try:
        urllib.request.urlopen(req)
    except Exception as e:
        app.logger.error(f"Email failed: {e}")

def get_db():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_db():
    with get_db() as conn:
        with conn.cursor() as cur:
            for table in ("todos", "groceries"):
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {table} (
                        id SERIAL PRIMARY KEY,
                        text TEXT NOT NULL,
                        done BOOLEAN DEFAULT FALSE,
                        position INTEGER DEFAULT 0
                    )
                """)
                cur.execute(f"""
                    ALTER TABLE {table} ADD COLUMN IF NOT EXISTS position INTEGER DEFAULT 0
                """)
                cur.execute(f"""
                    ALTER TABLE {table} ADD COLUMN IF NOT EXISTS progress TEXT DEFAULT 'not_started'
                """)
        conn.commit()

ALLOWED_SECTIONS = {"todos", "groceries"}

def validate(section):
    if section not in ALLOWED_SECTIONS:
        return jsonify({"error": "invalid section"}), 404
    return None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/<section>", methods=["GET"])
def get_items(section):
    err = validate(section)
    if err: return err
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT * FROM {section} ORDER BY position ASC, id ASC")
            items = cur.fetchall()
    return jsonify([dict(i) for i in items])

@app.route("/api/<section>", methods=["POST"])
def add_item(section):
    err = validate(section)
    if err: return err
    text = request.json.get("text", "").strip()
    if not text:
        return jsonify({"error": "empty"}), 400
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT COALESCE(MAX(position), -1) + 1 AS next_pos FROM {section}")
            next_pos = cur.fetchone()["next_pos"]
            cur.execute(
                f"INSERT INTO {section} (text, position) VALUES (%s, %s) RETURNING *",
                (text, next_pos)
            )
            item = cur.fetchone()
        conn.commit()
    threading.Thread(target=send_notification, args=(section, text), daemon=True).start()
    return jsonify(dict(item)), 201

@app.route("/api/<section>/<int:item_id>", methods=["PATCH"])
def toggle_item(section, item_id):
    err = validate(section)
    if err: return err
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(f"UPDATE {section} SET done = NOT done WHERE id = %s RETURNING *", (item_id,))
            item = cur.fetchone()
        conn.commit()
    return jsonify(dict(item))

ALLOWED_PROGRESS = {"not_started", "in_progress", "done"}

@app.route("/api/<section>/<int:item_id>/progress", methods=["PATCH"])
def set_progress(section, item_id):
    err = validate(section)
    if err: return err
    progress = request.json.get("progress")
    if progress not in ALLOWED_PROGRESS:
        return jsonify({"error": "invalid progress value"}), 400
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(f"UPDATE {section} SET progress = %s WHERE id = %s RETURNING *", (progress, item_id))
            item = cur.fetchone()
        conn.commit()
    return jsonify(dict(item))

@app.route("/api/<section>/reorder", methods=["POST"])
def reorder_items(section):
    err = validate(section)
    if err: return err
    ids = request.json.get("ids", [])
    with get_db() as conn:
        with conn.cursor() as cur:
            for pos, item_id in enumerate(ids):
                cur.execute(f"UPDATE {section} SET position = %s WHERE id = %s", (pos, item_id))
        conn.commit()
    return jsonify({"ok": True})

@app.route("/api/<section>/<int:item_id>", methods=["DELETE"])
def delete_item(section, item_id):
    err = validate(section)
    if err: return err
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(f"DELETE FROM {section} WHERE id = %s", (item_id,))
        conn.commit()
    return jsonify({"deleted": item_id})

init_db()

if __name__ == "__main__":
    app.run(debug=True)
