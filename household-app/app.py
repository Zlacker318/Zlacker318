import os
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
CORS(app)

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_db():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS todos (
                    id SERIAL PRIMARY KEY,
                    text TEXT NOT NULL,
                    done BOOLEAN DEFAULT FALSE
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS groceries (
                    id SERIAL PRIMARY KEY,
                    text TEXT NOT NULL,
                    done BOOLEAN DEFAULT FALSE
                )
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
            cur.execute(f"SELECT * FROM {section}")
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
            cur.execute(f"INSERT INTO {section} (text) VALUES (%s) RETURNING *", (text,))
            item = cur.fetchone()
        conn.commit()
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
