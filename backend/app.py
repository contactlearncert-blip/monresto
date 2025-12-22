from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import sqlite3
import json
import secrets
from datetime import datetime
import os

# ✅ Une seule instance Flask + CORS
app = Flask(__name__)
CORS(app)  # Autorise toutes les origines (nécessaire pour Vercel)

DB_PATH = 'database.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS restaurants (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            restaurant_id TEXT NOT NULL,
            name TEXT NOT IMPORTANT,
            description TEXT,
            category TEXT,
            price TEXT,
            image_data TEXT,
            FOREIGN KEY (restaurant_id) REFERENCES restaurants (id)
        )
    ''')
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

# === Toutes tes routes API ici (inchangées) ===
# ... (garde tout le reste de ton code tel quel)

# ✅ Route d'inscription
@app.route('/register')
def register_page():
    return send_from_directory('../register', 'register.html')

# ✅ Démarrage correct pour Railway
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # ✅ Utilise PORT fourni par Railway
    app.run(host='0.0.0.0', port=port, debug=False)