from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Restaurant(db.Model):
    __tablename__ = 'restaurant'
    
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(32), unique=True, nullable=False)  # ex: "rest_a1b2c3"
    name = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Restaurant {self.public_id}: {self.name}>"

class Category(db.Model):
    __tablename__ = 'category'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    
    # Relations
    restaurant = db.relationship('Restaurant', backref=db.backref('categories', lazy=True, cascade='all, delete-orphan'))

    def __repr__(self):
        return f"<Category {self.name} ({self.restaurant.public_id})>"

class Dish(db.Model):
    __tablename__ = 'dish'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)  # En MAD (nombre, ex: 35.0)
    image_base64 = db.Column(db.Text, nullable=True)  # Données Base64 de l'image
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    
    # Relations
    category = db.relationship('Category', backref=db.backref('dishes', lazy=True, cascade='all, delete-orphan'))
    restaurant = db.relationship('Restaurant', backref=db.backref('dishes', lazy=True, cascade='all, delete-orphan'))

    def __repr__(self):
        return f"<Dish {self.name} ({self.restaurant.public_id})>"

class Order(db.Model):
    __tablename__ = 'order'
    
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    table_number = db.Column(db.String(20), nullable=True)  # Peut être "5", "Terrasse", etc.
    status = db.Column(db.String(20), default="pending")  # pending, validated, completed, canceled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relation
    restaurant = db.relationship('Restaurant', backref=db.backref('orders', lazy=True, cascade='all, delete-orphan'))

    def __repr__(self):
        return f"<Order {self.id} - {self.status} ({self.restaurant.public_id})>"

class OrderItem(db.Model):
    __tablename__ = 'order_item'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    dish_id = db.Column(db.Integer, db.ForeignKey('dish.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    notes = db.Column(db.Text, nullable=True)
    
    # Relations
    dish = db.relationship('Dish')
    order = db.relationship('Order', backref=db.backref('items', lazy=True, cascade='all, delete-orphan'))

    def __repr__(self):
        return f"<OrderItem {self.quantity}x {self.dish.name} (Order {self.order_id})>"