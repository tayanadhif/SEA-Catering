
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from datetime import datetime, timedelta
import json
import os
import hashlib
import re
import secrets
from functools import wraps

app = Flask(__name__)
app.secret_key = 'sea-catering-secret-key-2024'

# Security configurations
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Simple file-based storage (in production, use a proper database)
USERS_FILE = 'data/users.json'
SUBSCRIPTIONS_FILE = 'data/subscriptions.json'
ORDERS_FILE = 'data/orders.json'

# Ensure data directory exists
os.makedirs('data', exist_ok=True)

def load_data(filename):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_data(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def sanitize_input(text):
    """Basic input sanitization to prevent XSS"""
    if not text:
        return text
    # Remove script tags and potentially dangerous HTML
    text = re.sub(r'<script.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<.*?>', '', text)  # Remove all HTML tags
    return text.strip()

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate Indonesian phone number"""
    pattern = r'^08[0-9]{8,13}$'
    return re.match(pattern, phone) is not None

def generate_csrf_token():
    """Generate CSRF token for forms"""
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(16)
    return session['csrf_token']

def validate_csrf_token(token):
    """Validate CSRF token"""
    return token and session.get('csrf_token') == token

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        users = load_data(USERS_FILE)
        user = users.get(session['user_id'])
        if not user or user.get('role') != 'admin':
            flash('Admin access required', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # CSRF Protection
        csrf_token = request.form.get('csrf_token')
        if not validate_csrf_token(csrf_token):
            flash('Security error. Please try again.', 'error')
            return render_template('auth/register.html', csrf_token=generate_csrf_token())
        
        # Input sanitization
        name = sanitize_input(request.form['name'])
        email = sanitize_input(request.form['email'])
        phone = sanitize_input(request.form['phone'])
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Validation
        if not all([name, email, phone, password]):
            flash('All fields are required', 'error')
            return render_template('auth/register.html', csrf_token=generate_csrf_token())
        
        if not validate_email(email):
            flash('Invalid email format', 'error')
            return render_template('auth/register.html', csrf_token=generate_csrf_token())
        
        if not validate_phone(phone):
            flash('Invalid phone number format', 'error')
            return render_template('auth/register.html', csrf_token=generate_csrf_token())
        
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return render_template('auth/register.html', csrf_token=generate_csrf_token())
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/register.html', csrf_token=generate_csrf_token())
        
        users = load_data(USERS_FILE)
        
        # Check if email already exists
        for user_id, user_data in users.items():
            if user_data['email'] == email:
                flash('Email already registered', 'error')
                return render_template('auth/register.html', csrf_token=generate_csrf_token())
        
        # Create new user
        user_id = str(len(users) + 1)
        users[user_id] = {
            'name': name,
            'email': email,
            'phone': phone,
            'password': hash_password(password),
            'role': 'admin' if email == 'admin@seacatering.com' else 'user',
            'created_at': datetime.now().isoformat(),
            'active': True,
            'last_login': None,
            'login_attempts': 0
        }
        
        save_data(USERS_FILE, users)
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/register.html', csrf_token=generate_csrf_token())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # CSRF Protection
        csrf_token = request.form.get('csrf_token')
        if not validate_csrf_token(csrf_token):
            flash('Security error. Please try again.', 'error')
            return render_template('auth/login.html', csrf_token=generate_csrf_token())
        
        email = sanitize_input(request.form['email'])
        password = request.form['password']
        
        users = load_data(USERS_FILE)
        hashed_password = hash_password(password)
        
        for user_id, user_data in users.items():
            if user_data['email'] == email:
                # Check for too many failed attempts
                if user_data.get('login_attempts', 0) >= 5:
                    flash('Account temporarily locked due to too many failed attempts', 'error')
                    return render_template('auth/login.html', csrf_token=generate_csrf_token())
                
                if user_data['password'] == hashed_password:
                    if user_data.get('active', True):
                        # Reset login attempts and update last login
                        user_data['login_attempts'] = 0
                        user_data['last_login'] = datetime.now().isoformat()
                        save_data(USERS_FILE, users)
                        
                        session['user_id'] = user_id
                        session['user_name'] = user_data['name']
                        session['user_role'] = user_data.get('role', 'user')
                        flash(f'Welcome back, {user_data["name"]}!', 'success')
                        return redirect(url_for('dashboard'))
                    else:
                        flash('Account is deactivated', 'error')
                        return render_template('auth/login.html', csrf_token=generate_csrf_token())
                else:
                    # Increment failed login attempts
                    user_data['login_attempts'] = user_data.get('login_attempts', 0) + 1
                    save_data(USERS_FILE, users)
                    break
        
        flash('Invalid email or password', 'error')
    
    return render_template('auth/login.html', csrf_token=generate_csrf_token())

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    if session.get('user_role') == 'admin':
        return redirect(url_for('admin_dashboard'))
    
    user_id = session['user_id']
    subscriptions = load_data(SUBSCRIPTIONS_FILE)
    orders = load_data(ORDERS_FILE)
    
    user_subscriptions = {k: v for k, v in subscriptions.items() if v['user_id'] == user_id}
    user_orders = {k: v for k, v in orders.items() if v['user_id'] == user_id}
    
    return render_template('dashboard/user.html', 
                         subscriptions=user_subscriptions, 
                         orders=user_orders)

@app.route('/subscribe', methods=['POST'])
@login_required
def subscribe():
    user_id = session['user_id']
    data = request.get_json()
    
    # Validate subscription data
    required_fields = ['plan', 'mealTypes', 'deliveryDays', 'totalPrice']
    for field in required_fields:
        if field not in data:
            return jsonify({'success': False, 'error': f'Missing {field}'})
    
    subscriptions = load_data(SUBSCRIPTIONS_FILE)
    
    # Generate subscription ID
    sub_id = str(len(subscriptions) + 1)
    
    # Create subscription
    subscription = {
        'user_id': user_id,
        'plan': data['plan'],
        'meal_types': data['mealTypes'],
        'delivery_days': data['deliveryDays'],
        'allergies': data.get('allergies', ''),
        'price_per_meal': data['pricePerMeal'],
        'total_monthly_price': data['totalPrice'],
        'status': 'pending_payment',
        'created_at': datetime.now().isoformat(),
        'next_billing_date': (datetime.now() + timedelta(days=30)).isoformat(),
        'active': True
    }
    
    subscriptions[sub_id] = subscription
    save_data(SUBSCRIPTIONS_FILE, subscriptions)
    
    return jsonify({'success': True, 'subscription_id': sub_id})

@app.route('/subscription/<sub_id>/cancel', methods=['POST'])
@login_required
def cancel_subscription(sub_id):
    subscriptions = load_data(SUBSCRIPTIONS_FILE)
    
    if sub_id in subscriptions and subscriptions[sub_id]['user_id'] == session['user_id']:
        subscriptions[sub_id]['status'] = 'cancelled'
        subscriptions[sub_id]['cancelled_at'] = datetime.now().isoformat()
        save_data(SUBSCRIPTIONS_FILE, subscriptions)
        flash('Subscription cancelled successfully', 'success')
    else:
        flash('Subscription not found', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/subscription/<sub_id>/reactivate', methods=['POST'])
@login_required
def reactivate_subscription(sub_id):
    subscriptions = load_data(SUBSCRIPTIONS_FILE)
    
    if sub_id in subscriptions and subscriptions[sub_id]['user_id'] == session['user_id']:
        subscriptions[sub_id]['status'] = 'active'
        subscriptions[sub_id]['next_billing_date'] = (datetime.now() + timedelta(days=30)).isoformat()
        save_data(SUBSCRIPTIONS_FILE, subscriptions)
        flash('Subscription reactivated successfully', 'success')
    else:
        flash('Subscription not found', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/payment/simulate/<sub_id>')
@login_required
def simulate_payment(sub_id):
    subscriptions = load_data(SUBSCRIPTIONS_FILE)
    
    if sub_id in subscriptions and subscriptions[sub_id]['user_id'] == session['user_id']:
        subscriptions[sub_id]['status'] = 'active'
        subscriptions[sub_id]['payment_status'] = 'paid'
        subscriptions[sub_id]['last_payment'] = datetime.now().isoformat()
        save_data(SUBSCRIPTIONS_FILE, subscriptions)
        
        # Create order record
        orders = load_data(ORDERS_FILE)
        order_id = str(len(orders) + 1)
        orders[order_id] = {
            'user_id': session['user_id'],
            'subscription_id': sub_id,
            'amount': subscriptions[sub_id]['total_monthly_price'],
            'status': 'paid',
            'created_at': datetime.now().isoformat(),
            'payment_method': 'simulated'
        }
        save_data(ORDERS_FILE, orders)
        
        flash('Payment successful! Your subscription is now active.', 'success')
    else:
        flash('Subscription not found', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    users = load_data(USERS_FILE)
    subscriptions = load_data(SUBSCRIPTIONS_FILE)
    orders = load_data(ORDERS_FILE)
    
    # Enhanced analytics for Level 5
    now = datetime.now()
    this_month = now.strftime('%Y-%m')
    last_month = (now.replace(day=1) - timedelta(days=1)).strftime('%Y-%m')
    
    # Calculate comprehensive statistics
    monthly_orders = [o for o in orders.values() if o['created_at'].startswith(this_month)]
    last_month_orders = [o for o in orders.values() if o['created_at'].startswith(last_month)]
    
    plan_distribution = {}
    for sub in subscriptions.values():
        plan = sub['plan']
        plan_distribution[plan] = plan_distribution.get(plan, 0) + 1
    
    recent_users = sorted(
        [(uid, u) for uid, u in users.items()], 
        key=lambda x: x[1]['created_at'], 
        reverse=True
    )[:10]
    
    stats = {
        'total_users': len(users),
        'active_users': len([u for u in users.values() if u.get('active', True)]),
        'new_users_this_month': len([u for u in users.values() if u['created_at'].startswith(this_month)]),
        'active_subscriptions': len([s for s in subscriptions.values() if s['status'] == 'active']),
        'pending_subscriptions': len([s for s in subscriptions.values() if s['status'] == 'pending_payment']),
        'cancelled_subscriptions': len([s for s in subscriptions.values() if s['status'] == 'cancelled']),
        'total_orders': len(orders),
        'monthly_orders': len(monthly_orders),
        'monthly_revenue': sum(float(o['amount']) for o in monthly_orders if o['status'] == 'paid'),
        'last_month_revenue': sum(float(o['amount']) for o in last_month_orders if o['status'] == 'paid'),
        'plan_distribution': plan_distribution,
        'avg_order_value': sum(float(o['amount']) for o in orders.values()) / len(orders) if orders else 0
    }
    
    # Calculate revenue growth
    if stats['last_month_revenue'] > 0:
        stats['revenue_growth'] = ((stats['monthly_revenue'] - stats['last_month_revenue']) / stats['last_month_revenue']) * 100
    else:
        stats['revenue_growth'] = 100 if stats['monthly_revenue'] > 0 else 0
    
    return render_template('dashboard/admin.html', 
                         users=users, 
                         subscriptions=subscriptions, 
                         orders=orders,
                         stats=stats,
                         recent_users=recent_users,
                         csrf_token=generate_csrf_token())

@app.route('/admin/user/<user_id>/toggle', methods=['POST'])
@admin_required
def toggle_user_status(user_id):
    users = load_data(USERS_FILE)
    
    if user_id in users:
        users[user_id]['active'] = not users[user_id].get('active', True)
        save_data(USERS_FILE, users)
        status = 'activated' if users[user_id]['active'] else 'deactivated'
        flash(f'User {status} successfully', 'success')
    else:
        flash('User not found', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf_token)

@app.route('/admin/analytics')
@admin_required
def analytics():
    """Enhanced analytics page for Level 5"""
    users = load_data(USERS_FILE)
    subscriptions = load_data(SUBSCRIPTIONS_FILE)
    orders = load_data(ORDERS_FILE)
    
    # Prepare data for charts
    monthly_data = {}
    plan_revenue = {'diet': 0, 'protein': 0, 'royal': 0}
    
    for order in orders.values():
        month = order['created_at'][:7]  # YYYY-MM
        if month not in monthly_data:
            monthly_data[month] = {'revenue': 0, 'orders': 0}
        monthly_data[month]['revenue'] += float(order['amount'])
        monthly_data[month]['orders'] += 1
    
    for sub in subscriptions.values():
        if sub['status'] == 'active':
            plan_revenue[sub['plan']] += float(sub['total_monthly_price'])
    
    return render_template('dashboard/analytics.html',
                         monthly_data=monthly_data,
                         plan_revenue=plan_revenue,
                         users=users,
                         subscriptions=subscriptions,
                         orders=orders)

@app.route('/admin/user/<user_id>/reset_attempts', methods=['POST'])
@admin_required
def reset_login_attempts(user_id):
    """Security feature: Reset failed login attempts"""
    csrf_token = request.form.get('csrf_token')
    if not validate_csrf_token(csrf_token):
        flash('Security error. Please try again.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    users = load_data(USERS_FILE)
    if user_id in users:
        users[user_id]['login_attempts'] = 0
        save_data(USERS_FILE, users)
        flash('Login attempts reset successfully', 'success')
    else:
        flash('User not found', 'error')
    
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
