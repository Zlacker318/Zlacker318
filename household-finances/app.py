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
                CREATE TABLE IF NOT EXISTS incomes (
                    id SERIAL PRIMARY KEY,
                    person TEXT NOT NULL,
                    amount NUMERIC(10,2) NOT NULL,
                    month TEXT NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id SERIAL PRIMARY KEY,
                    category TEXT NOT NULL,
                    description TEXT,
                    amount NUMERIC(10,2) NOT NULL,
                    month TEXT NOT NULL
                )
            """)
        conn.commit()

@app.route("/")
def index():
    return render_template("index.html")

# --- Incomes ---

@app.route("/api/incomes", methods=["GET"])
def get_incomes():
    month = request.args.get("month")
    with get_db() as conn:
        with conn.cursor() as cur:
            if month:
                cur.execute("SELECT * FROM incomes WHERE month = %s ORDER BY id ASC", (month,))
            else:
                cur.execute("SELECT * FROM incomes ORDER BY month DESC, id ASC")
            rows = cur.fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/incomes", methods=["POST"])
def add_income():
    data = request.json
    person = data.get("person", "").strip()
    amount = data.get("amount")
    month = data.get("month", "").strip()
    if not person or not amount or not month:
        return jsonify({"error": "person, amount, and month are required"}), 400
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO incomes (person, amount, month) VALUES (%s, %s, %s) RETURNING *",
                (person, amount, month)
            )
            row = cur.fetchone()
        conn.commit()
    return jsonify(dict(row)), 201

@app.route("/api/incomes/<int:item_id>", methods=["DELETE"])
def delete_income(item_id):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM incomes WHERE id = %s", (item_id,))
        conn.commit()
    return jsonify({"deleted": item_id})

# --- Expenses ---

@app.route("/api/expenses", methods=["GET"])
def get_expenses():
    month = request.args.get("month")
    with get_db() as conn:
        with conn.cursor() as cur:
            if month:
                cur.execute("SELECT * FROM expenses WHERE month = %s ORDER BY id ASC", (month,))
            else:
                cur.execute("SELECT * FROM expenses ORDER BY month DESC, id ASC")
            rows = cur.fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/expenses", methods=["POST"])
def add_expense():
    data = request.json
    category = data.get("category", "").strip()
    description = data.get("description", "").strip()
    amount = data.get("amount")
    month = data.get("month", "").strip()
    if not category or not amount or not month:
        return jsonify({"error": "category, amount, and month are required"}), 400
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO expenses (category, description, amount, month) VALUES (%s, %s, %s, %s) RETURNING *",
                (category, description or None, amount, month)
            )
            row = cur.fetchone()
        conn.commit()
    return jsonify(dict(row)), 201

@app.route("/api/expenses/<int:item_id>", methods=["DELETE"])
def delete_expense(item_id):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM expenses WHERE id = %s", (item_id,))
        conn.commit()
    return jsonify({"deleted": item_id})

# --- Summary (for charts) ---

@app.route("/api/summary", methods=["GET"])
def get_summary():
    month = request.args.get("month")
    with get_db() as conn:
        with conn.cursor() as cur:
            if month:
                cur.execute("SELECT person, SUM(amount) as total FROM incomes WHERE month = %s GROUP BY person", (month,))
            else:
                cur.execute("SELECT person, SUM(amount) as total FROM incomes GROUP BY person")
            incomes_by_person = [dict(r) for r in cur.fetchall()]

            if month:
                cur.execute("SELECT category, SUM(amount) as total FROM expenses WHERE month = %s GROUP BY category", (month,))
            else:
                cur.execute("SELECT category, SUM(amount) as total FROM expenses GROUP BY category")
            expenses_by_category = [dict(r) for r in cur.fetchall()]

            if month:
                cur.execute("SELECT COALESCE(SUM(amount), 0) as total FROM incomes WHERE month = %s", (month,))
            else:
                cur.execute("SELECT COALESCE(SUM(amount), 0) as total FROM incomes")
            total_income = float(cur.fetchone()["total"])

            if month:
                cur.execute("SELECT COALESCE(SUM(amount), 0) as total FROM expenses WHERE month = %s", (month,))
            else:
                cur.execute("SELECT COALESCE(SUM(amount), 0) as total FROM expenses")
            total_expenses = float(cur.fetchone()["total"])

    return jsonify({
        "incomes_by_person": incomes_by_person,
        "expenses_by_category": expenses_by_category,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "balance": total_income - total_expenses
    })

init_db()

if __name__ == "__main__":
    app.run(debug=True)
