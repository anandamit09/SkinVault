from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

DB_NAME = "database.db"

#INIT DB
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price REAL,
            stock INTEGER,
            image TEXT
        )
    """)

    conn.commit()
    conn.close()


init_db()

#ADD SKIN
@app.route('/add-skin', methods=['POST'])
def add_skin():
    data = request.json
    name = data.get("name")
    price = data.get("price")
    stock = data.get("stock")
    image = data.get("image")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("INSERT INTO skins (name, price, stock, image) VALUES (?, ?, ?, ?)",
                   (name, price, stock, image))

    conn.commit()
    conn.close()

    return jsonify({"message": "Skin added"})

#GET ALL SKINS
@app.route('/skins', methods=['GET'])
def get_skins():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM skins")
    skins = cursor.fetchall()

    conn.close()

    result = []
    for s in skins:
        result.append({
            "id": s[0],
            "name": s[1],
            "price": s[2],
            "stock": s[3],
            "image": s[4]
        })

    return jsonify(result)

#GET SINGLE SKIN
@app.route('/skin/<int:skin_id>', methods=['GET'])
def get_skin(skin_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM skins WHERE id=?", (skin_id,))
    s = cursor.fetchone()

    conn.close()

    if not s:
        return jsonify({"error": "Skin not found"}), 404

    return jsonify({
        "id": s[0],
        "name": s[1],
        "price": s[2],
        "stock": s[3],
        "image": s[4]
    })

#REDUCE STOCK
@app.route('/reduce-stock', methods=['POST'])
def reduce_stock():
    data = request.json
    skin_id = data.get("skin_id")
    quantity = data.get("quantity", 1)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT stock FROM skins WHERE id=?", (skin_id,))
    result = cursor.fetchone()

    if not result:
        return jsonify({"error": "Skin not found"}), 404

    if result[0] < quantity:
        return jsonify({"error": "Out of stock"}), 400

    cursor.execute("UPDATE skins SET stock = stock - ? WHERE id=?",
                   (quantity, skin_id))

    conn.commit()
    conn.close()

    return jsonify({"message": "Stock reduced"})

#RUN
if __name__ == "__main__":
    app.run(port=5002, debug=True)