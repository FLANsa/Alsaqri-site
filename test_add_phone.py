#!/usr/bin/env python3
"""
Test script to debug phone addition issues
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Phone, User
from datetime import datetime

def test_add_phone():
    """Test adding a phone to the database"""
    with app.app_context():
        try:
            # Check if we have users
            users = User.query.all()
            print(f"👥 Found {len(users)} users in database")
            for user in users:
                print(f"   - {user.username} (admin: {user.is_admin})")
            
            # Check current phones
            phones = Phone.query.all()
            print(f"📱 Found {len(phones)} phones in database")
            
            # Try to add a test phone
            print("\n📱 Adding test phone...")
            
            test_phone = Phone(
                brand="Test Brand",
                model="Test Model",
                condition='new',
                purchase_price=1000.0,
                selling_price=1200.0,
                purchase_price_with_vat=1150.0,
                selling_price_with_vat=1380.0,
                serial_number="TEST123456",
                phone_number="000001",
                barcode_path="test_barcode.png",
                description="Test phone for debugging",
                warranty=12,
                customer_name="Test Customer",
                customer_id="123456789",
                phone_color="Black",
                phone_memory="128GB",
                buyer_name="Test Buyer",
                date_added=datetime.utcnow()
            )
            
            db.session.add(test_phone)
            db.session.commit()
            
            print("✅ Test phone added successfully!")
            
            # Check phones again
            phones_after = Phone.query.all()
            print(f"📱 Now have {len(phones_after)} phones in database")
            
            # Clean up - remove test phone
            db.session.delete(test_phone)
            db.session.commit()
            print("🧹 Test phone removed")
            
            return True
            
        except Exception as e:
            print(f"❌ Error adding test phone: {str(e)}")
            db.session.rollback()
            return False

def check_database_schema():
    """Check database schema"""
    with app.app_context():
        try:
            # Check Phone table schema
            print("🔍 Checking Phone table schema...")
            
            # Try to get column info
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = inspector.get_columns('phone')
            
            print(f"📋 Phone table has {len(columns)} columns:")
            for col in columns:
                print(f"   - {col['name']}: {col['type']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error checking schema: {str(e)}")
            return False

if __name__ == "__main__":
    print("🔧 Testing phone addition...")
    
    print("\n1. Checking database schema:")
    schema_ok = check_database_schema()
    
    print("\n2. Testing phone addition:")
    phone_ok = test_add_phone()
    
    if schema_ok and phone_ok:
        print("\n🎉 All tests passed! Phone addition should work.")
    else:
        print("\n❌ Tests failed! There might be an issue.")
        sys.exit(1)
