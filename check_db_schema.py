#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from database import SessionLocal

load_dotenv()

def check_db_schema():
    engine = create_engine(os.getenv("DATABASE_URL"))
    with engine.connect() as conn:
        # Check templates table schema
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'templates' ORDER BY ordinal_position;"))
        print("Templates table columns:")
        for row in result:
            print(f"  - {row[0]}")

        # Check if templates table has data
        result = conn.execute(text("SELECT COUNT(*) FROM templates;"))
        count = result.fetchone()[0]
        print(f"Templates table has {count} rows")

        # Check campaigns table schema
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'campaigns' ORDER BY ordinal_position;"))
        print("\nCampaigns table columns:")
        for row in result:
            print(f"  - {row[0]}")

        # Check email_logs table schema
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'email_logs' ORDER BY ordinal_position;"))
        print("\nEmail_logs table columns:")
        for row in result:
            print(f"  - {row[0]}")

if __name__ == "__main__":
    check_db_schema()