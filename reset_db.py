#!/usr/bin/env python3
"""
Database Reset Script for Online Deployment
This script completely resets the database to ensure compatibility
"""

import os
import sqlite3
from app import app, db, User
from werkzeug.security import generate_password_hash

def reset_database():
    """Completely reset the database"""
    with app.app_context():
        print("Starting database reset...")
        
        # Get database path
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        if db_path.startswith('/'):
            db_path = db_path[1:]
        
        # Remove existing database completely
        if os.path.exists(db_path):
            print(f"Removing existing database: {db_path}")
            os.remove(db_path)
        
        # Create fresh database with simple schema
        print("Creating fresh database...")
        db.create_all()
        
        # Check if admin user already exists
        existing_admin = User.query.filter_by(username='admin').first()
        if not existing_admin:
            # Create admin user
            print("Creating admin user...")
            admin = User(
                username='admin',
                password=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin user created: admin / admin123")
        else:
            print("Admin user already exists")
        
        print("Database reset completed successfully!")

if __name__ == '__main__':
    reset_database()
