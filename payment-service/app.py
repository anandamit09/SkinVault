from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import requests

app = Flask(__name__)
CORS(app)

DB_NAME = "database.db"

#INIT DB
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT UNIQUE,
            user_id INTEGER,
            amount REAL,
            status TEXT
        )
    """)

    conn.commit()
    conn.close()


init_db()

#PAYMENT
@app.route('/pay', methods=['POST'])
def pay():
    data = request.json
    transaction_id = data.get("transaction_id")
    user_id = data.get("user_id")
    amount = data.get("amount")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    #Check idempotency (duplicate transaction)
    cursor.execute("SELECT * FROM transactions WHERE transaction_id=?", (transaction_id,))
    existing = cursor.fetchone()

    if existing:
        conn.close()
        return jsonify({
            "message": "Transaction already processed",
            "status": existing[4]
        })

    #Call User Service to deduct money
    try:
        response = requests.post(
            "http://127.0.0.1:5001/deduct-money",
            json={"user_id": user_id, "amount": amount}
        )

        result = response.json()

        if response.status_code != 200:
            #Payment failed
            cursor.execute(
                "INSERT INTO transactions (transaction_id, user_id, amount, status) VALUES (?, ?, ?, ?)",
                (transaction_id, user_id, amount, "failed")
            )
            conn.commit()
            conn.close()

            return jsonify({"error": result.get("error")}), 400

        #Payment success
        cursor.execute(
            "INSERT INTO transactions (transaction_id, user_id, amount, status) VALUES (?, ?, ?, ?)",
            (transaction_id, user_id, amount, "success")
        )

        conn.commit()
        conn.close()

        return jsonify({"message": "Payment successful"})

    except Exception as e:
        conn.close()
        return jsonify({"error": "User service not reachable"}), 500

#RUN
if __name__ == "__main__":
    app.run(port=5003, debug=True)