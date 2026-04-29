from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

DB_NAME = "database.db"

#DATABASE INIT
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            wallet REAL DEFAULT 1000
        )
    """)

    conn.commit()
    conn.close()


init_db()

#REGISTER
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                       (username, password))

        conn.commit()
        conn.close()

        return jsonify({"message": "User registered successfully"})

    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already exists"}), 400

#LOGIN
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username=? AND password=?",
                   (username, password))
    user = cursor.fetchone()

    conn.close()

    if user:
        return jsonify({"message": "Login successful", "user_id": user[0]})
    else:
        return jsonify({"error": "Invalid credentials"}), 401

#GET WALLET
@app.route('/wallet/<int:user_id>', methods=['GET'])
def get_wallet(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT wallet FROM users WHERE id=?", (user_id,))
    result = cursor.fetchone()

    conn.close()

    if result:
        return jsonify({"wallet": result[0]})
    else:
        return jsonify({"error": "User not found"}), 404

#ADD MONEY
@app.route('/add-money', methods=['POST'])
def add_money():
    data = request.json
    user_id = data.get("user_id")
    amount = data.get("amount")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("UPDATE users SET wallet = wallet + ? WHERE id=?",
                   (amount, user_id))

    conn.commit()
    conn.close()

    return jsonify({"message": "Money added successfully"})

#DEDUCT MONEY
@app.route('/deduct-money', methods=['POST'])
def deduct_money():
    data = request.json
    user_id = data.get("user_id")
    amount = data.get("amount")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT wallet FROM users WHERE id=?", (user_id,))
    result = cursor.fetchone()

    if not result:
        return jsonify({"error": "User not found"}), 404

    if result[0] < amount:
        return jsonify({"error": "Insufficient balance"}), 400

    cursor.execute("UPDATE users SET wallet = wallet - ? WHERE id=?",
                   (amount, user_id))

    conn.commit()
    conn.close()

    return jsonify({"message": "Payment successful"})

#RUN
if __name__ == "__main__":
    app.run(port=5001, debug=True)