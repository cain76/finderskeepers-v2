#!/usr/bin/env python3
"""
Initialize PostgreSQL database schema
"""

import psycopg2
import os

# Database connection parameters
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "finderskeepers_v2",
    "user": "finderskeepers",
    "password": "fk2025secure"
}

def init_database():
    """Initialize database with schema from init.sql"""
    try:
        # Read the initialization script
        with open('config/pgvector/init.sql', 'r') as f:
            init_sql = f.read()
        
        # Connect to PostgreSQL
        print("🔗 Connecting to PostgreSQL...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Execute the initialization script
        print("📊 Executing database initialization script...")
        cursor.execute(init_sql)
        
        # Commit changes
        conn.commit()
        print("✅ Database schema initialized successfully!")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

if __name__ == "__main__":
    success = init_database()
    if success:
        print("\n🎉 PostgreSQL database ready for use!")
    else:
        print("\n❌ Database initialization failed!")