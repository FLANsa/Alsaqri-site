#!/usr/bin/env python3
"""
Alsaqri Phone Shop Management System
A simple Flask application for managing phone inventory and sales
"""

import os
import sqlite3
import argparse
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont
import io
import base64
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
import tempfile

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///phone_shop.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Phone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    barcode = db.Column(db.String(50), unique=True, nullable=False)
    brand = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(30), nullable=False)
    storage = db.Column(db.String(20), nullable=False)
    condition = db.Column(db.String(20), nullable=False)  # new, used
    price = db.Column(db.Float, nullable=False)
    cost = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, default=1)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)

class Accessory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    cost = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, default=1)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_date = db.Column(db.DateTime, default=datetime.utcnow)
    customer_name = db.Column(db.String(100))
    customer_phone = db.Column(db.String(20))
    total_amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(20), default='cash')
    items = db.relationship('SaleItem', backref='sale', lazy=True, cascade='all, delete-orphan')

class SaleItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=False)
    item_type = db.Column(db.String(20), nullable=False)  # phone or accessory
    item_id = db.Column(db.Integer, nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.Float, nullable=False)
    cost = db.Column(db.Float, nullable=False)

class AccessoryCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    arabic_name = db.Column(db.String(50), nullable=False)

class PhoneType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    arabic_name = db.Column(db.String(50), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def create_admin_user():
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            password=generate_password_hash('admin123'),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully!")

# Routes
@app.route('/')
def index():
    try:
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return render_template('index.html')
    except Exception as e:
        return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    phones = Phone.query.all()
    accessories = Accessory.query.all()
    recent_sales = Sale.query.order_by(Sale.sale_date.desc()).limit(5).all()
    
    # Calculate statistics
    total_phones = sum(phone.quantity for phone in phones)
    total_accessories = sum(accessory.quantity for accessory in accessories)
    total_sales = Sale.query.count()
    
    return render_template('dashboard.html', 
                         phones=phones, 
                         accessories=accessories,
                         recent_sales=recent_sales,
                         total_phones=total_phones,
                         total_accessories=total_accessories,
                         total_sales=total_sales)

@app.route('/add_new_phone', methods=['GET', 'POST'])
@login_required
def add_new_phone():
    if request.method == 'POST':
        try:
            # Generate barcode
            last_phone = Phone.query.order_by(Phone.id.desc()).first()
            if last_phone:
                last_barcode = int(last_phone.barcode)
                new_barcode = str(last_barcode + 1).zfill(6)
            else:
                new_barcode = '000001'
            
            phone = Phone(
                barcode=new_barcode,
                brand=request.form['brand'],
                model=request.form['model'],
                color=request.form['color'],
                storage=request.form['storage'],
                condition='new',
                price=float(request.form['price']),
                cost=float(request.form['cost']),
                quantity=int(request.form['quantity']),
                notes=request.form.get('notes', '')
            )
            
            db.session.add(phone)
            db.session.commit()
            
            flash(f'تم إضافة الهاتف بنجاح! الباركود: {new_barcode}', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            flash(f'حدث خطأ: {str(e)}', 'error')
            db.session.rollback()
    
    return render_template('add_new_phone.html')

@app.route('/add_used_phone', methods=['GET', 'POST'])
@login_required
def add_used_phone():
    if request.method == 'POST':
        try:
            # Generate barcode
            last_phone = Phone.query.order_by(Phone.id.desc()).first()
            if last_phone:
                last_barcode = int(last_phone.barcode)
                new_barcode = str(last_barcode + 1).zfill(6)
            else:
                new_barcode = '000001'
            
            phone = Phone(
                barcode=new_barcode,
                brand=request.form['brand'],
                model=request.form['model'],
                color=request.form['color'],
                storage=request.form['storage'],
                condition='used',
                price=float(request.form['price']),
                cost=float(request.form['cost']),
                quantity=int(request.form['quantity']),
                notes=request.form.get('notes', '')
            )
            
            db.session.add(phone)
            db.session.commit()
            
            flash(f'تم إضافة الهاتف المستعمل بنجاح! الباركود: {new_barcode}', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            flash(f'حدث خطأ: {str(e)}', 'error')
            db.session.rollback()
    
    return render_template('add_used_phone.html')

@app.route('/add_accessory', methods=['GET', 'POST'])
@login_required
def add_accessory():
    if request.method == 'POST':
        try:
            accessory = Accessory(
                name=request.form['name'],
                category=request.form['category'],
                price=float(request.form['price']),
                cost=float(request.form['cost']),
                quantity=int(request.form['quantity']),
                notes=request.form.get('notes', '')
            )
            
            db.session.add(accessory)
            db.session.commit()
            
            flash('تم إضافة الأكسسوار بنجاح!', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            flash(f'حدث خطأ: {str(e)}', 'error')
            db.session.rollback()
    
    return render_template('add_accessory.html')

@app.route('/search')
@login_required
def search():
    search_term = request.args.get('search_term', '')
    search_type = request.args.get('search_type', 'all')
    
    results = []
    if search_term:
        if search_type == 'phones' or search_type == 'all':
            phones = Phone.query.filter(
                (Phone.barcode.contains(search_term)) |
                (Phone.brand.contains(search_term)) |
                (Phone.model.contains(search_term))
            ).all()
            results.extend(phones)
        
        if search_type == 'accessories' or search_type == 'all':
            accessories = Accessory.query.filter(
                (Accessory.name.contains(search_term)) |
                (Accessory.category.contains(search_term))
            ).all()
            results.extend(accessories)
    
    return render_template('search.html', results=results, search_term=search_term, search_type=search_type)

@app.route('/create_sale', methods=['GET', 'POST'])
@login_required
def create_sale():
    if request.method == 'POST':
        try:
            # Create sale
            sale = Sale(
                customer_name=request.form.get('customer_name', ''),
                customer_phone=request.form.get('customer_phone', ''),
                total_amount=float(request.form['total_amount']),
                payment_method=request.form.get('payment_method', 'cash')
            )
            db.session.add(sale)
            db.session.flush()  # Get the sale ID
            
            # Add sale items
            items_data = request.form.getlist('items[]')
            for item_data in items_data:
                if item_data:
                    item_type, item_id, quantity, price, cost = item_data.split('|')
                    sale_item = SaleItem(
                        sale_id=sale.id,
                        item_type=item_type,
                        item_id=int(item_id),
                        item_name=request.form.get(f'item_name_{item_id}', ''),
                        quantity=int(quantity),
                        price=float(price),
                        cost=float(cost)
                    )
                    db.session.add(sale_item)
                    
                    # Update inventory
                    if item_type == 'phone':
                        phone = Phone.query.get(int(item_id))
                        if phone:
                            phone.quantity -= int(quantity)
                    elif item_type == 'accessory':
                        accessory = Accessory.query.get(int(item_id))
                        if accessory:
                            accessory.quantity -= int(quantity)
            
            db.session.commit()
            flash('تم إنشاء عملية البيع بنجاح!', 'success')
            return redirect(url_for('view_sale', sale_id=sale.id))
            
        except Exception as e:
            flash(f'حدث خطأ: {str(e)}', 'error')
            db.session.rollback()
    
    phones = Phone.query.filter(Phone.quantity > 0).all()
    accessories = Accessory.query.filter(Accessory.quantity > 0).all()
    return render_template('create_sale.html', phones=phones, accessories=accessories)

@app.route('/view_sale/<int:sale_id>')
@login_required
def view_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    return render_template('view_sale.html', sale=sale)

@app.route('/list_sales')
@login_required
def list_sales():
    sales = Sale.query.order_by(Sale.sale_date.desc()).all()
    return render_template('list_sales.html', sales=sales)

@app.route('/inventory_summary')
@login_required
def inventory_summary():
    phones = Phone.query.all()
    accessories = Accessory.query.all()
    
    # Calculate totals
    total_phone_value = sum(phone.price * phone.quantity for phone in phones)
    total_accessory_value = sum(accessory.price * accessory.quantity for accessory in accessories)
    total_cost = sum(phone.cost * phone.quantity for phone in phones) + sum(accessory.cost * accessory.quantity for accessory in accessories)
    
    return render_template('inventory_summary.html', 
                         phones=phones, 
                         accessories=accessories,
                         total_phone_value=total_phone_value,
                         total_accessory_value=total_accessory_value,
                         total_cost=total_cost)

@app.route('/print_barcode/<barcode>')
@login_required
def print_barcode(barcode):
    try:
        # Find the item
        phone = Phone.query.filter_by(barcode=barcode).first()
        if not phone:
            flash('الهاتف غير موجود', 'error')
            return redirect(url_for('search'))
        
        # Generate barcode image
        barcode_class = barcode.get_barcode_class('code128')
        barcode_instance = barcode_class(barcode, writer=ImageWriter())
        
        # Create barcode image
        barcode_image = barcode_instance.render()
        
        # Create sticker image
        sticker_width = 400
        sticker_height = 200
        sticker = Image.new('RGB', (sticker_width, sticker_height), 'white')
        draw = ImageDraw.Draw(sticker)
        
        # Try to load Arabic font
        try:
            font_path = '/System/Library/Fonts/Arial.ttf'
            if os.path.exists(font_path):
                company_font = ImageFont.truetype(font_path, 24)
                detail_font = ImageFont.truetype(font_path, 12)
            else:
                company_font = ImageFont.load_default()
                detail_font = ImageFont.load_default()
        except:
            company_font = ImageFont.load_default()
            detail_font = ImageFont.load_default()
        
        # Add company name
        company_text = "الصقري للإتصالات"
        company_bbox = draw.textbbox((0, 0), company_text, font=company_font)
        company_width = company_bbox[2] - company_bbox[0]
        company_x = (sticker_width - company_width) // 2
        draw.text((company_x, 10), company_text, fill='black', font=company_font)
        
        # Resize and add barcode
        barcode_image = barcode_image.resize((300, 80))
        sticker.paste(barcode_image, (50, 50))
        
        # Add details
        details = [
            f"الذاكرة: {phone.storage}",
            f"نسبة البطارية: 100%",
            f"رقم الجهاز: {phone.barcode}"
        ]
        
        y_position = 140
        for detail in details:
            detail_bbox = draw.textbbox((0, 0), detail, font=detail_font)
            detail_width = detail_bbox[2] - detail_bbox[0]
            detail_x = (sticker_width - detail_width) // 2
            draw.text((detail_x, y_position), detail, fill='black', font=detail_font)
            y_position += 15
        
        # Save to static folder
        static_folder = os.path.join(app.root_path, 'static', 'barcodes')
        os.makedirs(static_folder, exist_ok=True)
        barcode_path = os.path.join(static_folder, f'{barcode}.png')
        sticker.save(barcode_path)
        
        return render_template('print_barcode.html', barcode=barcode, phone=phone)
        
    except Exception as e:
        flash(f'حدث خطأ في إنشاء الباركود: {str(e)}', 'error')
        return redirect(url_for('search'))

@app.route('/health')
def health_check():
    """Health check endpoint for online deployment"""
    try:
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'message': 'Application is running successfully'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'error',
            'error': str(e)
        }), 500

@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors gracefully"""
    db.session.rollback()
    return render_template('error.html', error="Database error. Please try again."), 500

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return render_template('error.html', error="Page not found."), 404

@app.route('/favicon.ico')
def favicon():
    static_favicon = os.path.join(app.root_path, 'static', 'favicon.ico')
    if os.path.exists(static_favicon):
        return send_file(static_favicon)
    return ("", 204)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables if they do not exist
        create_admin_user()  # Create admin user on startup if missing
    
    # Check if running in production
    if os.environ.get('PORT'):
        # Production deployment
        port = int(os.environ.get('PORT'))
        app.run(debug=False, host='0.0.0.0', port=port)
    else:
        # Development
        parser = argparse.ArgumentParser()
        parser.add_argument('--port', type=int, default=5001)
        args = parser.parse_args()
        app.run(debug=True, port=args.port) 