import os
import secrets
from PIL import Image
from flask import current_app
from models import Notification, Transaction, db

def save_picture(form_picture, folder):
    """Save uploaded image with random filename"""
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static', folder, picture_fn)
    
    # Resize image
    img = Image.open(form_picture)
    img.thumbnail((800, 800))
    img.save(picture_path)
    
    return picture_fn

def create_notification(user_id, message, notification_type):
    """Create a new notification for a user"""
    notification = Notification(
        user_id=user_id,
        message=message,
        type=notification_type
    )
    db.session.add(notification)
    db.session.commit()

def add_coins(user, amount, description, item_id=None):
    """Add coins to user account and create transaction record"""
    user.coin_balance += amount
    
    transaction = Transaction(
        user_id=user.id,
        type='earned',
        amount=amount,
        description=description,
        item_id=item_id
    )
    
    db.session.add(transaction)
    db.session.commit()

def spend_coins(user, amount, description, item_id=None):
    """Spend coins from user account and create transaction record"""
    if user.coin_balance < amount:
        return False
    
    user.coin_balance -= amount
    
    transaction = Transaction(
        user_id=user.id,
        type='spent',
        amount=amount,
        description=description,
        item_id=item_id
    )
    
    db.session.add(transaction)
    db.session.commit()
    return True

def get_unread_notification_count(user_id):
    """Get count of unread notifications for a user"""
    return Notification.query.filter_by(user_id=user_id, is_read=False).count()
