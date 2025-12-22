from flask import Flask, jsonify, request, send_from_directory
import sqlite3
import json
import secrets
from datetime import datetime
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # ✅ Autorise toutes les origines (pour le développement)
app = Flask(__name__)
DB_PATH = 'database.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Table des restaurants
    c.execute('''
        CREATE TABLE IF NOT EXISTS restaurants (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE
        )
    ''')
    # Table des plats
    c.execute('''
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            restaurant_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT,
            price TEXT,
            image_data TEXT,
            FOREIGN KEY (restaurant_id) REFERENCES restaurants (id)
        )
    ''')
    # Table des commandes
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            restaurant_id TEXT NOT NULL,
            table_number INTEGER NOT NULL,
            items TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            total_price REAL DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (restaurant_id) REFERENCES restaurants (id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# === API : inscription d'un restaurant ===
@app.route('/api/register', methods=['POST'])
def register_restaurant():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    if not name or not email:
        return jsonify({"error": "Nom et email requis"}), 400

    conn = get_db()
    # Vérifier si l'email existe déjà
    existing = conn.execute('SELECT 1 FROM restaurants WHERE email = ?', (email,)).fetchone()
    if existing:
        conn.close()
        return jsonify({"error": "Email déjà utilisé"}), 400

    restaurant_id = "rest_" + secrets.token_urlsafe(8)
    conn.execute('INSERT INTO restaurants (id, name, email) VALUES (?, ?, ?)', (restaurant_id, name, email))
    conn.commit()
    conn.close()

    base_url = os.getenv("BASE_URL", "http://localhost:5000")
    return jsonify({
        "restaurant_id": restaurant_id,
        "client_link": f"{base_url}/client/{restaurant_id}",
        "staff_link": f"{base_url}/staff/{restaurant_id}"
    }), 201

# === Utilitaire : valider restaurant_id ===
def validate_restaurant(restaurant_id):
    if not restaurant_id or not restaurant_id.startswith("rest_"):
        return False
    conn = get_db()
    exists = conn.execute('SELECT 1 FROM restaurants WHERE id = ?', (restaurant_id,)).fetchone()
    conn.close()
    return exists is not None

# === API : menu (avec restaurant_id) ===
@app.route('/api/menu/<restaurant_id>')
def api_menu(restaurant_id):
    if not validate_restaurant(restaurant_id):
        return jsonify({"error": "Restaurant non trouvé"}), 404
    conn = get_db()
    items = conn.execute('SELECT * FROM menu_items WHERE restaurant_id = ?', (restaurant_id,)).fetchall()
    conn.close()
    return jsonify([dict(item) for item in items])

# === API : passer une commande ===
@app.route('/api/order/<restaurant_id>', methods=['POST'])
def create_order(restaurant_id):
    if not validate_restaurant(restaurant_id):
        return jsonify({"error": "Restaurant non trouvé"}), 404

    data = request.json
    table_number = data.get('table_number')
    items = data.get('items')
    total_price = data.get('total_price', 0)

    if not table_number or not items:
        return jsonify({"error": "Données manquantes"}), 400

    items_json = json.dumps(items, ensure_ascii=False)

    conn = get_db()
    conn.execute(
        'INSERT INTO orders (restaurant_id, table_number, items, total_price) VALUES (?, ?, ?, ?)',
        (restaurant_id, table_number, items_json, total_price)
    )
    order_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.commit()
    conn.close()
    return jsonify({"message": "Commande envoyée", "order_id": order_id}), 201

# === API : commandes en attente ===
@app.route('/api/orders/pending/<restaurant_id>')
def pending_orders(restaurant_id):
    if not validate_restaurant(restaurant_id):
        return jsonify({"error": "Restaurant non trouvé"}), 404
    conn = get_db()
    orders = conn.execute('SELECT * FROM orders WHERE restaurant_id = ? AND status = "pending"', (restaurant_id,)).fetchall()
    conn.close()
    return jsonify([dict(order) for order in orders])

# === API : commandes confirmées ===
@app.route('/api/orders/confirmed/<restaurant_id>')
def confirmed_orders(restaurant_id):
    if not validate_restaurant(restaurant_id):
        return jsonify({"error": "Restaurant non trouvé"}), 404
    conn = get_db()
    orders = conn.execute('SELECT * FROM orders WHERE restaurant_id = ? AND status = "confirmed"', (restaurant_id,)).fetchall()
    conn.close()
    return jsonify([dict(order) for order in orders])

# === API : confirmer commande ===
@app.route('/api/order/<int:order_id>/confirm', methods=['POST'])
def confirm_order(order_id):
    conn = get_db()
    order = conn.execute('SELECT restaurant_id FROM orders WHERE id = ?', (order_id,)).fetchone()
    if not order:
        conn.close()
        return jsonify({"error": "Commande non trouvée"}), 404
    conn.execute('UPDATE orders SET status = "confirmed" WHERE id = ?', (order_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Commande confirmée"}), 200

# === API : supprimer une commande ===
@app.route('/api/order/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    conn = get_db()
    exists = conn.execute('SELECT 1 FROM orders WHERE id = ?', (order_id,)).fetchone()
    if not exists:
        conn.close()
        return jsonify({"error": "Commande non trouvée"}), 404
    conn.execute('DELETE FROM orders WHERE id = ?', (order_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Commande supprimée"}), 200

# === API : statut commande ===
@app.route('/api/order/<int:order_id>/status')
def order_status(order_id):
    conn = get_db()
    order = conn.execute('SELECT status FROM orders WHERE id = ?', (order_id,)).fetchone()
    conn.close()
    if order:
        return jsonify({"status": order['status']})
    return jsonify({"error": "Commande non trouvée"}), 404

# === API : ajouter un plat ===
@app.route('/api/menu/add/<restaurant_id>', methods=['POST'])
def add_menu_item(restaurant_id):
    if not validate_restaurant(restaurant_id):
        return jsonify({"error": "Restaurant non trouvé"}), 404

    data = request.json
    name = data.get('name')
    description = data.get('description')
    category = data.get('category')
    price = data.get('price')
    image_data = data.get('image_data')
    if not all([name, description, category, price]):
        return jsonify({"error": "Données manquantes"}), 400

    conn = get_db()
    c = conn.cursor()
    c.execute('''
        INSERT INTO menu_items (restaurant_id, name, description, category, price, image_data)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (restaurant_id, name, description, category, price, image_data))
    conn.commit()
    item_id = c.lastrowid
    conn.close()
    return jsonify({"message": "Plat ajouté", "id": item_id}), 201

# === API : supprimer un plat ===
@app.route('/api/menu/<int:item_id>', methods=['DELETE'])
def delete_menu_item(item_id):
    conn = get_db()
    exists = conn.execute('SELECT 1 FROM menu_items WHERE id = ?', (item_id,)).fetchone()
    if not exists:
        conn.close()
        return jsonify({"error": "Plat non trouvé"}), 404
    conn.execute('DELETE FROM menu_items WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Plat supprimé"}), 200

# === API : statistiques du jour ===
@app.route('/api/stats/today/<restaurant_id>')
def stats_today(restaurant_id):
    if not validate_restaurant(restaurant_id):
        return jsonify({"error": "Restaurant non trouvé"}), 404

    today = datetime.now().strftime('%Y-%m-%d')
    conn = get_db()
    total = conn.execute('''
        SELECT SUM(total_price) as total
        FROM orders
        WHERE restaurant_id = ? AND status = "confirmed" AND DATE(timestamp) = ?
    ''', (restaurant_id, today)).fetchone()['total'] or 0
    count = conn.execute('''
        SELECT COUNT(*) as count
        FROM orders
        WHERE restaurant_id = ? AND status = "confirmed" AND DATE(timestamp) = ?
    ''', (restaurant_id, today)).fetchone()['count']
    conn.close()
    return jsonify({
        "total_sales": round(total, 2),
        "orders_count": count
    })

# === Servir les pages ===
@app.route('/client/<restaurant_id>')
def client_page(restaurant_id):
    if not validate_restaurant(restaurant_id):
        return "Restaurant non trouvé", 404
    response = send_from_directory('../client', 'index.html')
    response.headers['X-Restaurant-ID'] = restaurant_id
    return response

@app.route('/staff/<restaurant_id>')
def staff_page(restaurant_id):
    if not validate_restaurant(restaurant_id):
        return "Restaurant non trouvé", 404
    response = send_from_directory('../staff', 'dashboard.html')
    response.headers['X-Restaurant-ID'] = restaurant_id
    return response

# ✅ Nouvelle route : page d'inscription
@app.route('/register')
def register_page():
    return send_from_directory('../register', 'register.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)