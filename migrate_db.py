#!/usr/bin/env python3
"""
Database Migration Script
This script handles database schema updates for the online deployment.
"""

import sqlite3
import os
from app import app, db, User
from werkzeug.security import generate_password_hash

def migrate_database():
    """Migrate the database to include new user role columns"""
    with app.app_context():
        # Get the database path
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        if db_path.startswith('/'):
            db_path = db_path[1:]
        
        # Check if database exists
        if not os.path.exists(db_path):
            print("Database doesn't exist, creating new one...")
            db.create_all()
            create_users()
            return
        
        # Connect to existing database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Check if new columns exist
            cursor.execute("PRAGMA table_info(user)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Add missing columns
            if 'role' not in columns:
                print("Adding 'role' column...")
                cursor.execute("ALTER TABLE user ADD COLUMN role TEXT DEFAULT 'user'")
            
            if 'can_access_dashboard' not in columns:
                print("Adding 'can_access_dashboard' column...")
                cursor.execute("ALTER TABLE user ADD COLUMN can_access_dashboard BOOLEAN DEFAULT 1")
            
            if 'can_add_phones' not in columns:
                print("Adding 'can_add_phones' column...")
                cursor.execute("ALTER TABLE user ADD COLUMN can_add_phones BOOLEAN DEFAULT 1")
            
            if 'can_add_accessories' not in columns:
                print("Adding 'can_add_accessories' column...")
                cursor.execute("ALTER TABLE user ADD COLUMN can_add_accessories BOOLEAN DEFAULT 1")
            
            if 'can_create_sales' not in columns:
                print("Adding 'can_create_sales' column...")
                cursor.execute("ALTER TABLE user ADD COLUMN can_create_sales BOOLEAN DEFAULT 1")
            
            if 'can_view_reports' not in columns:
                print("Adding 'can_view_reports' column...")
                cursor.execute("ALTER TABLE user ADD COLUMN can_view_reports BOOLEAN DEFAULT 1")
            
            conn.commit()
            print("Database migration completed successfully!")
            
            # Update existing users
            update_existing_users()
            
        except Exception as e:
            print(f"Migration error: {e}")
            # If migration fails, recreate the database
            print("Recreating database...")
            conn.close()
            os.remove(db_path)
            db.create_all()
            create_users()
        finally:
            conn.close()

def update_existing_users():
    """Update existing users with proper roles"""
    with app.app_context():
        # Update admin user
        admin = User.query.filter_by(username='admin').first()
        if admin:
            admin.role = 'admin'
            admin.is_admin = True
            admin.can_access_dashboard = True
            admin.can_add_phones = True
            admin.can_add_accessories = True
            admin.can_create_sales = True
            admin.can_view_reports = True
            print("Updated admin user")
        
        # Create limited user if it doesn't exist
        limited = User.query.filter_by(username='limited').first()
        if not limited:
            limited = User(
                username='limited',
                password=generate_password_hash('limited123'),
                is_admin=False,
                role='limited',
                can_access_dashboard=False,
                can_add_phones=True,
                can_add_accessories=True,
                can_create_sales=True,
                can_view_reports=False
            )
            db.session.add(limited)
            print("Created limited user")
        
        db.session.commit()

def create_users():
    """Create initial users"""
    with app.app_context():
        # Create admin user
        admin = User(
            username='admin',
            password=generate_password_hash('admin123'),
            is_admin=True,
            role='admin',
            can_access_dashboard=True,
            can_add_phones=True,
            can_add_accessories=True,
            can_create_sales=True,
            can_view_reports=True
        )
        db.session.add(admin)
        
        # Create limited user
        limited = User(
            username='limited',
            password=generate_password_hash('limited123'),
            is_admin=False,
            role='limited',
            can_access_dashboard=False,
            can_add_phones=True,
            can_add_accessories=True,
            can_create_sales=True,
            can_view_reports=False
        )
        db.session.add(limited)
        
        db.session.commit()
        print("Created admin and limited users")

if __name__ == '__main__':
    migrate_database()
