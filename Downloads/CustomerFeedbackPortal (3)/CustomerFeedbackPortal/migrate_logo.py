#!/usr/bin/env python3
"""
Database migration script to add logo_filename column
"""
from app import app, db

def add_logo_column():
    with app.app_context():
        try:
            # Add the logo_filename column to the companies table
            with db.engine.connect() as connection:
                print("Adding logo_filename column to companies table...")
                connection.execute(db.text("ALTER TABLE companies ADD COLUMN logo_filename VARCHAR(255) DEFAULT NULL"))
                connection.commit()
                print("Column added successfully!")
                
                # Verify the new column exists
                print("\nUpdated Companies table structure:")
                result = connection.execute(db.text("DESCRIBE companies"))
                for row in result:
                    print(f"  {row}")
                    
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("Column already exists, skipping...")
            else:
                print(f"Error adding column: {e}")
                raise

if __name__ == "__main__":
    add_logo_column()