#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base, User
from passlib.context import CryptContext

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def create_test_user():
    # Create tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # List all existing users
        all_users = db.query(User).all()
        print("Existing users:")
        for user in all_users:
            print(f"  Username: {user.username}, Email: {user.email}, Role: {user.role}")

        # Check if admin user exists
        admin_user = db.query(User).filter(User.username == "admin").first()
        if admin_user:
            print("Admin user already exists")
            # Update password to ensure it's correct
            admin_user.hashed_password = get_password_hash("admin123")
            db.commit()
            print("Admin password updated")
        else:
            # Create admin user
            admin_password = get_password_hash("admin123")
            admin_user = User(
                username="admin",
                email="admin@example.com",
                hashed_password=admin_password,
                role="admin"
            )
            db.add(admin_user)
            db.commit()
            print("Admin user created")

        print("Login credentials:")
        print("Admin: admin / admin123")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()