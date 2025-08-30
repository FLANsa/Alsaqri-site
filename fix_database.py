#!/usr/bin/env python3
"""
Script to fix database schema issues
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
import sqlite3

def fix_database_schema():
    """Fix database schema issues"""
    with app.app_context():
        try:
            # Connect to the database
            db_path = 'instance/phone_shop.db'
            
            # Create a backup
            import shutil
            if os.path.exists(db_path):
                shutil.copy2(db_path, db_path + '.backup')
                print("✅ Database backup created")
            
            # Drop all tables and recreate them
            print("🗑️ Dropping all tables...")
            db.drop_all()
            
            print("🏗️ Creating new tables...")
            db.create_all()
            
            print("👤 Creating admin users...")
            from app import create_admin_user, create_default_phone_types, create_default_accessory_categories
            
            create_admin_user()
            create_default_phone_types()
            create_default_accessory_categories()
            
            print("✅ Database schema fixed successfully!")
            print("📊 Database now has:")
            print("   - Updated Transaction table with date_created column")
            print("   - All phone types and categories")
            print("   - Admin users: admin/admin123 and manaf/manaf123")
            
        except Exception as e:
            print(f"❌ Error fixing database: {str(e)}")
            return False
    
    return True

if __name__ == "__main__":
    print("🔧 Fixing database schema...")
    success = fix_database_schema()
    
    if success:
        print("\n🎉 Database fixed successfully!")
        print("You can now run the application without errors.")
    else:
        print("\n❌ Failed to fix database!")
        sys.exit(1)
