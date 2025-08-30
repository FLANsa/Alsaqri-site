#!/usr/bin/env python3
"""
Script to delete all phone types from the database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, PhoneType

def delete_all_phone_types():
    """Delete all phone types from the database"""
    with app.app_context():
        try:
            # Get count of phone types
            count = PhoneType.query.count()
            print(f"📱 Found {count} phone types in database")
            
            if count == 0:
                print("✅ No phone types to delete")
                return True
            
            # Delete all phone types
            print("🗑️ Deleting all phone types...")
            PhoneType.query.delete()
            db.session.commit()
            
            print(f"✅ Successfully deleted {count} phone types!")
            print("📱 Phone types table is now empty")
            
            return True
            
        except Exception as e:
            print(f"❌ Error deleting phone types: {str(e)}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    print("🗑️ Deleting all phone types...")
    success = delete_all_phone_types()
    
    if success:
        print("\n🎉 Phone types deleted successfully!")
        print("The add phone forms will now use manual input instead of dropdowns.")
    else:
        print("\n❌ Failed to delete phone types!")
        sys.exit(1)
