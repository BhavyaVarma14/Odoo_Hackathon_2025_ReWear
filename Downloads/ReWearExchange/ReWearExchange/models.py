from datetime import datetime
from app import db
from flask_login import UserMixin
from sqlalchemy import func

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    coin_balance = db.Column(db.Integer, default=0)
    avatar = db.Column(db.String(200), default='')
    bio = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    items = db.relationship('Item', backref='owner', lazy=True, foreign_keys='Item.user_id')
    notifications = db.relationship('Notification', backref='user', lazy=True)
    swap_requests_sent = db.relationship('SwapRequest', backref='requester', lazy=True, foreign_keys='SwapRequest.requester_id')
    swap_requests_received = db.relationship('SwapRequest', backref='owner', lazy=True, foreign_keys='SwapRequest.owner_id')
    addresses = db.relationship('Address', backref='user', lazy=True)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    
    # Relationships
    items = db.relationship('Item', backref='category', lazy=True)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    size = db.Column(db.String(20), nullable=False)
    condition = db.Column(db.String(50), nullable=False)
    tags = db.Column(db.String(500), default='')
    coin_value = db.Column(db.Integer, default=0)
    suggested_coin_value = db.Column(db.Integer, default=0)  # User's suggested coin value
    status = db.Column(db.String(20), default='pending')  # pending, approved, swapped, rejected
    images = db.Column(db.Text, default='')  # JSON string of image filenames
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    
    # Relationships - removed ambiguous swap_requests relationship

class SwapRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, default='')
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    responded_at = db.Column(db.DateTime)
    
    # Foreign keys
    requested_item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)  # Item being requested
    offered_item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)   # Item being offered in exchange
    requester_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    requested_item = db.relationship('Item', foreign_keys=[requested_item_id], backref='received_swap_requests')
    offered_item = db.relationship('Item', foreign_keys=[offered_item_id], backref='offered_in_swaps')

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(500), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # swap_request, item_approved, item_redeemed, etc.
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)  # earned, spent
    amount = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=True)

class Address(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    street_address = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class RedemptionRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, shipped
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    responded_at = db.Column(db.DateTime)
    message = db.Column(db.Text, default='')
    
    # Foreign keys
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    requester_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    address_id = db.Column(db.Integer, db.ForeignKey('address.id'), nullable=False)
    
    # Relationships
    item = db.relationship('Item', backref='redemption_requests')
    requester = db.relationship('User', foreign_keys=[requester_id], backref='sent_redemptions')
    seller = db.relationship('User', foreign_keys=[seller_id], backref='received_redemptions')
    address = db.relationship('Address', backref='redemption_requests')
