from flask import Flask, request, jsonify
import sqlite3
import requests
import uuid

app = Flask(__name__)

DB_NAME = "database.db"


#INIT DB
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            skin_id INTEGER,
            amount REAL,
            status TEXT
        )
    """)

    conn.commit()
    conn.close()


init_db()

#CREATE ORDER
@app.route('/create-order', methods=['POST'])
def create_order():
    data = request.json
    user_id = data.get("user_id")
    skin_id = data.get("skin_id")

    #Get product details
    try:
        product_res = requests.get(f"http://127.0.0.1:5002/skin/{skin_id}")
        if product_res.status_code != 200:
            return jsonify({"error": "Skin not found"}), 404

        product = product_res.json()
        price = product["price"]

    except:
        return jsonify({"error": "Product service not reachable"}), 500

    #Process payment
    transaction_id = str(uuid.uuid4())

    try:
        payment_res = requests.post(
            "http://127.0.0.1:5003/pay",
            json={
                "transaction_id": transaction_id,
                "user_id": user_id,
                "amount": price
            }
        )

        if payment_res.status_code != 200:
            return jsonify(payment_res.json()), 400

    except:
        return jsonify({"error": "Payment service not reachable"}), 500

    #educe stock
    try:
        stock_res = requests.post(
            "http://127.0.0.1:5002/reduce-stock",
            json={"skin_id": skin_id, "quantity": 1}
        )

        if stock_res.status_code != 200:
            return jsonify({"error": "Stock update failed"}), 400

    except:
        return jsonify({"error": "Product service not reachable"}), 500

    #Save order
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO orders (user_id, skin_id, amount, status) VALUES (?, ?, ?, ?)",
        (user_id, skin_id, price, "success")
    )

    conn.commit()
    conn.close()

    return jsonify({"message": "Order placed successfully"})

#GET ORDERS
@app.route('/orders/<int:user_id>', methods=['GET'])
def get_orders(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM orders WHERE user_id=?", (user_id,))
    rows = cursor.fetchall()

    conn.close()

    result = []
    for r in rows:
        result.append({
            "order_id": r[0],
            "user_id": r[1],
            "skin_id": r[2],
            "amount": r[3],
            "status": r[4]
        })

    return jsonify(result)

#RUN
if __name__ == "__main__":
    app.run(port=5004, debug=True)