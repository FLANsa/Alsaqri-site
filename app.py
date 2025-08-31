from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import os
from sqlalchemy import func
import random
import barcode
from barcode.writer import ImageWriter
from PIL import Image
import argparse
from werkzeug.security import generate_password_hash, check_password_hash
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4
from io import BytesIO
import arabic_reshaper
from bidi.algorithm import get_display

# VAT Configuration for Saudi Arabia
VAT_RATE = 0.15  # 15% VAT rate

def calculate_vat(amount):
    """Calculate VAT amount for a given price"""
    return amount * VAT_RATE

def calculate_price_with_vat(price_without_vat):
    """Calculate price including VAT"""
    return price_without_vat * (1 + VAT_RATE)

def calculate_price_without_vat(price_with_vat):
    """Calculate price excluding VAT"""
    return price_with_vat / (1 + VAT_RATE)

def generate_invoice_number():
    """Generate unique invoice number"""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = random.randint(1000, 9999)
    return f"INV-{timestamp}-{random_suffix}"



app = Flask(__name__)

# Production configuration
if os.environ.get('DATABASE_URL'):
    # For production (Render, Railway, Heroku)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
else:
    # For development
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///phone_shop.db'
    app.config['SECRET_KEY'] = 'your-secret-key-here'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'



# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Phone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(100), nullable=False)
    condition = db.Column(db.String(20), nullable=False)  # new or used
    purchase_price = db.Column(db.Float, nullable=False)  # سعر الشراء (بدون ضريبة)
    selling_price = db.Column(db.Float, nullable=False)   # سعر البيع (بدون ضريبة)
    purchase_price_with_vat = db.Column(db.Float, nullable=False)  # سعر الشراء (مع ضريبة)
    selling_price_with_vat = db.Column(db.Float, nullable=False)   # سعر البيع (مع ضريبة)
    serial_number = db.Column(db.String(100), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)  # New field for phone number
    barcode_path = db.Column(db.String(200))  # New field for barcode image path
    description = db.Column(db.Text)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    warranty = db.Column(db.Integer)
    phone_condition = db.Column(db.String(20))
    age = db.Column(db.Integer)
    
    # Customer information fields
    customer_name = db.Column(db.String(100))  # اسم العميل
    customer_phone = db.Column(db.String(20))  # رقم هاتف العميل
    customer_id = db.Column(db.String(50))     # رقم الهوية / الإقامة
    phone_color = db.Column(db.String(50))     # لون الجوال
    phone_memory = db.Column(db.String(50))    # الذاكرة
    buyer_name = db.Column(db.String(100))     # اسم المشتري

class PhoneType(db.Model):
    """نموذج أنواع الهواتف - للتحكم في العلامات التجارية والموديلات"""
    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), default='smartphone')  # smartphone, tablet, etc.
    release_year = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)

# Transaction model removed - replaced by Sale and SaleItem models

class Transaction(db.Model):
    """نموذج المعاملات - للاحتفاظ بسجل المعاملات"""
    id = db.Column(db.Integer, primary_key=True)
    phone_id = db.Column(db.Integer, db.ForeignKey('phone.id'), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # buy, sell
    serial_number = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)  # السعر قبل الضريبة
    price_with_vat = db.Column(db.Float, nullable=False)  # السعر مع الضريبة
    vat_amount = db.Column(db.Float, nullable=False)  # مبلغ الضريبة
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    customer_name = db.Column(db.String(100))
    customer_phone = db.Column(db.String(20))
    notes = db.Column(db.Text)

class Sale(db.Model):
    """نموذج عملية البيع - يمكن أن تحتوي على عدة منتجات"""
    id = db.Column(db.Integer, primary_key=True)
    sale_number = db.Column(db.String(50), unique=True, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Company Information (معلومات الشركة)
    company_name = db.Column(db.String(200), nullable=False, default="شركة الهواتف الذكية")
    company_vat_number = db.Column(db.String(50), nullable=False, default="123456789012345")
    company_address = db.Column(db.Text, nullable=False, default="الرياض، المملكة العربية السعودية")
    company_phone = db.Column(db.String(20), nullable=False, default="+966-11-123-4567")
    
    # Customer Information (معلومات العميل)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20))
    customer_email = db.Column(db.String(100))
    customer_address = db.Column(db.Text)
    
    # Sale Details (تفاصيل البيع)
    subtotal = db.Column(db.Float, nullable=False, default=0.0)  # المبلغ قبل الضريبة
    vat_amount = db.Column(db.Float, nullable=False, default=0.0)  # مبلغ الضريبة
    total_amount = db.Column(db.Float, nullable=False, default=0.0)  # المبلغ الإجمالي
    payment_method = db.Column(db.String(50), default="نقدي")
    
    # Additional Fields
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default="مكتمل")  # مكتمل، ملغي، مرفوض
    
    # Relationships
    items = db.relationship('SaleItem', backref='sale', lazy=True, cascade='all, delete-orphan')

class AccessoryCategory(db.Model):
    """نموذج فئات الأكسسوارات - للتحكم في الفئات"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    arabic_name = db.Column(db.String(100), nullable=False)  # الاسم بالعربية
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)

class Accessory(db.Model):
    """نموذج الأكسسوارات والمستلزمات"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)  # accessory, charger, case, screen_protector
    description = db.Column(db.Text)
    purchase_price = db.Column(db.Float, nullable=False)  # سعر الشراء (بدون ضريبة)
    selling_price = db.Column(db.Float, nullable=False)   # سعر البيع (بدون ضريبة)
    purchase_price_with_vat = db.Column(db.Float, nullable=False)  # سعر الشراء (مع ضريبة)
    selling_price_with_vat = db.Column(db.Float, nullable=False)   # سعر البيع (مع ضريبة)
    quantity_in_stock = db.Column(db.Integer, nullable=False, default=0)
    min_quantity = db.Column(db.Integer, default=5)  # الحد الأدنى للمخزون
    supplier = db.Column(db.String(200))
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)

class SaleItem(db.Model):
    """نموذج عنصر البيع - كل منتج في عملية البيع"""
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=False)
    
    # Product Information (معلومات المنتج)
    product_type = db.Column(db.String(50), nullable=False)  # phone, accessory, charger, etc.
    product_name = db.Column(db.String(200), nullable=False)
    product_description = db.Column(db.Text)
    serial_number = db.Column(db.String(100))  # للهواتف فقط
    
    # Pricing (التسعير)
    unit_price = db.Column(db.Float, nullable=False)  # سعر الوحدة قبل الضريبة
    purchase_price = db.Column(db.Float, nullable=False, default=0.0)  # سعر الشراء قبل الضريبة
    quantity = db.Column(db.Integer, nullable=False, default=1)
    total_price = db.Column(db.Float, nullable=False)  # السعر الإجمالي للكمية
    
    # Additional Fields
    notes = db.Column(db.Text)

# Invoice model removed - invoices are now generated from Sale data



@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Database initialization functions
def create_admin_user():
    """Create admin user if it doesn't exist"""
    try:
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin', 
                password=generate_password_hash('admin123'), 
                is_admin=True,
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully!")
        else:
            print("Admin user already exists!")
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.session.rollback()

def initialize_database():
    """Initialize database with proper error handling"""
    try:
        # Check if tables exist by trying to query
        User.query.first()
        print("Database tables already exist!")
    except Exception:
        print("Creating database tables...")
        try:
            db.create_all()
            print("Database tables created successfully!")
        except Exception as e:
            print(f"Error creating tables: {e}")
            return False
    
    # Create admin user
    create_admin_user()
    return True

# Initialize database on app startup
with app.app_context():
    initialize_database()

# Create limited user if not exists




# Routes
@app.route('/')
def index():
    try:
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return render_template('index.html')
    except Exception as e:
        # If there's a database error, show a simple page
        return render_template('index.html')



@app.route('/health')
def health_check():
    """Health check endpoint for online deployment"""
    try:
        # Test database connection
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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user:
            # Backward-compatible check: if stored value looks hashed, verify hash; otherwise compare plaintext
            is_hashed = user.password.startswith('pbkdf2:') or user.password.startswith('scrypt:') or user.password.startswith('argon2:')
            if (is_hashed and check_password_hash(user.password, password)) or (not is_hashed and user.password == password):
                # If old plaintext password, upgrade it to hashed transparently
                if not is_hashed:
                    user.password = generate_password_hash(password)
                    db.session.commit()
                login_user(user)
                return redirect(url_for('dashboard'))
        flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    phones = Phone.query.all()
    accessories = Accessory.query.all()
    
    # Calculate financial summaries for current inventory (phones + accessories)
    total_phones = len(phones)
    total_accessories = sum(acc.quantity_in_stock for acc in accessories)
    total_items = total_phones + total_accessories
    
    # Phone values
    phone_purchase_value = sum(phone.purchase_price for phone in phones)
    phone_selling_value = sum(phone.selling_price for phone in phones)
    
    # Accessory values (considering quantity in stock)
    accessory_purchase_value = sum(acc.purchase_price_with_vat * acc.quantity_in_stock for acc in accessories)
    accessory_selling_value = sum(acc.selling_price_with_vat * acc.quantity_in_stock for acc in accessories)
    
    # Total values for all inventory
    total_purchase_value = phone_purchase_value + accessory_purchase_value
    total_selling_value = phone_selling_value + accessory_selling_value
    total_expected_profit = total_selling_value - total_purchase_value
    
    # Recent sales
    recent_sales = Sale.query.order_by(Sale.date_created.desc()).limit(10).all()
    
    # Sales statistics
    total_sales = Sale.query.count()
    total_sales_amount = sum(sale.total_amount for sale in Sale.query.all())
    
    # Calculate sales subtotal and VAT
    total_sales_subtotal = sum(sale.subtotal for sale in Sale.query.all())
    total_vat_amount = sum(sale.vat_amount for sale in Sale.query.all())
    
    # Calculate actual profit from completed sales
    total_actual_profit = 0.0
    all_sales = Sale.query.all()
    
    for sale in all_sales:
        for item in sale.items:
            # Calculate profit using stored purchase price
            selling_price_without_vat = item.unit_price / (1 + VAT_RATE)
            purchase_price_without_vat = item.purchase_price / (1 + VAT_RATE)
            profit = selling_price_without_vat - purchase_price_without_vat
            total_actual_profit += profit * item.quantity
    
    return render_template('dashboard.html', 
                         phones=phones,
                         accessories=accessories,
                         total_phones=total_phones,
                         total_accessories=total_accessories,
                         total_items=total_items,
                         phone_purchase_value=phone_purchase_value,
                         phone_selling_value=phone_selling_value,
                         accessory_purchase_value=accessory_purchase_value,
                         accessory_selling_value=accessory_selling_value,
                         total_purchase_value=total_purchase_value,
                         total_selling_value=total_selling_value,
                         total_expected_profit=total_expected_profit,
                         total_sales_count=total_sales,
                         total_sales_amount=total_sales_amount,
                         total_sales_subtotal=total_sales_subtotal,
                         total_vat_amount=total_vat_amount,
                         total_actual_profit=total_actual_profit,
                         recent_sales=recent_sales)

# Transactions route removed - replaced by sales system

def generate_barcode(phone_number, battery_age=None):
    """Generate barcode for phone with sticker design"""
    # Create barcode data with phone number and battery age
    barcode_data = phone_number
    if battery_age is not None:
        barcode_data += f"|B{battery_age:03d}"
    
    # Create barcode with enhanced data
    barcode_class = barcode.get_barcode_class('code128')
    barcode_instance = barcode_class(barcode_data, writer=ImageWriter())
    
    # Set custom options for the barcode (optimized for 2x5cm sticker)
    options = {
        'module_width': 0.2,   # Width of each bar
        'module_height': 8,    # Height of the barcode
        'font_size': 6,        # Font size for the number
        'text_distance': 0.5,  # Distance between barcode and text
        'quiet_zone': 0.5,     # Quiet zone around the barcode
        'dpi': 203            # DPI optimized for thermal printers
    }
    
    # Create barcodes directory if it doesn't exist
    if not os.path.exists('static/barcodes'):
        os.makedirs('static/barcodes')
    
    # Save barcode image with custom options
    filename = f"static/barcodes/{phone_number}"
    barcode_path = barcode_instance.save(filename, options)
    
    # Convert the saved image to sticker size (6cm x 3cm - compact layout)
    img = Image.open(barcode_path)
    # Convert cm to pixels (1cm = 37.795276 pixels at 96 DPI)
    width_px = int(6.0 * 37.795276)   # 6cm width
    height_px = int(3.0 * 37.795276)  # 3cm height
    img = img.resize((width_px, height_px), Image.Resampling.LANCZOS)
    img.save(barcode_path)
    
    return barcode_path

@app.route('/barcode/<phone_number>')
@login_required
def get_barcode(phone_number):
    phone = Phone.query.filter_by(phone_number=phone_number).first()
    if phone and phone.barcode_path:
        return send_file(phone.barcode_path, mimetype='image/png')
    return "Barcode not found", 404

@app.route('/print_barcode/<phone_number>')
@login_required
def print_barcode(phone_number):
    phone = Phone.query.filter_by(phone_number=phone_number).first()
    if not phone:
        flash('الهاتف غير موجود', 'error')
        return redirect(url_for('dashboard'))
    return render_template('print_barcode.html', phone=phone)

@app.route('/download_barcode_pdf/<phone_number>')
@login_required
def download_barcode_pdf(phone_number):
    """Download barcode as PDF with exact dimensions"""
    phone = Phone.query.filter_by(phone_number=phone_number).first()
    if not phone:
        flash('الهاتف غير موجود', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        # Create complete sticker image first
        def create_complete_sticker_image():
            from PIL import Image, ImageDraw, ImageFont
            
            # Create image with exact dimensions (6cm x 3cm at 300 DPI)
            width_px = int(6 * 118.11)  # 6cm at 300 DPI
            height_px = int(3 * 118.11)  # 3cm at 300 DPI
            
            # Create white background
            sticker_img = Image.new('RGB', (width_px, height_px), color='white')
            draw = ImageDraw.Draw(sticker_img)
            
            # Try to load Arabic font
            try:
                font_paths = [
                    '/System/Library/Fonts/Arial.ttf',
                    '/System/Library/Fonts/Helvetica.ttc',
                    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                    'C:/Windows/Fonts/arial.ttf',
                ]
                
                arabic_font = None
                for font_path in font_paths:
                    if os.path.exists(font_path):
                        arabic_font = ImageFont.truetype(font_path, 32)
                        break
                
                if arabic_font is None:
                    arabic_font = ImageFont.load_default()
                    
            except:
                arabic_font = ImageFont.load_default()
            
            # Company name at top - مطابق للصفحة
            company_text = "الصقري للإتصالات"
            # Use much larger font for company name - تحسين تحميل الخط
            try:
                company_font = ImageFont.truetype('/System/Library/Fonts/Arial.ttf', 160)
            except:
                try:
                    company_font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 160)
                except:
                    company_font = arabic_font
            
            bbox = draw.textbbox((0, 0), company_text, font=company_font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (width_px - text_width) // 2
            y = 10  # Top area like in page
            draw.text((x, y), company_text, fill='black', font=company_font)
            
            # Barcode in center - مطابق للصفحة
            if phone.barcode_path and os.path.exists(phone.barcode_path):
                barcode_img = Image.open(phone.barcode_path)
                # Resize barcode to 80% width like in page
                barcode_width = int(width_px * 0.8)  # 80% of sticker width
                barcode_height = int(1 * 118.11)  # 1cm height
                barcode_img = barcode_img.resize((barcode_width, barcode_height), Image.Resampling.LANCZOS)
                
                # Paste barcode in center
                barcode_x = (width_px - barcode_width) // 2
                barcode_y = (height_px - barcode_height) // 2
                sticker_img.paste(barcode_img, (barcode_x, barcode_y))
            
            # Device details at bottom - مطابق للصفحة
            # Use the same Arabic font for all text
            detail_font = arabic_font
            
            # Calculate positions for 3 columns like in page - تحسين الترتيب
            col_width = width_px // 3
            start_y = height_px - 70
            
            # Use smaller font for details
            detail_font_small = ImageFont.truetype('/System/Library/Fonts/Arial.ttf', 8) if os.path.exists('/System/Library/Fonts/Arial.ttf') else detail_font
            
            # Device number - Column 1
            device_label = "رقم الجهاز"
            device_value = phone.phone_number
            # Center text in column with more spacing
            bbox1 = draw.textbbox((0, 0), device_label, font=detail_font_small)
            label_width1 = bbox1[2] - bbox1[0]
            x1 = col_width//2 - label_width1//2
            draw.text((x1, start_y), device_label, fill='black', font=detail_font_small)
            
            bbox1_val = draw.textbbox((0, 0), device_value, font=detail_font_small)
            value_width1 = bbox1_val[2] - bbox1_val[0]
            x1_val = col_width//2 - value_width1//2
            draw.text((x1_val, start_y + 25), device_value, fill='black', font=detail_font_small)
            
            # Battery percentage - Column 2
            battery_value = str(phone.age) if phone.condition == 'used' and phone.age else "100"
            battery_label = "نسبة البطارية"
            bbox2 = draw.textbbox((0, 0), battery_label, font=detail_font_small)
            label_width2 = bbox2[2] - bbox2[0]
            x2 = col_width + col_width//2 - label_width2//2
            draw.text((x2, start_y), battery_label, fill='black', font=detail_font_small)
            
            bbox2_val = draw.textbbox((0, 0), battery_value, font=detail_font_small)
            value_width2 = bbox2_val[2] - bbox2_val[0]
            x2_val = col_width + col_width//2 - value_width2//2
            draw.text((x2_val, start_y + 25), battery_value, fill='black', font=detail_font_small)
            
            # Memory - Column 3
            memory_value = phone.phone_memory if phone.phone_memory else "512"
            memory_label = "الذاكرة"
            bbox3 = draw.textbbox((0, 0), memory_label, font=detail_font_small)
            label_width3 = bbox3[2] - bbox3[0]
            x3 = 2*col_width + col_width//2 - label_width3//2
            draw.text((x3, start_y), memory_label, fill='black', font=detail_font_small)
            
            bbox3_val = draw.textbbox((0, 0), memory_value, font=detail_font_small)
            value_width3 = bbox3_val[2] - bbox3_val[0]
            x3_val = 2*col_width + col_width//2 - value_width3//2
            draw.text((x3_val, start_y + 25), memory_value, fill='black', font=detail_font_small)
            
            return sticker_img
        
        # Create the complete sticker image
        sticker_img = create_complete_sticker_image()
        
        # Save sticker image temporarily
        sticker_temp_path = f"static/barcodes/sticker_{phone_number}.png"
        sticker_img.save(sticker_temp_path, 'PNG')
        
        # Create PDF with the sticker image
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=(6*cm, 3*cm))
        
        # Add the complete sticker image to PDF
        p.drawImage(sticker_temp_path, 0, 0, width=6*cm, height=3*cm)
        
        p.showPage()
        p.save()
        
        # Clean up temp file
        if os.path.exists(sticker_temp_path):
            os.remove(sticker_temp_path)
        
        buffer.seek(0)
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f'barcode_{phone_number}.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        flash(f'خطأ في إنشاء PDF: {str(e)}', 'error')
        return redirect(url_for('print_barcode', phone_number=phone_number))

def generate_unique_phone_number():
    # Get the highest existing phone number
    highest_phone = db.session.query(func.max(Phone.phone_number)).scalar()
    
    if highest_phone is None:
        # If no phones exist, start from 1
        next_number = 1
    else:
        # Convert the highest phone number to integer and increment
        next_number = int(highest_phone) + 1
    
    # Check if we've reached the limit
    if next_number > 100000:
        raise ValueError("Maximum number of phones (100000) reached")
    
    # Format the number with leading zeros to make it 6 digits
    phone_number = f"{next_number:06d}"
    return phone_number









@app.route('/add_new_phone', methods=['GET', 'POST'])
@login_required
def add_new_phone():
    if request.method == 'POST':
        try:
            brand = request.form.get('brand')
            model = request.form.get('model')
            purchase_price_with_vat = float(request.form.get('purchase_price'))  # Input already includes VAT
            selling_price_with_vat = float(request.form.get('selling_price'))    # Input already includes VAT
            serial_number = request.form.get('serial_number')
            warranty = int(request.form.get('warranty'))
            
            # Calculate base prices without VAT
            purchase_price = calculate_price_without_vat(purchase_price_with_vat)
            selling_price = calculate_price_without_vat(selling_price_with_vat)
            
            # Calculate VAT amounts
            purchase_vat = purchase_price_with_vat - purchase_price
            selling_vat = selling_price_with_vat - selling_price
            description = request.form.get('description')
            
            # Customer information fields
            customer_name = request.form.get('customer_name')
            customer_phone = request.form.get('customer_phone')
            customer_id = request.form.get('customer_id')
            phone_color = request.form.get('phone_color')
            phone_memory = request.form.get('phone_memory')
            buyer_name = request.form.get('buyer_name')
            
            # Check if serial number already exists
            existing_phone = Phone.query.filter_by(serial_number=serial_number).first()
            if existing_phone:
                flash('الرقم التسلسلي موجود بالفعل في النظام', 'error')
                return redirect(url_for('add_new_phone'))
            
            try:
                phone_number = generate_unique_phone_number()
            except ValueError as e:
                flash(str(e), 'error')
                return redirect(url_for('add_new_phone'))
            
            # Generate barcode automatically
            barcode_path = generate_barcode(phone_number=phone_number)
            
            new_phone = Phone(
                brand=brand,
                model=model,
                condition='new',
                purchase_price=purchase_price,
                selling_price=selling_price,
                purchase_price_with_vat=purchase_price_with_vat,
                selling_price_with_vat=selling_price_with_vat,
                serial_number=serial_number,
                phone_number=phone_number,
                barcode_path=barcode_path,
                description=description,
                warranty=warranty,
                customer_name=customer_name,
                customer_phone=customer_phone,
                customer_id=customer_id,
                phone_color=phone_color,
                phone_memory=phone_memory,
                buyer_name=buyer_name
            )
            
            db.session.add(new_phone)
            db.session.commit()
            
            # Record a buy transaction
            buy_tx = Transaction(
                phone_id=new_phone.id,
                transaction_type='buy',
                serial_number=serial_number,
                price=purchase_price,
                price_with_vat=purchase_price_with_vat,
                vat_amount=purchase_vat,
                user_id=current_user.id,
                customer_name=customer_name,
                customer_phone=None,
                notes='شراء هاتف جديد'
            )
            db.session.add(buy_tx)
            db.session.commit()
            
            flash('تمت إضافة الهاتف الجديد بنجاح', 'success')
            return redirect(url_for('print_barcode', phone_number=phone_number))
        except ValueError:
            db.session.rollback()
            flash('خطأ في إدخال البيانات. يرجى التحقق من القيم المدخلة', 'error')
            return redirect(url_for('add_new_phone'))
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ: {str(e)}', 'error')
            return redirect(url_for('add_new_phone'))
    
    # Get brands and models data for the dropdown
    brands = {}
    phone_types = PhoneType.query.all()
    for phone_type in phone_types:
        if phone_type.brand not in brands:
            brands[phone_type.brand] = []
        brands[phone_type.brand].append(phone_type.model)
    
    return render_template('add_new_phone.html', brands=brands)

@app.route('/add_used_phone', methods=['GET', 'POST'])
@login_required
def add_used_phone():
    if request.method == 'POST':
        try:
            brand = request.form.get('brand')
            model = request.form.get('model')
            purchase_price_with_vat = float(request.form.get('purchase_price'))  # Input already includes VAT
            selling_price_with_vat = float(request.form.get('selling_price'))    # Input already includes VAT
            serial_number = request.form.get('serial_number')
            phone_condition = request.form.get('phone_condition')
            age = int(request.form.get('age'))
            
            # Calculate base prices without VAT
            purchase_price = calculate_price_without_vat(purchase_price_with_vat)
            selling_price = calculate_price_without_vat(selling_price_with_vat)
            
            # Calculate VAT amounts
            purchase_vat = purchase_price_with_vat - purchase_price
            selling_vat = selling_price_with_vat - selling_price
            description = request.form.get('description')
            
            # Customer information fields
            customer_name = request.form.get('customer_name')
            customer_phone = request.form.get('customer_phone')
            customer_id = request.form.get('customer_id')
            phone_color = request.form.get('phone_color')
            phone_memory = request.form.get('phone_memory')
            buyer_name = request.form.get('buyer_name')
            
            existing_phone = Phone.query.filter_by(serial_number=serial_number).first()
            if existing_phone:
                flash('الرقم التسلسلي موجود بالفعل في النظام', 'error')
                return redirect(url_for('add_used_phone'))
            
            try:
                phone_number = generate_unique_phone_number()
            except ValueError as e:
                flash(str(e), 'error')
                return redirect(url_for('add_used_phone'))
            
            # Generate barcode automatically with battery age
            barcode_path = generate_barcode(phone_number=phone_number, battery_age=age)
            
            used_phone = Phone(
                brand=brand,
                model=model,
                condition='used',
                purchase_price=purchase_price,
                selling_price=selling_price,
                purchase_price_with_vat=purchase_price_with_vat,
                selling_price_with_vat=selling_price_with_vat,
                serial_number=serial_number,
                phone_number=phone_number,
                barcode_path=barcode_path,
                phone_condition=phone_condition,
                age=age,
                description=description,
                customer_name=customer_name,
                customer_phone=customer_phone,
                customer_id=customer_id,
                phone_color=phone_color,
                phone_memory=phone_memory,
                buyer_name=buyer_name
            )
            db.session.add(used_phone)
            db.session.commit()
            
            # Record a buy transaction
            buy_tx = Transaction(
                phone_id=used_phone.id,
                transaction_type='buy',
                serial_number=serial_number,
                price=purchase_price,
                price_with_vat=purchase_price_with_vat,
                vat_amount=purchase_vat,
                user_id=current_user.id,
                customer_name=customer_name,
                customer_phone=None,
                notes='شراء هاتف مستعمل'
            )
            db.session.add(buy_tx)
            db.session.commit()
            
            flash('تمت إضافة الهاتف المستعمل بنجاح', 'success')
            return redirect(url_for('print_barcode', phone_number=phone_number))
        except ValueError:
            db.session.rollback()
            flash('خطأ في إدخال البيانات. يرجى التحقق من القيم المدخلة', 'error')
            return redirect(url_for('add_used_phone'))
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ: {str(e)}', 'error')
            return redirect(url_for('add_used_phone'))
    
    # Get brands and models data for the dropdown
    brands = {}
    phone_types = PhoneType.query.all()
    for phone_type in phone_types:
        if phone_type.brand not in brands:
            brands[phone_type.brand] = []
        brands[phone_type.brand].append(phone_type.model)
    
    return render_template('add_used_phone.html', brands=brands)

@app.route('/dashboard/delete/<int:phone_id>', methods=['POST'])
@login_required
def delete_phone(phone_id):
    phone = Phone.query.get_or_404(phone_id)
    try:
        db.session.delete(phone)
        db.session.commit()
        flash('تم حذف الهاتف بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف الهاتف: {str(e)}', 'error')
    return redirect(url_for('dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Invoice routes removed - replaced by sales system

@app.route('/create_sale')
@login_required
def create_sale_page():
    """Show create sale page"""
    phones = Phone.query.all()
    accessories = Accessory.query.all()
    
    # Convert Phone objects to dictionaries for JSON serialization
    phones_data = []
    for phone in phones:
        phones_data.append({
            'id': phone.id,
            'brand': phone.brand,
            'model': phone.model,
            'serial_number': phone.serial_number,
            'selling_price': phone.selling_price_with_vat,  # Use price with VAT
            'description': phone.description or ''
        })
    
    # Convert Accessory objects to dictionaries
    accessories_data = []
    for accessory in accessories:
        accessories_data.append({
            'id': accessory.id,
            'name': accessory.name,
            'category': accessory.category,
            'description': accessory.description or '',
            'selling_price': accessory.selling_price_with_vat,  # Use price with VAT
            'quantity_in_stock': accessory.quantity_in_stock
        })
    
    return render_template('create_sale.html', phones=phones_data, accessories=accessories_data)

@app.route('/create_sale', methods=['POST'])
@login_required
def create_sale():
    """Create a new sale with multiple items"""
    try:
        data = request.get_json()
        
        # Create sale record
        sale = Sale(
            sale_number=generate_invoice_number(),
            customer_name=data['customer_name'],
            customer_phone=data['customer_phone'],
            customer_email=data['customer_email'],
            customer_address=data['customer_address'],
            payment_method=data['payment_method'],
            notes=data['notes']
        )
        
        # Calculate totals - prices already include VAT
        total_amount = sum(item['totalPrice'] for item in data['items'])
        # Calculate VAT amount from total (since prices include VAT)
        subtotal = total_amount / (1 + VAT_RATE)  # Remove VAT to get subtotal
        vat_amount = total_amount - subtotal
        
        sale.subtotal = subtotal
        sale.vat_amount = vat_amount
        sale.total_amount = total_amount
        
        db.session.add(sale)
        db.session.flush()  # Get the sale ID
        
        # Add sale items
        for item_data in data['items']:
            # Get purchase price from the product
            purchase_price = 0.0
            if item_data['type'] == 'phone':
                phone = Phone.query.get(item_data['id'])
                if phone:
                    purchase_price = phone.purchase_price
                    sale_item = SaleItem(
                        sale_id=sale.id,
                        product_type=item_data['type'],
                        product_name=item_data['name'],
                        product_description=item_data['description'],
                        unit_price=item_data['unitPrice'],
                        purchase_price=purchase_price,
                        quantity=item_data['quantity'],
                        total_price=item_data['totalPrice']
                    )
                    sale_item.serial_number = phone.serial_number
                    # Remove phone from inventory
                    db.session.delete(phone)
            elif item_data['type'] in ['accessory', 'charger', 'case', 'screen_protector']:
                accessory = Accessory.query.get(item_data['id'])
                if accessory:
                    purchase_price = accessory.purchase_price
                    sale_item = SaleItem(
                        sale_id=sale.id,
                        product_type=item_data['type'],
                        product_name=item_data['name'],
                        product_description=item_data['description'],
                        unit_price=item_data['unitPrice'],
                        purchase_price=purchase_price,
                        quantity=item_data['quantity'],
                        total_price=item_data['totalPrice']
                    )
                    # Update accessory stock
                    accessory.quantity_in_stock -= item_data['quantity']
                    if accessory.quantity_in_stock < 0:
                        accessory.quantity_in_stock = 0
            
            db.session.add(sale_item)
        
        db.session.commit()
        
        return jsonify({'success': True, 'sale_id': sale.id})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/sale/<int:sale_id>')
@login_required
def view_sale(sale_id):
    """View sale details"""
    sale = Sale.query.get_or_404(sale_id)
    return render_template('view_sale.html', sale=sale)

@app.route('/accessories')
@login_required
def list_accessories():
    """List all accessories"""
    accessories = Accessory.query.order_by(Accessory.date_added.desc()).all()
    
    # Calculate totals considering quantity
    total_purchase_value = sum(acc.purchase_price_with_vat * acc.quantity_in_stock for acc in accessories)
    total_selling_value = sum(acc.selling_price_with_vat * acc.quantity_in_stock for acc in accessories)
    total_quantity = sum(acc.quantity_in_stock for acc in accessories)
    
    # Get categories for display
    categories = AccessoryCategory.query.all()
    category_map = {cat.name: cat.arabic_name for cat in categories}
    
    return render_template('list_accessories.html', 
                         accessories=accessories,
                         total_purchase_value=total_purchase_value,
                         total_selling_value=total_selling_value,
                         total_quantity=total_quantity,
                         category_map=category_map)

@app.route('/add_accessory', methods=['GET', 'POST'])
@login_required
def add_accessory():
    """Add new accessory"""
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            category = request.form.get('category')
            description = request.form.get('description')
            purchase_price_with_vat = float(request.form.get('purchase_price'))  # Input already includes VAT
            selling_price_with_vat = float(request.form.get('selling_price'))    # Input already includes VAT
            quantity = int(request.form.get('quantity', 0))
            supplier = request.form.get('supplier')
            notes = request.form.get('notes')
            
            # Calculate base prices without VAT
            purchase_price = calculate_price_without_vat(purchase_price_with_vat)
            selling_price = calculate_price_without_vat(selling_price_with_vat)
            
            # Calculate VAT amounts
            purchase_vat = purchase_price_with_vat - purchase_price
            selling_vat = selling_price_with_vat - selling_price
            
            accessory = Accessory(
                name=name,
                category=category,
                description=description,
                purchase_price=purchase_price,
                selling_price=selling_price,
                purchase_price_with_vat=purchase_price_with_vat,
                selling_price_with_vat=selling_price_with_vat,
                quantity_in_stock=quantity,
                supplier=supplier,
                notes=notes
            )
            
            db.session.add(accessory)
            db.session.commit()
            
            flash('تمت إضافة الأكسسوار بنجاح', 'success')
            return redirect(url_for('list_accessories'))
            
        except ValueError:
            flash('خطأ في إدخال البيانات. يرجى التحقق من القيم المدخلة', 'error')
            return redirect(url_for('add_accessory'))
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ: {str(e)}', 'error')
            return redirect(url_for('add_accessory'))
    
    # Get categories for the dropdown
    categories = AccessoryCategory.query.all()
    return render_template('add_accessory.html', categories=categories)

@app.route('/edit_accessory/<int:accessory_id>', methods=['GET', 'POST'])
@login_required
def edit_accessory(accessory_id):
    """Edit existing accessory"""
    accessory = Accessory.query.get_or_404(accessory_id)
    
    if request.method == 'POST':
        try:
            accessory.name = request.form.get('name')
            accessory.category = request.form.get('category')
            accessory.description = request.form.get('description')
            purchase_price_with_vat = float(request.form.get('purchase_price'))  # Input already includes VAT
            selling_price_with_vat = float(request.form.get('selling_price'))    # Input already includes VAT
            accessory.quantity_in_stock = int(request.form.get('quantity', 0))
            accessory.supplier = request.form.get('supplier')
            accessory.notes = request.form.get('notes')
            
            # Calculate base prices without VAT
            accessory.purchase_price = calculate_price_without_vat(purchase_price_with_vat)
            accessory.selling_price = calculate_price_without_vat(selling_price_with_vat)
            
            # Store the prices with VAT
            accessory.purchase_price_with_vat = purchase_price_with_vat
            accessory.selling_price_with_vat = selling_price_with_vat
            
            db.session.commit()
            
            flash('تم تحديث الأكسسوار بنجاح', 'success')
            return redirect(url_for('list_accessories'))
            
        except ValueError:
            flash('خطأ في إدخال البيانات. يرجى التحقق من القيم المدخلة', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ: {str(e)}', 'error')
    
    # Get categories for the dropdown
    categories = AccessoryCategory.query.all()
    return render_template('edit_accessory.html', accessory=accessory, categories=categories)

@app.route('/delete_accessory/<int:accessory_id>', methods=['DELETE'])
@login_required
def delete_accessory(accessory_id):
    """Delete accessory"""
    try:
        accessory = Accessory.query.get_or_404(accessory_id)
        db.session.delete(accessory)
        db.session.commit()
        return jsonify({'success': True, 'message': 'تم حذف الأكسسوار بنجاح'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/search')
@login_required
def search():
    """Search for phones and accessories"""
    search_term = request.args.get('search_term', '').strip()
    search_type = request.args.get('search_type', 'all')
    condition = request.args.get('condition', '')
    
    phones = []
    accessories = []
    
    if search_term:
        # Search in phones
        if search_type in ['all', 'phones']:
            phone_query = Phone.query
            
            # Add condition filter if specified
            if condition:
                phone_query = phone_query.filter_by(condition=condition)
            
            # Search in multiple phone fields
            phone_query = phone_query.filter(
                db.or_(
                    Phone.phone_number.contains(search_term),
                    Phone.serial_number.contains(search_term),
                    Phone.brand.contains(search_term),
                    Phone.model.contains(search_term),
                    Phone.phone_color.contains(search_term),
                    Phone.phone_memory.contains(search_term),
                    Phone.description.contains(search_term),
                    Phone.customer_name.contains(search_term),
                    Phone.customer_id.contains(search_term)
                )
            )
            
            phones = phone_query.all()
        
        # Search in accessories
        if search_type in ['all', 'accessories']:
            accessory_query = Accessory.query.filter(
                db.or_(
                    Accessory.name.contains(search_term),
                    Accessory.category.contains(search_term),
                    Accessory.description.contains(search_term),
                    Accessory.supplier.contains(search_term),
                    Accessory.notes.contains(search_term)
                )
            )
            
            accessories = accessory_query.all()
    
    return render_template('search.html', 
                         phones=phones, 
                         accessories=accessories,
                         search_term=search_term,
                         search_type=search_type,
                         condition=condition)

@app.route('/sales')
@login_required
def list_sales():
    """List all sales with filtering"""
    from datetime import datetime, timedelta
    
    # Get filter parameters
    filter_type = request.args.get('filter_type', 'all')
    filter_date = request.args.get('filter_date', '')
    filter_month_year = request.args.get('filter_month_year', '')
    filter_month_month = request.args.get('filter_month_month', '')
    filter_year = request.args.get('filter_year', '')
    
    # Base query
    query = Sale.query
    
    # Apply filters
    if filter_type == 'day' and filter_date:
        try:
            filter_date_obj = datetime.strptime(filter_date, '%Y-%m-%d')
            next_day = filter_date_obj + timedelta(days=1)
            query = query.filter(
                Sale.date_created >= filter_date_obj,
                Sale.date_created < next_day
            )
        except ValueError:
            pass
    elif filter_type == 'month' and filter_month_year and filter_month_month:
        try:
            month_start = datetime(int(filter_month_year), int(filter_month_month), 1)
            if int(filter_month_month) == 12:
                next_month = datetime(int(filter_month_year) + 1, 1, 1)
            else:
                next_month = datetime(int(filter_month_year), int(filter_month_month) + 1, 1)
            query = query.filter(
                Sale.date_created >= month_start,
                Sale.date_created < next_month
            )
        except ValueError:
            pass
    elif filter_type == 'year' and filter_year:
        try:
            year_start = datetime(int(filter_year), 1, 1)
            year_end = datetime(int(filter_year) + 1, 1, 1)
            query = query.filter(
                Sale.date_created >= year_start,
                Sale.date_created < year_end
            )
        except ValueError:
            pass
    
    # Get filtered sales
    sales = query.order_by(Sale.date_created.desc()).all()
    
    # Calculate summary statistics for filtered results
    total_sales_count = len(sales)
    total_sales_amount = sum(sale.total_amount for sale in sales)
    total_sales_subtotal = sum(sale.subtotal for sale in sales)
    total_vat_amount = sum(sale.vat_amount for sale in sales)
    
    # Get current date for default values
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    
    return render_template('list_sales.html', 
                         sales=sales,
                         filter_type=filter_type,
                         filter_date=filter_date,
                         filter_month_year=filter_month_year,
                         filter_month_month=filter_month_month,
                         filter_year=filter_year,
                         total_sales_count=total_sales_count,
                         total_sales_amount=total_sales_amount,
                         total_sales_subtotal=total_sales_subtotal,
                         total_vat_amount=total_vat_amount,
                         current_year=current_year,
                         current_month=current_month)

# Invoices route removed - replaced by sales system



@app.route('/inventory_summary')
@login_required
def inventory_summary():
    # Get total phones count
    total_phones = Phone.query.count()
    
    # Get new and used phones counts
    new_phones_count = Phone.query.filter_by(condition='new').count()
    used_phones_count = Phone.query.filter_by(condition='used').count()
    
    # Get values for new and used phones
    new_phones = Phone.query.filter_by(condition='new').all()
    used_phones = Phone.query.filter_by(condition='used').all()
    
    # Calculate purchase and selling values
    new_phones_purchase_value = sum(phone.purchase_price for phone in new_phones)
    new_phones_selling_value = sum(phone.selling_price for phone in new_phones)
    new_phones_profit = new_phones_selling_value - new_phones_purchase_value
    
    used_phones_purchase_value = sum(phone.purchase_price for phone in used_phones)
    used_phones_selling_value = sum(phone.selling_price for phone in used_phones)
    used_phones_profit = used_phones_selling_value - used_phones_purchase_value
    
    # Total values
    total_purchase_value = new_phones_purchase_value + used_phones_purchase_value
    total_selling_value = new_phones_selling_value + used_phones_selling_value
    total_profit = total_selling_value - total_purchase_value
    
    # Get phone type summary (new vs used)
    phone_type_summary = db.session.query(
        Phone.condition,
        func.count(Phone.id).label('total_phones'),
        func.sum(Phone.purchase_price).label('total_purchase_value'),
        func.sum(Phone.selling_price).label('total_selling_value'),
        func.avg(Phone.selling_price).label('average_price')
    ).group_by(Phone.condition).all()
    
    # Get brand and model summary within each phone type
    new_phones_brand_summary = db.session.query(
        Phone.brand,
        Phone.model,
        func.count(Phone.id).label('total_phones'),
        func.sum(Phone.purchase_price).label('total_purchase_value'),
        func.sum(Phone.selling_price).label('total_selling_value'),
        func.avg(Phone.selling_price).label('average_price')
    ).filter_by(condition='new').group_by(Phone.brand, Phone.model).all()
    
    used_phones_brand_summary = db.session.query(
        Phone.brand,
        Phone.model,
        func.count(Phone.id).label('total_phones'),
        func.sum(Phone.purchase_price).label('total_purchase_value'),
        func.sum(Phone.selling_price).label('total_selling_value'),
        func.avg(Phone.selling_price).label('average_price')
    ).filter_by(condition='used').group_by(Phone.brand, Phone.model).all()
    
    return render_template('inventory_summary.html',
                         total_phones=total_phones,
                         new_phones_count=new_phones_count,
                         used_phones_count=used_phones_count,
                         new_phones_purchase_value=new_phones_purchase_value,
                         new_phones_selling_value=new_phones_selling_value,
                         new_phones_profit=new_phones_profit,
                         used_phones_purchase_value=used_phones_purchase_value,
                         used_phones_selling_value=used_phones_selling_value,
                         used_phones_profit=used_phones_profit,
                         total_purchase_value=total_purchase_value,
                         total_selling_value=total_selling_value,
                         total_profit=total_profit,
                         phone_type_summary=phone_type_summary,
                         new_phones_brand_summary=new_phones_brand_summary,
                         used_phones_brand_summary=used_phones_brand_summary)

# AJAX routes for phone types and accessory categories
@app.route('/add_phone_type_ajax', methods=['POST'])
@login_required
def add_phone_type_ajax():
    """Add a new phone type via AJAX"""
    try:
        data = request.get_json()
        brand = data.get('brand', '').strip()
        model = data.get('model', '').strip()
        
        if not brand or not model:
            return jsonify({'success': False, 'message': 'يرجى إدخال العلامة التجارية والموديل'})
        
        # Check if phone type already exists
        existing = PhoneType.query.filter_by(brand=brand, model=model).first()
        if existing:
            return jsonify({'success': False, 'message': 'هذا الموديل موجود بالفعل'})
        
        # Create new phone type
        phone_type = PhoneType(brand=brand, model=model)
        db.session.add(phone_type)
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'تم إضافة {brand} {model} بنجاح'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@app.route('/delete_phone_type_ajax', methods=['POST'])
@login_required
def delete_phone_type_ajax():
    """Delete a phone type via AJAX"""
    try:
        data = request.get_json()
        brand = data.get('brand', '').strip()
        model = data.get('model', '').strip()
        
        if not brand or not model:
            return jsonify({'success': False, 'message': 'يرجى اختيار العلامة التجارية والموديل'})
        
        # Check if phone type exists
        phone_type = PhoneType.query.filter_by(brand=brand, model=model).first()
        if not phone_type:
            return jsonify({'success': False, 'message': 'الموديل غير موجود'})
        
        # Check if any phones are using this type
        phones_using_type = Phone.query.filter_by(brand=brand, model=model).count()
        if phones_using_type > 0:
            return jsonify({'success': False, 'message': f'لا يمكن حذف هذا الموديل لأنه مستخدم في {phones_using_type} هاتف'})
        
        # Delete the phone type
        db.session.delete(phone_type)
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'تم حذف {brand} {model} بنجاح'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@app.route('/get_phone_types_ajax')
@login_required
def get_phone_types_ajax():
    """Get phone types for AJAX"""
    try:
        phone_types = PhoneType.query.all()
        brands = {}
        for phone_type in phone_types:
            if phone_type.brand not in brands:
                brands[phone_type.brand] = []
            brands[phone_type.brand].append(phone_type.model)
        
        return jsonify({'success': True, 'brands': brands})
    except Exception as e:
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@app.route('/add_accessory_category_ajax', methods=['POST'])
@login_required
def add_accessory_category_ajax():
    """Add a new accessory category via AJAX"""
    try:
        data = request.get_json()
        arabic_name = data.get('name', '').strip()
        
        if not arabic_name:
            return jsonify({'success': False, 'message': 'يرجى إدخال اسم الفئة'})
        
        # Generate English name from Arabic name
        english_name = arabic_name.lower().replace(' ', '_').replace('أ', 'a').replace('ب', 'b').replace('ت', 't').replace('ث', 'th').replace('ج', 'j').replace('ح', 'h').replace('خ', 'kh').replace('د', 'd').replace('ذ', 'th').replace('ر', 'r').replace('ز', 'z').replace('س', 's').replace('ش', 'sh').replace('ص', 's').replace('ض', 'd').replace('ط', 't').replace('ظ', 'z').replace('ع', 'a').replace('غ', 'gh').replace('ف', 'f').replace('ق', 'q').replace('ك', 'k').replace('ل', 'l').replace('م', 'm').replace('ن', 'n').replace('ه', 'h').replace('و', 'w').replace('ي', 'y').replace('ة', 'h').replace('ى', 'a').replace('ئ', 'a')
        
        # Check if category already exists (check both name and arabic_name)
        existing = AccessoryCategory.query.filter(
            (AccessoryCategory.name == english_name) | 
            (AccessoryCategory.arabic_name == arabic_name)
        ).first()
        if existing:
            return jsonify({'success': False, 'message': 'هذه الفئة موجودة بالفعل'})
        
        # Create new category
        category = AccessoryCategory(name=english_name, arabic_name=arabic_name)
        db.session.add(category)
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'تم إضافة فئة {arabic_name} بنجاح'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@app.route('/delete_accessory_category_ajax', methods=['POST'])
@login_required
def delete_accessory_category_ajax():
    """Delete an accessory category via AJAX"""
    try:
        data = request.get_json()
        arabic_name = data.get('name', '').strip()
        
        if not arabic_name:
            return jsonify({'success': False, 'message': 'يرجى اختيار الفئة'})
        
        # Check if category exists (search by arabic_name)
        category = AccessoryCategory.query.filter_by(arabic_name=arabic_name).first()
        if not category:
            return jsonify({'success': False, 'message': 'الفئة غير موجودة'})
        
        # Check if any accessories are using this category
        accessories_using_category = Accessory.query.filter_by(category=category.name).count()
        if accessories_using_category > 0:
            return jsonify({'success': False, 'message': f'لا يمكن حذف هذه الفئة لأنها مستخدمة في {accessories_using_category} أكسسوار'})
        
        # Delete the category
        db.session.delete(category)
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'تم حذف فئة {arabic_name} بنجاح'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@app.route('/get_accessory_categories_ajax')
@login_required
def get_accessory_categories_ajax():
    """Get accessory categories for AJAX"""
    try:
        categories = AccessoryCategory.query.all()
        category_list = [category.arabic_name for category in categories]
        return jsonify({'success': True, 'categories': category_list})
    except Exception as e:
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

# sell_phone route removed - replaced by comprehensive sales system

if __name__ == '__main__':
    with app.app_context():
        # Initialize database with proper error handling
        initialize_database()
    
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