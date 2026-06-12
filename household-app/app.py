from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__)
CORS(app)

DB = "database.db"

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                done INTEGER DEFAULT 0
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS groceries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                done INTEGER DEFAULT 0
            )
        """)
        db.commit()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/<section>", methods=["GET"])
def get_items(section):
    with get_db() as db:
        items = db.execute(f"SELECT * FROM {section}").fetchall()
    return jsonify([dict(i) for i in items])

@app.route("/api/<section>", methods=["POST"])
def add_item(section):
    text = request.json.get("text", "").strip()
    if not text:
        return jsonify({"error": "empty"}), 400
    with get_db() as db:
        cur = db.execute(f"INSERT INTO {section} (text) VALUES (?)", (text,))
        db.commit()
        item = db.execute(f"SELECT * FROM {section} WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(dict(item)), 201

@app.route("/api/<section>/<int:item_id>", methods=["PATCH"])
def toggle_item(section, item_id):
    with get_db() as db:
        db.execute(f"UPDATE {section} SET done = 1 - done WHERE id = ?", (item_id,))
        db.commit()
        item = db.execute(f"SELECT * FROM {section} WHERE id = ?", (item_id,)).fetchone()
    return jsonify(dict(item))

@app.route("/api/<section>/<int:item_id>", methods=["DELETE"])
def delete_item(section, item_id):
    with get_db() as db:
        db.execute(f"DELETE FROM {section} WHERE id = ?", (item_id,))
        db.commit()
    return jsonify({"deleted": item_id})

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
