import sqlite3

# Connexion à la base de données
conn = sqlite3.connect('backend/database.db')
c = conn.cursor()

# Table des restaurants (optionnel, mais utile pour la gestion)
c.execute('''
    CREATE TABLE IF NOT EXISTS restaurants (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE
    )
''')

# Table des plats — avec restaurant_id
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

# Table des commandes — avec restaurant_id
c.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        restaurant_id TEXT NOT NULL,
        table_number INTEGER NOT NULL,
        items TEXT NOT NULL,           -- JSON sous forme de texte
        status TEXT DEFAULT 'pending',
        total_price REAL DEFAULT 0,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (restaurant_id) REFERENCES restaurants (id)
    )
''')

# Validation et fermeture
conn.commit()
conn.close()

print("✅ Base de données initialisée pour multi-restaurants.")