# 📱 Phone Shop Management System

## 🎯 Overview
A comprehensive phone shop management system built with Flask, featuring inventory management, sales tracking, and thermal receipt printing capabilities.

## ✨ Features

### 🏪 **Core Management**
- **Phone Inventory**: Add new/used phones with detailed specifications
- **Accessory Management**: Track accessories, chargers, cases, and more
- **Customer Database**: Store customer information and purchase history
- **Barcode System**: Generate and scan barcodes for inventory tracking

### 🛍️ **Sales System**
- **Multi-Item Sales**: Sell multiple products in a single transaction
- **Comprehensive Invoicing**: Detailed sales records with customer information
- **VAT Calculation**: Automatic 15% VAT calculation for Saudi Arabia compliance
- **Payment Methods**: Support for cash, credit card, bank transfer, and more

### 🧾 **Receipt System**
- **Thermal Printer Compatible**: Optimized for 80mm receipt roll printers
- **Dual Format**: Screen view for management, print view for receipts
- **Professional Layout**: Company branding, customer details, itemized products
- **Automatic Calculations**: Subtotal, VAT, and total amounts

### 📊 **Reporting & Analytics**
- **Dashboard**: Real-time overview of inventory and sales
- **Inventory Summary**: Detailed breakdown by brand, condition, and value
- **Sales History**: Complete transaction records with search capabilities
- **Financial Reports**: Purchase costs, selling prices, and profit margins

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8+
- pip package manager

### Setup Steps
1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd phone_shop_system
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Access the system**
   - URL: http://127.0.0.1:5001
   - Username: `admin`
   - Password: `admin123`

## 🏗️ System Architecture

### **Database Models**
- **Phone**: Brand, model, condition, prices, serial numbers
- **Accessory**: Name, category, stock quantities, supplier info
- **Sale**: Multi-item sales with customer details
- **SaleItem**: Individual products within sales
- **User**: Admin authentication and permissions

### **Key Routes**
- `/dashboard` - Main dashboard with overview
- `/create_sale` - Create new multi-item sales
- `/inventory_summary` - Detailed inventory analysis
- `/accessories` - Manage accessory inventory
- `/sales` - View all sales history

### **Receipt Printing**
- **Template**: `templates/view_sale.html`
- **Format**: 80mm thermal printer compatible
- **Features**: Company branding, customer details, itemized products
- **Print Method**: Custom print function with dedicated styling

## 🎨 User Interface

### **Design Principles**
- **RTL Support**: Right-to-left Arabic text layout
- **Responsive Design**: Works on desktop and mobile devices
- **Modern UI**: Bootstrap-based interface with custom styling
- **Intuitive Navigation**: Easy-to-use menu system

### **Key Pages**
- **Dashboard**: Overview cards and recent activity
- **Sales Creation**: Multi-step form for complex transactions
- **Inventory Management**: Add, edit, and track products
- **Receipt View**: Professional invoice layout

## 🔧 Technical Details

### **Technologies Used**
- **Backend**: Flask (Python web framework)
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap
- **Barcode**: python-barcode library
- **Authentication**: Flask-Login

### **Key Functions**
- **VAT Calculation**: 15% Saudi Arabia compliance
- **Barcode Generation**: Automatic phone number assignment
- **Inventory Updates**: Real-time stock management
- **Sales Processing**: Multi-item transaction handling

## 🧪 Testing & Demo Data

### **Sample Data Included**
- **5 Demo Phones**: iPhone, Samsung, OnePlus, Xiaomi, Google
- **8 Demo Accessories**: Headphones, chargers, cases, cables
- **3 Demo Sales**: Multi-item transactions with different customers

### **Testing Scenarios**
- **Inventory Management**: Add, edit, delete products
- **Sales Creation**: Multi-item transactions
- **Receipt Printing**: Thermal printer format testing
- **User Authentication**: Login/logout functionality

## 🔒 Security Features

### **Authentication**
- **Admin User**: Default admin account creation
- **Session Management**: Secure login/logout handling
- **Route Protection**: Login-required decorators

### **Data Validation**
- **Input Sanitization**: Form data validation
- **SQL Injection Protection**: SQLAlchemy ORM usage
- **Error Handling**: Graceful error management

## 📈 Future Enhancements

### **Planned Features**
- **Multi-User Support**: Role-based access control
- **Advanced Reporting**: Export to PDF/Excel
- **Backup System**: Database backup and restore
- **API Integration**: External system connectivity
- **Mobile App**: Native iOS/Android applications

### **Technical Improvements**
- **Performance Optimization**: Database query optimization
- **Caching System**: Redis integration for speed
- **Logging System**: Comprehensive activity logging
- **Testing Suite**: Automated testing framework

## 🐛 Troubleshooting

### **Common Issues**
- **Port Conflicts**: Ensure port 5001 is available
- **Database Errors**: Delete `instance/phone_shop.db` to reset
- **Barcode Issues**: Check `static/barcodes/` directory permissions
- **Print Problems**: Verify browser print settings

### **Debug Mode**
- **Development Server**: Debug mode enabled by default
- **Error Logging**: Detailed error messages in console
- **Hot Reload**: Automatic restart on code changes

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the documentation

---

**Last Updated**: August 28, 2025
**Version**: 2.0.0
**Status**: Production Ready Web Application 