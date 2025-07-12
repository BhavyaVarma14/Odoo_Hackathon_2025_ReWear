#!/usr/bin/env python3
"""
Database setup script to create tables in MySQL database
"""
from app import app, db
from models import Company, Feedback

def setup_database():
    with app.app_context():
        try:
            # Check if tables exist and show their structure
            print("Checking database connection...")
            
            # Try to query existing tables
            with db.engine.connect() as connection:
                result = connection.execute(db.text("SHOW TABLES"))
                existing_tables = [row[0] for row in result]
                print(f"Existing tables: {existing_tables}")
                
                # If tables exist, check their structure
                if 'companies' in existing_tables:
                    print("\nCompanies table structure:")
                    result = connection.execute(db.text("DESCRIBE companies"))
                    for row in result:
                        print(f"  {row}")
                
                if 'feedback' in existing_tables:
                    print("\nFeedback table structure:")
                    result = connection.execute(db.text("DESCRIBE feedback"))
                    for row in result:
                        print(f"  {row}")
            
            # Drop existing tables if they have wrong structure
            print("\nDropping existing tables...")
            db.drop_all()
            
            # Create all tables with correct structure
            print("Creating new tables...")
            db.create_all()
            
            print("Database setup completed successfully!")
            
            # Show new table structure
            with db.engine.connect() as connection:
                print("\nNew Companies table structure:")
                result = connection.execute(db.text("DESCRIBE companies"))
                for row in result:
                    print(f"  {row}")
                    
                print("\nNew Feedback table structure:")
                result = connection.execute(db.text("DESCRIBE feedback"))
                for row in result:
                    print(f"  {row}")
                
        except Exception as e:
            print(f"Error setting up database: {e}")
            raise

if __name__ == "__main__":
    setup_database()