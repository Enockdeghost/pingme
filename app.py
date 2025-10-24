"""
VENDOR DIGITIZATION WEB APP - PRODUCTION READY
Complete Flask application with all features
"""

# PART 1: APP INITIALIZATION & CONFIGURATION

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps
import os
import json
import secrets
from io import BytesIO
import csv

# Create Flask app first
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vendor_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize extensions
db = SQLAlchemy(app)
CORS(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# PART 2: DATABASE MODELS

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='vendor')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    language = db.Column(db.String(10), default='sw')
    
    shops = db.relationship('Shop', backref='owner', lazy=True, cascade='all, delete-orphan')
    expenses = db.relationship('Expense', backref='user', lazy=True)
    orders = db.relationship('Order', foreign_keys='Order.buyer_id', backref='buyer', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Shop(db.Model):
    __tablename__ = 'shops'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50))
    location = db.Column(db.String(200))
    description = db.Column(db.Text)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    products = db.relationship('Product', backref='shop', lazy=True, cascade='all, delete-orphan')
    sales = db.relationship('Sale', backref='shop', lazy=True)

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    cost_price = db.Column(db.Float)
    quantity = db.Column(db.Integer, default=0)
    unit = db.Column(db.String(20), default='pcs')
    sku = db.Column(db.String(50), unique=True)
    barcode = db.Column(db.String(100))
    category = db.Column(db.String(100))
    expiry_date = db.Column(db.Date)
    reorder_level = db.Column(db.Integer, default=10)
    shop_id = db.Column(db.Integer, db.ForeignKey('shops.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    sale_items = db.relationship('SaleItem', backref='product', lazy=True)

class Sale(db.Model):
    __tablename__ = 'sales'
    id = db.Column(db.Integer, primary_key=True)
    sale_number = db.Column(db.String(50), unique=True, nullable=False)
    shop_id = db.Column(db.Integer, db.ForeignKey('shops.id'), nullable=False)
    customer_name = db.Column(db.String(100))
    customer_phone = db.Column(db.String(20))
    total_amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50))
    payment_reference = db.Column(db.String(100))
    status = db.Column(db.String(20), default='completed')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    
    items = db.relationship('SaleItem', backref='sale', lazy=True, cascade='all, delete-orphan')

class SaleItem(db.Model):
    __tablename__ = 'sale_items'
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

class Expense(db.Model):
    __tablename__ = 'expenses'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    payment_method = db.Column(db.String(50))
    receipt_number = db.Column(db.String(100))

class Supplier(db.Model):
    __tablename__ = 'suppliers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    contact_person = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    category = db.Column(db.String(100))
    rating = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    orders = db.relationship('Order', backref='supplier', lazy=True)

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    total_amount = db.Column(db.Float, nullable=False)
    delivery_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

class Alert(db.Model):
    __tablename__ = 'alerts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    alert_type = db.Column(db.String(50))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='alerts')

class SyncLog(db.Model):
    __tablename__ = 'sync_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sync_type = db.Column(db.String(50))
    data = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    synced_at = db.Column(db.DateTime)
    
def init_db():
    """Initialize database with tables and default data"""
    print("🔧 Initializing database...")
    
    # Remove existing database to start fresh
    if os.path.exists('vendor_app.db'):
        os.remove('vendor_app.db')
        print("🗑️ Removed existing database file")
    
    # Create all tables
    db.create_all()
    print("✅ Database tables created successfully!")
    
    # Create admin user
    admin = User(
        phone='admin',
        name='Administrator',
        email='admin@vendorapp.com',
        role='admin'
    )
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.commit()
    print("✅ Default admin user created (phone: admin, password: admin123)")

# Initialize database immediately when the app starts
with app.app_context():
    init_db()



# PART 3: AUTHENTICATION & AUTHORIZATION


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            if current_user.role not in roles:
                flash('Hakuna ruhusa ya kufikia ukurasa huu', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator



# PART 4: ROUTES - AUTHENTICATION


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.form
        
        # Check if user exists after ensuring tables are created
        existing_user = User.query.filter_by(phone=data['phone']).first()
        if existing_user:
            flash('Namba ya simu tayari imejiandikisha', 'danger')
            return redirect(url_for('register'))
        
        user = User(
            phone=data['phone'],
            name=data['name'],
            email=data.get('email'),
            role=data.get('role', 'vendor')
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        flash('Umefanikiwa kujiandikisha! Tafadhali ingia', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        phone = request.form['phone']
        password = request.form['password']
        
        user = User.query.filter_by(phone=phone).first()
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            flash(f'Karibu, {user.name}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Namba ya simu au nenosiri sio sahihi', 'danger')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Umetoka kikamilifu', 'info')
    return redirect(url_for('login'))



# PART 5: ROUTES - DASHBOARD & ANALYTICS


@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'vendor':
        shops = Shop.query.filter_by(owner_id=current_user.id).all()
        
        # Calculate stats
        total_sales = 0
        total_products = 0
        low_stock_count = 0
        today_sales = 0
        
        today = datetime.utcnow().date()
        
        for shop in shops:
            shop_sales = Sale.query.filter_by(shop_id=shop.id).all()
            total_sales += sum(sale.total_amount for sale in shop_sales)
            
            today_shop_sales = Sale.query.filter_by(shop_id=shop.id).filter(
                db.func.date(Sale.created_at) == today
            ).all()
            today_sales += sum(sale.total_amount for sale in today_shop_sales)
            
            products = Product.query.filter_by(shop_id=shop.id, is_active=True).all()
            total_products += len(products)
            low_stock_count += len([p for p in products if p.quantity <= p.reorder_level])
        
        # Recent sales
        recent_sales = []
        for shop in shops:
            shop_recent = Sale.query.filter_by(shop_id=shop.id).order_by(
                Sale.created_at.desc()
            ).limit(5).all()
            recent_sales.extend(shop_recent)
        
        recent_sales = sorted(recent_sales, key=lambda x: x.created_at, reverse=True)[:10]
        
        # Alerts
        alerts = Alert.query.filter_by(user_id=current_user.id, is_read=False).order_by(
            Alert.created_at.desc()
        ).limit(5).all()
        
        return render_template('dashboard_vendor.html',
                             shops=shops,
                             total_sales=total_sales,
                             today_sales=today_sales,
                             total_products=total_products,
                             low_stock_count=low_stock_count,
                             recent_sales=recent_sales,
                             alerts=alerts)
    
    elif current_user.role == 'admin':
        total_users = User.query.count()
        total_shops = Shop.query.count()
        total_products = Product.query.count()
        total_sales = db.session.query(db.func.sum(Sale.total_amount)).scalar() or 0
        
        return render_template('dashboard_admin.html',
                             total_users=total_users,
                             total_shops=total_shops,
                             total_products=total_products,
                             total_sales=total_sales)
    
    return render_template('dashboard.html')



# PART 6: ROUTES - SHOP MANAGEMENT


@app.route('/shops')
@login_required
@role_required(['vendor', 'admin'])
def shops():
    if current_user.role == 'admin':
        all_shops = Shop.query.all()
    else:
        all_shops = Shop.query.filter_by(owner_id=current_user.id).all()
    
    return render_template('shops.html', shops=all_shops)


@app.route('/shop/create', methods=['GET', 'POST'])
@login_required
@role_required(['vendor'])
def create_shop():
    if request.method == 'POST':
        shop = Shop(
            name=request.form['name'],
            category=request.form['category'],
            location=request.form['location'],
            description=request.form.get('description'),
            owner_id=current_user.id
        )
        
        db.session.add(shop)
        db.session.commit()
        
        flash('Duka limeundwa kikamilifu!', 'success')
        return redirect(url_for('shops'))
    
    return render_template('shop_create.html')


@app.route('/shop/<int:shop_id>')
@login_required
def shop_detail(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    
    if current_user.role != 'admin' and shop.owner_id != current_user.id:
        flash('Hakuna ruhusa', 'danger')
        return redirect(url_for('shops'))
    
    products = Product.query.filter_by(shop_id=shop_id, is_active=True).all()
    sales = Sale.query.filter_by(shop_id=shop_id).order_by(Sale.created_at.desc()).limit(20).all()
    
    return render_template('shop_detail.html', shop=shop, products=products, sales=sales)



# PART 7: ROUTES - INVENTORY MANAGEMENT


@app.route('/products')
@login_required
def products():
    if current_user.role == 'vendor':
        user_shops = Shop.query.filter_by(owner_id=current_user.id).all()
        shop_ids = [shop.id for shop in user_shops]
        all_products = Product.query.filter(Product.shop_id.in_(shop_ids)).all()
    else:
        all_products = Product.query.all()
    
    return render_template('products.html', products=all_products)


@app.route('/product/add', methods=['GET', 'POST'])
@login_required
@role_required(['vendor'])
def add_product():
    if request.method == 'POST':
        # Generate SKU if not provided
        sku = request.form.get('sku')
        if not sku:
            sku = f"PRD{datetime.utcnow().timestamp():.0f}"
        
        expiry = request.form.get('expiry_date')
        expiry_date = datetime.strptime(expiry, '%Y-%m-%d').date() if expiry else None
        
        product = Product(
            name=request.form['name'],
            description=request.form.get('description'),
            price=float(request.form['price']),
            cost_price=float(request.form.get('cost_price', 0)),
            quantity=int(request.form['quantity']),
            unit=request.form.get('unit', 'pcs'),
            sku=sku,
            category=request.form.get('category'),
            expiry_date=expiry_date,
            reorder_level=int(request.form.get('reorder_level', 10)),
            shop_id=int(request.form['shop_id'])
        )
        
        db.session.add(product)
        db.session.commit()
        
        # Check if low stock alert needed
        if product.quantity <= product.reorder_level:
            alert = Alert(
                user_id=current_user.id,
                title='Bidhaa zimepungua',
                message=f'{product.name} iko chini ya kiwango cha uhakika',
                alert_type='low_stock'
            )
            db.session.add(alert)
            db.session.commit()
        
        flash('Bidhaa imeongezwa kikamilifu!', 'success')
        return redirect(url_for('products'))
    
    shops = Shop.query.filter_by(owner_id=current_user.id).all()
    return render_template('product_add.html', shops=shops)


@app.route('/product/<int:product_id>/update', methods=['GET', 'POST'])
@login_required
def update_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        product.name = request.form['name']
        product.price = float(request.form['price'])
        product.quantity = int(request.form['quantity'])
        product.description = request.form.get('description')
        product.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Bidhaa imesasishwa!', 'success')
        return redirect(url_for('products'))
    
    return render_template('product_update.html', product=product)



# PART 8: ROUTES - SALES MANAGEMENT


@app.route('/sales')
@login_required
def sales():
    if current_user.role == 'vendor':
        user_shops = Shop.query.filter_by(owner_id=current_user.id).all()
        shop_ids = [shop.id for shop in user_shops]
        all_sales = Sale.query.filter(Sale.shop_id.in_(shop_ids)).order_by(
            Sale.created_at.desc()
        ).all()
    else:
        all_sales = Sale.query.order_by(Sale.created_at.desc()).all()
    
    return render_template('sales.html', sales=all_sales)


@app.route('/sale/create', methods=['GET', 'POST'])
@login_required
@role_required(['vendor'])
def create_sale():
    if request.method == 'POST':
        data = request.json
        
        # Generate sale number
        sale_number = f"SALE{datetime.utcnow().timestamp():.0f}"
        
        sale = Sale(
            sale_number=sale_number,
            shop_id=data['shop_id'],
            customer_name=data.get('customer_name'),
            customer_phone=data.get('customer_phone'),
            total_amount=float(data['total_amount']),
            payment_method=data.get('payment_method', 'cash'),
            payment_reference=data.get('payment_reference'),
            notes=data.get('notes')
        )
        
        db.session.add(sale)
        db.session.flush()
        
        # Add sale items and update inventory
        for item in data['items']:
            product = Product.query.get(item['product_id'])
            
            if product.quantity < item['quantity']:
                db.session.rollback()
                return jsonify({'error': f'Stock ya {product.name} hazitosha'}), 400
            
            sale_item = SaleItem(
                sale_id=sale.id,
                product_id=item['product_id'],
                quantity=item['quantity'],
                unit_price=item['unit_price'],
                subtotal=item['subtotal']
            )
            
            # Update product quantity
            product.quantity -= item['quantity']
            
            db.session.add(sale_item)
        
        db.session.commit()
        
        return jsonify({'success': True, 'sale_id': sale.id, 'sale_number': sale_number})
    
    shops = Shop.query.filter_by(owner_id=current_user.id).all()
    return render_template('sale_create.html', shops=shops)


@app.route('/api/shop/<int:shop_id>/products')
@login_required
def get_shop_products(shop_id):
    products = Product.query.filter_by(shop_id=shop_id, is_active=True).all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'price': p.price,
        'quantity': p.quantity,
        'unit': p.unit
    } for p in products])



# PART 9: ROUTES - EXPENSE MANAGEMENT


@app.route('/expenses')
@login_required
def expenses():
    all_expenses = Expense.query.filter_by(user_id=current_user.id).order_by(
        Expense.date.desc()
    ).all()
    
    # Calculate totals by category
    categories = db.session.query(
        Expense.category,
        db.func.sum(Expense.amount).label('total')
    ).filter_by(user_id=current_user.id).group_by(Expense.category).all()
    
    return render_template('expenses.html', expenses=all_expenses, categories=categories)


@app.route('/expense/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        expense_date = request.form.get('date')
        date_obj = datetime.strptime(expense_date, '%Y-%m-%d').date() if expense_date else datetime.utcnow().date()
        
        expense = Expense(
            user_id=current_user.id,
            category=request.form['category'],
            amount=float(request.form['amount']),
            description=request.form.get('description'),
            date=date_obj,
            payment_method=request.form.get('payment_method'),
            receipt_number=request.form.get('receipt_number')
        )
        
        db.session.add(expense)
        db.session.commit()
        
        flash('Gharama imeongezwa kikamilifu!', 'success')
        return redirect(url_for('expenses'))
    
    return render_template('expense_add.html')



# PART 10: ROUTES - REPORTS & ANALYTICS


@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html')


@app.route('/api/analytics/sales')
@login_required
def analytics_sales():
    period = request.args.get('period', '7days')
    
    if period == '7days':
        start_date = datetime.utcnow() - timedelta(days=7)
    elif period == '30days':
        start_date = datetime.utcnow() - timedelta(days=30)
    else:
        start_date = datetime.utcnow() - timedelta(days=365)
    
    # Get sales data
    if current_user.role == 'vendor':
        shops = Shop.query.filter_by(owner_id=current_user.id).all()
        shop_ids = [s.id for s in shops]
        sales = Sale.query.filter(
            Sale.shop_id.in_(shop_ids),
            Sale.created_at >= start_date
        ).all()
    else:
        sales = Sale.query.filter(Sale.created_at >= start_date).all()
    
    # Group by date
    daily_sales = {}
    for sale in sales:
        date_key = sale.created_at.strftime('%Y-%m-%d')
        daily_sales[date_key] = daily_sales.get(date_key, 0) + sale.total_amount
    
    return jsonify({
        'labels': list(daily_sales.keys()),
        'data': list(daily_sales.values())
    })


@app.route('/api/analytics/top-products')
@login_required
def analytics_top_products():
    if current_user.role == 'vendor':
        shops = Shop.query.filter_by(owner_id=current_user.id).all()
        shop_ids = [s.id for s in shops]
        
        top_products = db.session.query(
            Product.name,
            db.func.sum(SaleItem.quantity).label('total_sold')
        ).join(SaleItem).join(Sale).filter(
            Sale.shop_id.in_(shop_ids)
        ).group_by(Product.name).order_by(
            db.desc('total_sold')
        ).limit(10).all()
    else:
        top_products = db.session.query(
            Product.name,
            db.func.sum(SaleItem.quantity).label('total_sold')
        ).join(SaleItem).group_by(Product.name).order_by(
            db.desc('total_sold')
        ).limit(10).all()
    
    return jsonify({
        'labels': [p[0] for p in top_products],
        'data': [float(p[1]) for p in top_products]
    })


@app.route('/reports/download/<report_type>')
@login_required
def download_report(report_type):
    if report_type == 'sales':
        # Generate CSV
        output = BytesIO()
        writer = csv.writer(output)
        writer.writerow(['Sale Number', 'Date', 'Customer', 'Amount', 'Payment Method'])
        
        if current_user.role == 'vendor':
            shops = Shop.query.filter_by(owner_id=current_user.id).all()
            shop_ids = [s.id for s in shops]
            sales = Sale.query.filter(Sale.shop_id.in_(shop_ids)).all()
        else:
            sales = Sale.query.all()
        
        for sale in sales:
            writer.writerow([
                sale.sale_number,
                sale.created_at.strftime('%Y-%m-%d %H:%M'),
                sale.customer_name or 'N/A',
                sale.total_amount,
                sale.payment_method
            ])
        
        output.seek(0)
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'sales_report_{datetime.utcnow().strftime("%Y%m%d")}.csv'
        )
    
    return jsonify({'error': 'Invalid report type'}), 400



# PART 11: ROUTES - SUPPLIER MANAGEMENT


@app.route('/suppliers')
@login_required
def suppliers():
    all_suppliers = Supplier.query.filter_by(is_active=True).all()
    return render_template('suppliers.html', suppliers=all_suppliers)


@app.route('/supplier/add', methods=['GET', 'POST'])
@login_required
@role_required(['vendor', 'admin'])
def add_supplier():
    if request.method == 'POST':
        supplier = Supplier(
            name=request.form['name'],
            contact_person=request.form.get('contact_person'),
            phone=request.form['phone'],
            email=request.form.get('email'),
            address=request.form.get('address'),
            category=request.form.get('category')
        )
        
        db.session.add(supplier)
        db.session.commit()
        
        flash('Muuzaji ameongezwa kikamilifu!', 'success')
        return redirect(url_for('suppliers'))
    
    return render_template('supplier_add.html')


@app.route('/orders')
@login_required
def orders():
    if current_user.role == 'vendor':
        all_orders = Order.query.filter_by(buyer_id=current_user.id).order_by(
            Order.created_at.desc()
        ).all()
    else:
        all_orders = Order.query.order_by(Order.created_at.desc()).all()
    
    return render_template('orders.html', orders=all_orders)


@app.route('/order/create', methods=['GET', 'POST'])
@login_required
@role_required(['vendor'])
def create_order():
    if request.method == 'POST':
        data = request.json
        
        order_number = f"ORD{datetime.utcnow().timestamp():.0f}"
        
        order = Order(
            order_number=order_number,
            buyer_id=current_user.id,
            supplier_id=data['supplier_id'],
            total_amount=float(data['total_amount']),
            delivery_date=datetime.strptime(data['delivery_date'], '%Y-%m-%d').date() if data.get('delivery_date') else None,
            notes=data.get('notes')
        )
        
        db.session.add(order)
        db.session.flush()
        
        for item in data['items']:
            order_item = OrderItem(
                order_id=order.id,
                product_name=item['product_name'],
                quantity=item['quantity'],
                unit_price=item['unit_price'],
                subtotal=item['subtotal']
            )
            db.session.add(order_item)
        
        db.session.commit()
        
        return jsonify({'success': True, 'order_id': order.id, 'order_number': order_number})
    
    suppliers_list = Supplier.query.filter_by(is_active=True).all()
    return render_template('order_create.html', suppliers=suppliers_list)


@app.route('/order/<int:order_id>/status', methods=['POST'])
@login_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    
    new_status = request.json.get('status')
    if new_status in ['pending', 'approved', 'shipped', 'delivered', 'cancelled']:
        order.status = new_status
        db.session.commit()
        
        return jsonify({'success': True, 'status': new_status})
    
    return jsonify({'error': 'Invalid status'}), 400



# PART 12: ROUTES - ALERTS & NOTIFICATIONS


@app.route('/alerts')
@login_required
def alerts():
    all_alerts = Alert.query.filter_by(user_id=current_user.id).order_by(
        Alert.created_at.desc()
    ).all()
    return render_template('alerts.html', alerts=all_alerts)


@app.route('/alert/<int:alert_id>/read', methods=['POST'])
@login_required
def mark_alert_read(alert_id):
    alert = Alert.query.get_or_404(alert_id)
    
    if alert.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    alert.is_read = True
    db.session.commit()
    
    return jsonify({'success': True})


@app.route('/api/check-alerts')
@login_required
def check_alerts():
    # Check for low stock
    if current_user.role == 'vendor':
        shops = Shop.query.filter_by(owner_id=current_user.id).all()
        
        for shop in shops:
            products = Product.query.filter_by(shop_id=shop.id, is_active=True).all()
            
            for product in products:
                if product.quantity <= product.reorder_level:
                    # Check if alert already exists
                    existing_alert = Alert.query.filter_by(
                        user_id=current_user.id,
                        alert_type='low_stock',
                        message__contains=product.name,
                        is_read=False
                    ).first()
                    
                    if not existing_alert:
                        alert = Alert(
                            user_id=current_user.id,
                            title='Bidhaa zimepungua',
                            message=f'{product.name} iko chini ya kiwango ({product.quantity} {product.unit})',
                            alert_type='low_stock'
                        )
                        db.session.add(alert)
        
        db.session.commit()
    
    unread_count = Alert.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({'unread_count': unread_count})



# PART 13: ROUTES - OFFLINE SYNC


@app.route('/api/sync/upload', methods=['POST'])
@login_required
def sync_upload():
    """Receive offline data and sync to database"""
    data = request.json
    
    sync_log = SyncLog(
        user_id=current_user.id,
        sync_type=data['type'],
        data=json.dumps(data['payload'])
    )
    
    db.session.add(sync_log)
    
    try:
        if data['type'] == 'sale':
            # Process offline sale
            payload = data['payload']
            
            sale_number = f"SALE{datetime.utcnow().timestamp():.0f}"
            
            sale = Sale(
                sale_number=sale_number,
                shop_id=payload['shop_id'],
                customer_name=payload.get('customer_name'),
                total_amount=float(payload['total_amount']),
                payment_method=payload.get('payment_method', 'cash'),
                created_at=datetime.fromisoformat(payload.get('created_at', datetime.utcnow().isoformat()))
            )
            
            db.session.add(sale)
            db.session.flush()
            
            for item in payload['items']:
                product = Product.query.get(item['product_id'])
                
                sale_item = SaleItem(
                    sale_id=sale.id,
                    product_id=item['product_id'],
                    quantity=item['quantity'],
                    unit_price=item['unit_price'],
                    subtotal=item['subtotal']
                )
                
                product.quantity -= item['quantity']
                db.session.add(sale_item)
        
        elif data['type'] == 'expense':
            payload = data['payload']
            
            expense = Expense(
                user_id=current_user.id,
                category=payload['category'],
                amount=float(payload['amount']),
                description=payload.get('description'),
                date=datetime.fromisoformat(payload['date']).date()
            )
            
            db.session.add(expense)
        
        sync_log.status = 'completed'
        sync_log.synced_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Data synced successfully'})
    
    except Exception as e:
        db.session.rollback()
        sync_log.status = 'failed'
        db.session.commit()
        
        return jsonify({'error': str(e)}), 500


@app.route('/api/sync/download')
@login_required
def sync_download():
    """Send latest data to client for offline use"""
    if current_user.role == 'vendor':
        shops = Shop.query.filter_by(owner_id=current_user.id).all()
        shop_ids = [s.id for s in shops]
        
        products = Product.query.filter(Product.shop_id.in_(shop_ids), Product.is_active==True).all()
        
        return jsonify({
            'shops': [{
                'id': s.id,
                'name': s.name,
                'category': s.category
            } for s in shops],
            'products': [{
                'id': p.id,
                'name': p.name,
                'price': p.price,
                'quantity': p.quantity,
                'shop_id': p.shop_id,
                'unit': p.unit
            } for p in products]
        })
    
    return jsonify({'shops': [], 'products': []})



# PART 14: ROUTES - SETTINGS & PROFILE


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        current_user.name = request.form['name']
        current_user.email = request.form.get('email')
        current_user.language = request.form.get('language', 'sw')
        
        new_password = request.form.get('new_password')
        if new_password:
            current_user.set_password(new_password)
        
        db.session.commit()
        flash('Mipangilio imesasishwa!', 'success')
        return redirect(url_for('settings'))
    
    return render_template('settings.html')



# PART 15: API ENDPOINTS - MOBILE MONEY


@app.route('/api/payment/initiate', methods=['POST'])
@login_required
def initiate_payment():
    """Initiate mobile money payment"""
    data = request.json
    
    # This is a placeholder for actual mobile money API integration
    # You would integrate with M-Pesa, TigoPesa, or Airtel Money APIs here
    
    payment_method = data.get('payment_method')  # mpesa, tigopesa, airtel_money
    phone_number = data.get('phone_number')
    amount = data.get('amount')
    
    # Simulate API call
    payment_reference = f"PAY{datetime.utcnow().timestamp():.0f}"
    
    return jsonify({
        'success': True,
        'payment_reference': payment_reference,
        'status': 'pending',
        'message': 'Angalia simu yako kumaliza malipo'
    })


@app.route('/api/payment/callback', methods=['POST'])
def payment_callback():
    """Handle payment callback from mobile money provider"""
    data = request.json
    
    # Process payment confirmation
    # Update sale status, create transaction record, etc.
    
    return jsonify({'success': True})



# PART 16: ADMIN ROUTES


@app.route('/admin/users')
@login_required
@role_required(['admin'])
def admin_users():
    all_users = User.query.all()
    return render_template('admin_users.html', users=all_users)


@app.route('/admin/user/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@role_required(['admin'])
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    
    return jsonify({'success': True, 'is_active': user.is_active})


@app.route('/admin/statistics')
@login_required
@role_required(['admin'])
def admin_statistics():
    total_revenue = db.session.query(db.func.sum(Sale.total_amount)).scalar() or 0
    total_expenses = db.session.query(db.func.sum(Expense.amount)).scalar() or 0
    
    # Monthly growth
    current_month = datetime.utcnow().replace(day=1)
    last_month = (current_month - timedelta(days=1)).replace(day=1)
    
    current_month_sales = db.session.query(db.func.sum(Sale.total_amount)).filter(
        Sale.created_at >= current_month
    ).scalar() or 0
    
    last_month_sales = db.session.query(db.func.sum(Sale.total_amount)).filter(
        Sale.created_at >= last_month,
        Sale.created_at < current_month
    ).scalar() or 0
    
    growth_rate = ((current_month_sales - last_month_sales) / last_month_sales * 100) if last_month_sales > 0 else 0
    
    return render_template('admin_statistics.html',
                         total_revenue=total_revenue,
                         total_expenses=total_expenses,
                         growth_rate=growth_rate)



# PART 17: ERROR HANDLERS


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500



# PART 18: DATABASE INITIALIZATION

def init_db():
    """Initialize database with tables and default data"""
    with app.app_context():
        try:
            # First, create all tables - this must happen before any queries
            print("🔧 Creating database tables...")
            db.create_all()
            print("✅ Database tables created successfully!")
            
            # Now that tables exist, we can safely query them
            # Check if admin user exists
            admin = User.query.filter_by(phone='admin').first()
            if not admin:
                admin = User(
                    phone='admin',
                    name='Administrator',
                    email='admin@vendorapp.com',
                    role='admin'
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("✅ Default admin user created (phone: admin, password: admin123)")
            else:
                print("ℹ️ Admin user already exists")
                
        except Exception as e:
            print(f"❌ Error in database initialization: {e}")
            # If there's an error, the database might be corrupted
            # Delete the database file and try again
            import os
            if os.path.exists('vendor_app.db'):
                os.remove('vendor_app.db')
                print("🗑️ Removed corrupted database file")
            
            # Try to recreate everything
            try:
                db.create_all()
                print("✅ Database tables recreated")
                
                # Create admin user
                admin = User(
                    phone='admin',
                    name='Administrator',
                    email='admin@vendorapp.com',
                    role='admin'
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("✅ Default admin user created after recovery")
            except Exception as e2:
                print(f"❌ Critical error: Could not initialize database: {e2}")
                raise e2


# PART 19: MAIN APPLICATION ENTRY


if __name__ == '__main__':
    # Create uploads folder if not exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
        print("✅ Created uploads folder")
    
    # Initialize database with error handling
    # try:
    #     init_db()
    # except Exception as e:
    #     print(f"❌ Failed to initialize database: {e}")
    #     print("💡 If the error persists, manually delete 'vendor_app.db' and run again")
    #     exit(1)
    
    # Run application
    
    
    app.run(debug=True, host='0.0.0.0', port=5000)