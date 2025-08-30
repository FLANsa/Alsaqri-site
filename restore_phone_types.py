#!/usr/bin/env python3
"""
Script to restore phone types and dropdown functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, PhoneType

def restore_phone_types():
    """Restore default phone types"""
    with app.app_context():
        try:
            # Check if phone types already exist
            count = PhoneType.query.count()
            if count > 0:
                print(f"📱 Found {count} phone types already in database")
                return True
            
            print("📱 Restoring default phone types...")
            
            # Default phone types
            default_types = [
                # Apple - Most Popular Models
                {'brand': 'Apple', 'model': 'iPhone 15 Pro Max'},
                {'brand': 'Apple', 'model': 'iPhone 15 Pro'},
                {'brand': 'Apple', 'model': 'iPhone 15 Plus'},
                {'brand': 'Apple', 'model': 'iPhone 15'},
                {'brand': 'Apple', 'model': 'iPhone 14 Pro Max'},
                {'brand': 'Apple', 'model': 'iPhone 14 Pro'},
                {'brand': 'Apple', 'model': 'iPhone 14 Plus'},
                {'brand': 'Apple', 'model': 'iPhone 14'},
                {'brand': 'Apple', 'model': 'iPhone 13 Pro Max'},
                {'brand': 'Apple', 'model': 'iPhone 13 Pro'},
                {'brand': 'Apple', 'model': 'iPhone 13'},
                {'brand': 'Apple', 'model': 'iPhone 12 Pro Max'},
                {'brand': 'Apple', 'model': 'iPhone 12 Pro'},
                {'brand': 'Apple', 'model': 'iPhone 12'},
                {'brand': 'Apple', 'model': 'iPhone 11 Pro Max'},
                {'brand': 'Apple', 'model': 'iPhone 11 Pro'},
                {'brand': 'Apple', 'model': 'iPhone 11'},
                
                # Samsung - Most Popular Models
                {'brand': 'Samsung', 'model': 'Galaxy S24 Ultra'},
                {'brand': 'Samsung', 'model': 'Galaxy S24+'},
                {'brand': 'Samsung', 'model': 'Galaxy S24'},
                {'brand': 'Samsung', 'model': 'Galaxy S23 Ultra'},
                {'brand': 'Samsung', 'model': 'Galaxy S23+'},
                {'brand': 'Samsung', 'model': 'Galaxy S23'},
                {'brand': 'Samsung', 'model': 'Galaxy S22 Ultra'},
                {'brand': 'Samsung', 'model': 'Galaxy S22+'},
                {'brand': 'Samsung', 'model': 'Galaxy S22'},
                {'brand': 'Samsung', 'model': 'Galaxy S21 Ultra'},
                {'brand': 'Samsung', 'model': 'Galaxy S21+'},
                {'brand': 'Samsung', 'model': 'Galaxy S21'},
                {'brand': 'Samsung', 'model': 'Galaxy A54'},
                {'brand': 'Samsung', 'model': 'Galaxy A34'},
                {'brand': 'Samsung', 'model': 'Galaxy A24'},
                
                # Huawei - Popular Models
                {'brand': 'Huawei', 'model': 'P60 Pro'},
                {'brand': 'Huawei', 'model': 'P60'},
                {'brand': 'Huawei', 'model': 'P50 Pro'},
                {'brand': 'Huawei', 'model': 'P50'},
                {'brand': 'Huawei', 'model': 'Mate 60 Pro'},
                {'brand': 'Huawei', 'model': 'Mate 50 Pro'},
                {'brand': 'Huawei', 'model': 'Nova 11'},
                {'brand': 'Huawei', 'model': 'Nova 10'},
                
                # Xiaomi - Popular Models
                {'brand': 'Xiaomi', 'model': '14 Ultra'},
                {'brand': 'Xiaomi', 'model': '14 Pro'},
                {'brand': 'Xiaomi', 'model': '14'},
                {'brand': 'Xiaomi', 'model': '13 Ultra'},
                {'brand': 'Xiaomi', 'model': '13 Pro'},
                {'brand': 'Xiaomi', 'model': '13'},
                {'brand': 'Xiaomi', 'model': 'Redmi Note 13 Pro+'},
                {'brand': 'Xiaomi', 'model': 'Redmi Note 13 Pro'},
                {'brand': 'Xiaomi', 'model': 'Redmi Note 13'},
                
                # OnePlus - Popular Models
                {'brand': 'OnePlus', 'model': '12'},
                {'brand': 'OnePlus', 'model': '11'},
                {'brand': 'OnePlus', 'model': '10 Pro'},
                {'brand': 'OnePlus', 'model': '10'},
                {'brand': 'OnePlus', 'model': 'Nord 3'},
                {'brand': 'OnePlus', 'model': 'Nord 2T'},
                
                # Google - Popular Models
                {'brand': 'Google', 'model': 'Pixel 8 Pro'},
                {'brand': 'Google', 'model': 'Pixel 8'},
                {'brand': 'Google', 'model': 'Pixel 7 Pro'},
                {'brand': 'Google', 'model': 'Pixel 7'},
                {'brand': 'Google', 'model': 'Pixel 6 Pro'},
                {'brand': 'Google', 'model': 'Pixel 6'},
                
                # Oppo - Popular Models
                {'brand': 'Oppo', 'model': 'Find X7 Ultra'},
                {'brand': 'Oppo', 'model': 'Find X6 Pro'},
                {'brand': 'Oppo', 'model': 'Find X6'},
                {'brand': 'Oppo', 'model': 'Reno 11 Pro'},
                {'brand': 'Oppo', 'model': 'Reno 11'},
                {'brand': 'Oppo', 'model': 'Reno 10 Pro+'},
                
                # Vivo - Popular Models
                {'brand': 'Vivo', 'model': 'X100 Pro'},
                {'brand': 'Vivo', 'model': 'X100'},
                {'brand': 'Vivo', 'model': 'X90 Pro+'},
                {'brand': 'Vivo', 'model': 'X90 Pro'},
                {'brand': 'Vivo', 'model': 'V29 Pro'},
                {'brand': 'Vivo', 'model': 'V29'},
                
                # Realme - Popular Models
                {'brand': 'Realme', 'model': 'GT 5 Pro'},
                {'brand': 'Realme', 'model': 'GT 5'},
                {'brand': 'Realme', 'model': 'GT Neo 5'},
                {'brand': 'Realme', 'model': 'GT Neo 4'},
                {'brand': 'Realme', 'model': 'Number Series'},
            ]
            
            # Add phone types
            for phone_data in default_types:
                phone_type = PhoneType(**phone_data)
                db.session.add(phone_type)
            
            db.session.commit()
            print(f"✅ Successfully restored {len(default_types)} phone types!")
            
            return True
            
        except Exception as e:
            print(f"❌ Error restoring phone types: {str(e)}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    print("📱 Restoring phone types...")
    success = restore_phone_types()
    
    if success:
        print("\n🎉 Phone types restored successfully!")
        print("Dropdown menus will now work with phone brands and models.")
    else:
        print("\n❌ Failed to restore phone types!")
        sys.exit(1)
