#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

def migrate_database():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is required")
    
    if not database_url.startswith(('postgresql://', 'sqlite://')):
        raise ValueError("DATABASE_URL must be a valid PostgreSQL or SQLite connection string")
    
    engine = create_engine(database_url)
    with engine.connect() as conn:
        try:
            # Add missing columns to templates table
            print("Adding created_at and updated_at columns to templates table...")
            conn.execute(text("ALTER TABLE templates ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;"))
            conn.execute(text("ALTER TABLE templates ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;"))

            # Add user_id column to email_logs table
            print("Adding user_id column to email_logs table...")
            conn.execute(text("ALTER TABLE email_logs ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id);"))

            # Make campaign_id nullable since individual emails don't have campaigns
            print("Making campaign_id nullable in email_logs table...")
            conn.execute(text("ALTER TABLE email_logs ALTER COLUMN campaign_id DROP NOT NULL;"))

            print("Migration completed successfully!")

            # Verify the changes
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'templates' ORDER BY ordinal_position;"))
            print("\nUpdated templates table columns:")
            for row in result:
                print(f"  - {row[0]}")

            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'email_logs' ORDER BY ordinal_position;"))
            print("\nUpdated email_logs table columns:")
            for row in result:
                print(f"  - {row[0]}")
            
            # Commit after successful verification
            conn.commit()

        except Exception as e:
            print(f"Migration failed: {e}")
            conn.rollback()

if __name__ == "__main__":
    migrate_database()