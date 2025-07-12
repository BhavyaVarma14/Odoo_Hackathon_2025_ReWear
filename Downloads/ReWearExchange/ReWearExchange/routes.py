import os
import json
from flask import render_template, url_for, flash, redirect, request, abort, jsonify
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db
from models import User, Item, Category, SwapRequest, Notification, Transaction, Address, RedemptionRequest
from forms import LoginForm, RegisterForm, ItemUploadForm, SwapRequestForm, AdminApprovalForm, SearchForm, AddressForm
from utils import save_picture, create_notification, add_coins, spend_coins, get_unread_notification_count

# Initialize categories (moved to app.py initialization)

# Context processor for notifications
@app.context_processor
def inject_notifications():
    if current_user.is_authenticated:
        unread_count = get_unread_notification_count(current_user.id)
        return {'unread_notification_count': unread_count}
    return {'unread_notification_count': 0}

# Main routes
@app.route('/')
def index():
    # Get featured items (newest approved items)
    featured_items = Item.query.filter_by(status='approved').order_by(Item.approved_at.desc()).limit(6).all()
    return render_template('index.html', featured_items=featured_items)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=hashed_password,
            coin_balance=50  # Welcome bonus
        )
        db.session.add(user)
        db.session.commit()
        
        # Welcome notification
        create_notification(
            user.id,
            'Welcome to ReWear! You received 50 welcome coins.',
            'welcome'
        )
        
        flash('Registration successful! You received 50 welcome coins.', 'success')
        return redirect(url_for('auth_login'))
    
    return render_template('auth/register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def auth_login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('auth/login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get user's items
    user_items = Item.query.filter_by(user_id=current_user.id).order_by(Item.created_at.desc()).all()
    
    # Get recent transactions
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.created_at.desc()).limit(5).all()
    
    # Get pending swap requests
    incoming_requests = SwapRequest.query.filter_by(owner_id=current_user.id, status='pending').all()
    outgoing_requests = SwapRequest.query.filter_by(requester_id=current_user.id, status='pending').all()
    
    # Get pending redemption requests
    incoming_redemptions = RedemptionRequest.query.filter_by(seller_id=current_user.id, status='pending').all()
    outgoing_redemptions = RedemptionRequest.query.filter_by(requester_id=current_user.id).all()
    
    return render_template('dashboard.html', 
                         user_items=user_items, 
                         transactions=transactions,
                         incoming_requests=incoming_requests,
                         outgoing_requests=outgoing_requests,
                         incoming_redemptions=incoming_redemptions,
                         outgoing_redemptions=outgoing_redemptions)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_item():
    form = ItemUploadForm()
    
    if form.validate_on_submit():
        # Handle image uploads
        images = request.files.getlist('images')
        image_filenames = []
        
        for image in images:
            if image and image.filename:
                filename = save_picture(image, 'uploads')
                image_filenames.append(filename)
        
        # Create new item
        item = Item(
            title=form.title.data,
            description=form.description.data,
            category_id=form.category_id.data,
            size=form.size.data,
            condition=form.condition.data,
            tags=form.tags.data,
            suggested_coin_value=form.suggested_coin_value.data,
            images=json.dumps(image_filenames),
            user_id=current_user.id
        )
        
        db.session.add(item)
        db.session.commit()
        
        flash('Item uploaded successfully! It will be reviewed by our team.', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('upload_item.html', form=form)

@app.route('/browse')
def browse_items():
    form = SearchForm()
    page = request.args.get('page', 1, type=int)
    
    # Build query
    query = Item.query.filter_by(status='approved')
    
    # Apply filters if provided
    search_query = request.args.get('query', '')
    category_id = request.args.get('category_id', '')
    size = request.args.get('size', '')
    min_coins = request.args.get('min_coins', type=int)
    max_coins = request.args.get('max_coins', type=int)
    
    if search_query:
        query = query.filter(Item.title.contains(search_query) | Item.description.contains(search_query))
    if category_id:
        query = query.filter_by(category_id=int(category_id))
    if size:
        query = query.filter_by(size=size)
    if min_coins:
        query = query.filter(Item.coin_value >= min_coins)
    if max_coins:
        query = query.filter(Item.coin_value <= max_coins)
    
    items = query.order_by(Item.approved_at.desc()).paginate(
        page=page, per_page=12, error_out=False
    )
    
    # Pre-populate form with current filters
    form.query.data = search_query
    form.category_id.data = int(category_id) if category_id else None
    form.size.data = size
    form.min_coins.data = min_coins
    form.max_coins.data = max_coins
    
    return render_template('browse_items.html', items=items, form=form)

@app.route('/item/<int:id>')
def item_detail(id):
    item = Item.query.get_or_404(id)
    
    # Parse images
    images = []
    if item.images:
        try:
            images = json.loads(item.images)
        except:
            images = []
    
    # Check if current user can swap/redeem
    can_interact = (current_user.is_authenticated and 
                   current_user.id != item.user_id and 
                   item.status == 'approved')
    
    has_enough_coins = current_user.is_authenticated and current_user.coin_balance >= item.coin_value
    
    # Get user's available items for swapping (if authenticated)
    user_items = []
    if current_user.is_authenticated:
        user_items = Item.query.filter_by(user_id=current_user.id, status='approved').all()
    
    # Create swap form for the modal
    swap_form = SwapRequestForm(user_items=user_items)
    
    return render_template('item_detail.html', 
                         item=item, 
                         images=images,
                         can_interact=can_interact,
                         has_enough_coins=has_enough_coins,
                         swap_form=swap_form)

@app.route('/swap_request/<int:item_id>', methods=['GET', 'POST'])
@login_required
def swap_request(item_id):
    item = Item.query.get_or_404(item_id)
    
    # Check if user can make swap request
    if item.user_id == current_user.id:
        flash('You cannot swap your own item!', 'danger')
        return redirect(url_for('item_detail', id=item_id))
    
    if item.status != 'approved':
        flash('This item is not available for swap.', 'danger')
        return redirect(url_for('item_detail', id=item_id))
    
    # Check if user has items to offer
    user_items = Item.query.filter_by(user_id=current_user.id, status='approved').all()
    if not user_items:
        flash('You need to have approved items to make swap requests!', 'warning')
        return redirect(url_for('item_detail', id=item_id))
    
    form = SwapRequestForm(user_items=user_items)
    
    if form.validate_on_submit():
        # Get the offered item
        offered_item = Item.query.get(form.offered_item_id.data)
        if not offered_item or offered_item.user_id != current_user.id:
            flash('Invalid item selected!', 'danger')
            return redirect(url_for('item_detail', id=item_id))
        
        # Create swap request
        swap_request = SwapRequest(
            requested_item_id=item_id,
            offered_item_id=offered_item.id,
            requester_id=current_user.id,
            owner_id=item.user_id,
            message=form.message.data
        )
        
        db.session.add(swap_request)
        db.session.commit()
        
        # Create notification for item owner
        create_notification(
            item.user_id,
            f'{current_user.username} wants to swap their "{offered_item.title}" for your "{item.title}"',
            'swap_request'
        )
        
        flash('Swap request sent successfully!', 'success')
        return redirect(url_for('item_detail', id=item_id))
    
    return redirect(url_for('item_detail', id=item_id))

@app.route('/redeem/<int:item_id>', methods=['GET', 'POST'])
@login_required
def redeem_item(item_id):
    item = Item.query.get_or_404(item_id)
    
    # Check if user can redeem
    if item.user_id == current_user.id:
        flash('You cannot redeem your own item!', 'danger')
        return redirect(url_for('item_detail', id=item_id))
    
    if item.status != 'approved':
        flash('This item is not available for redemption.', 'danger')
        return redirect(url_for('item_detail', id=item_id))
    
    # Check if user has enough coins
    if current_user.coin_balance < item.coin_value:
        flash(f'You need {item.coin_value} coins to redeem this item. You have {current_user.coin_balance} coins.', 'danger')
        return redirect(url_for('item_detail', id=item_id))
    
    # Show address collection form
    form = AddressForm()
    
    if form.validate_on_submit():
        # Save address
        address = Address(
            user_id=current_user.id,
            name=form.name.data,
            phone=form.phone.data,
            street_address=form.street_address.data,
            city=form.city.data,
            state=form.state.data,
            postal_code=form.postal_code.data,
            country=form.country.data
        )
        db.session.add(address)
        db.session.flush()  # Get the address ID
        
        # Create redemption request (pending seller approval)
        redemption_request = RedemptionRequest(
            item_id=item.id,
            requester_id=current_user.id,
            seller_id=item.user_id,
            address_id=address.id,
            message=f'Redemption request for "{item.title}"'
        )
        db.session.add(redemption_request)
        db.session.commit()
        
        # Create notification for seller
        create_notification(
            item.user_id,
            f'{current_user.username} wants to redeem your item "{item.title}" for {item.coin_value} coins. Please review their address and approve.',
            'redemption_request'
        )
        
        flash('Redemption request sent! The seller will review your address and approve the transaction.', 'success')
        return redirect(url_for('item_detail', id=item_id))
    
    return render_template('redeem_popup.html', form=form, item=item)

@app.route('/respond_swap/<int:request_id>/<action>')
@login_required
def respond_swap(request_id, action):
    swap_request = SwapRequest.query.get_or_404(request_id)
    
    # Check if current user is the owner
    if swap_request.owner_id != current_user.id:
        abort(403)
    
    if action == 'accept':
        # Check if both items are still available
        if (swap_request.requested_item.status == 'approved' and 
            swap_request.offered_item.status == 'approved'):
            
            # Swap item ownership
            original_owner = swap_request.requested_item.user_id
            requester = swap_request.offered_item.user_id
            
            # Update item owners
            swap_request.requested_item.user_id = requester
            swap_request.offered_item.user_id = original_owner
            
            # Mark both items as swapped
            swap_request.requested_item.status = 'swapped'
            swap_request.offered_item.status = 'swapped'
            
            # Update swap request status
            swap_request.status = 'accepted'
            swap_request.responded_at = db.func.now()
            
            # Create notifications
            create_notification(
                swap_request.requester_id,
                f'Your swap request was accepted! You now own "{swap_request.requested_item.title}"',
                'swap_accepted'
            )
            
            create_notification(
                original_owner,
                f'Swap completed! You now own "{swap_request.offered_item.title}"',
                'swap_completed'
            )
            
            flash('Swap request accepted! Items have been exchanged.', 'success')
        else:
            flash('One or both items are no longer available for swap.', 'danger')
    
    elif action == 'reject':
        swap_request.status = 'rejected'
        swap_request.responded_at = db.func.now()
        
        create_notification(
            swap_request.requester_id,
            f'Your swap request for "{swap_request.item.title}" was rejected.',
            'swap_rejected'
        )
        
        flash('Swap request rejected.', 'info')
    
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/respond_redemption/<int:request_id>/<action>')
@login_required
def respond_redemption(request_id, action):
    redemption_request = RedemptionRequest.query.get_or_404(request_id)
    
    # Check if current user is the seller
    if redemption_request.seller_id != current_user.id:
        abort(403)
    
    if action == 'approve':
        # Check if requester still has enough coins
        if redemption_request.requester.coin_balance >= redemption_request.item.coin_value:
            # Process the redemption
            spend_coins(
                redemption_request.requester, 
                redemption_request.item.coin_value,
                f'Redeemed "{redemption_request.item.title}"',
                redemption_request.item.id
            )
            
            # Update status
            redemption_request.status = 'approved'
            redemption_request.item.status = 'swapped'
            redemption_request.responded_at = db.func.now()
            
            # Create notifications
            create_notification(
                redemption_request.requester_id,
                f'Your redemption for "{redemption_request.item.title}" was approved! The seller will ship it to your address.',
                'redemption_approved'
            )
            
            flash('Redemption approved! Make sure to ship the item to the provided address.', 'success')
        else:
            flash('Requester no longer has enough coins.', 'danger')
    
    elif action == 'reject':
        redemption_request.status = 'rejected'
        redemption_request.responded_at = db.func.now()
        
        create_notification(
            redemption_request.requester_id,
            f'Your redemption request for "{redemption_request.item.title}" was rejected.',
            'redemption_rejected'
        )
        
        flash('Redemption request rejected.', 'info')
    
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/profile/<username>')
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    items = Item.query.filter_by(user_id=user.id, status='approved').order_by(Item.approved_at.desc()).all()
    return render_template('profile.html', user=user, items=items)

@app.route('/notifications')
@login_required
def notifications():
    page = request.args.get('page', 1, type=int)
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(
        Notification.created_at.desc()
    ).paginate(page=page, per_page=20, error_out=False)
    
    # Mark all as read
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    
    return render_template('notifications.html', notifications=notifications)

# Admin routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.is_admin and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials', 'danger')
    
    return render_template('admin/login.html', form=form)

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        abort(403)
    
    # Get pending items
    pending_items = Item.query.filter_by(status='pending').order_by(Item.created_at.desc()).all()
    
    # Create form instances for each pending item
    forms = {}
    for item in pending_items:
        forms[item.id] = AdminApprovalForm()
    
    # Get site statistics
    total_users = User.query.count()
    total_items = Item.query.count()
    approved_items = Item.query.filter_by(status='approved').count()
    pending_approvals = Item.query.filter_by(status='pending').count()
    
    stats = {
        'total_users': total_users,
        'total_items': total_items,
        'approved_items': approved_items,
        'pending_approvals': pending_approvals
    }
    
    return render_template('admin/dashboard.html', pending_items=pending_items, stats=stats, forms=forms)

@app.route('/admin/approve/<int:item_id>', methods=['POST'])
@login_required
def admin_approve_item(item_id):
    if not current_user.is_admin:
        abort(403)
    
    item = Item.query.get_or_404(item_id)
    form = AdminApprovalForm()
    
    if form.validate_on_submit():
        coin_value = form.coin_value.data
        
        # Approve item
        item.status = 'approved'
        item.coin_value = coin_value
        item.approved_at = db.func.now()
        
        # Award coins to user
        add_coins(
            item.owner,
            coin_value,
            f'Item approved: "{item.title}"',
            item.id
        )
        
        # Create notification
        create_notification(
            item.user_id,
            f'Your item "{item.title}" was approved and you earned {coin_value} coins!',
            'item_approved'
        )
        
        db.session.commit()
        flash(f'Item approved and {coin_value} coins awarded to user!', 'success')
    else:
        flash('Please enter a valid coin value.', 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject/<int:item_id>')
@login_required
def admin_reject_item(item_id):
    if not current_user.is_admin:
        abort(403)
    
    item = Item.query.get_or_404(item_id)
    item.status = 'rejected'
    
    # Create notification
    create_notification(
        item.user_id,
        f'Your item "{item.title}" was rejected. Please review our guidelines and try again.',
        'item_rejected'
    )
    
    db.session.commit()
    flash('Item rejected.', 'info')
    return redirect(url_for('admin_dashboard'))
