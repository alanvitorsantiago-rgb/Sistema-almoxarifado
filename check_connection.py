
from app import app, db, User
import os

with app.app_context():
    try:
        print(f"Testing connection to: {app.config['SQLALCHEMY_DATABASE_URI'].split('@')[1]}") # Print host only
        user_count = User.query.count()
        print(f"✅ Connection Successful!")
        print(f"Found {user_count} users in the database.")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
