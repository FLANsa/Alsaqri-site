#!/usr/bin/env python3
"""
Startup script for online deployment
This ensures the database is properly initialized before starting the app
"""

import os
import sqlite3
from app import app, db, User
from werkzeug.security import generate_password_hash

def initialize_database():
    """Initialize the database with proper schema and users"""
    with app.app_context():
        print("Starting database initialization...")
        
        # Get database path
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        if db_path.startswith('/'):
            db_path = db_path[1:]
        
        # Remove existing database if it exists
        if os.path.exists(db_path):
            print(f"Removing existing database: {db_path}")
            os.remove(db_path)
        
        # Create fresh database
        print("Creating fresh database...")
        db.create_all()
        
        # Create admin user
        print("Creating admin user...")
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
        print("Creating limited user...")
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
        
        # Commit changes
        db.session.commit()
        print("Database initialization completed successfully!")
        print("Users created:")
        print("- Admin: admin / admin123")
        print("- Limited: limited / limited123")

if __name__ == '__main__':
    initialize_database()
