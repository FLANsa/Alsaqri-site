#!/usr/bin/env python3
"""
Script to add manaf user to the database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User
from werkzeug.security import generate_password_hash

def add_manaf_user():
    """Add manaf user to the database"""
    with app.app_context():
        try:
            # Check if manaf user already exists
            existing_user = User.query.filter_by(username='manaf').first()
            if existing_user:
                print("✅ User 'manaf' already exists!")
                return True
            
            # Create manaf user
            manaf_user = User(
                username='manaf',
                password=generate_password_hash('manaf123'),
                is_admin=True
            )
            
            db.session.add(manaf_user)
            db.session.commit()
            
            print("✅ User 'manaf' created successfully!")
            print("   Username: manaf")
            print("   Password: manaf123")
            print("   Admin: Yes")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating manaf user: {str(e)}")
            return False

if __name__ == "__main__":
    print("👤 Adding manaf user...")
    success = add_manaf_user()
    
    if success:
        print("\n🎉 Manaf user added successfully!")
    else:
        print("\n❌ Failed to add manaf user!")
        sys.exit(1)
