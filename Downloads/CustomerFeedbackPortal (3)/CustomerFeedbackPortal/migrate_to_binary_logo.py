#!/usr/bin/env python3
"""
Database migration script to change from logo_filename to binary logo storage
"""
from app import app, db

def migrate_to_binary_logo():
    with app.app_context():
        try:
            with db.engine.connect() as connection:
                print("Migrating from logo_filename to binary logo storage...")
                
                # Check current structure
                result = connection.execute(db.text("DESCRIBE companies"))
                columns = [row[0] for row in result]
                print(f"Current columns: {columns}")
                
                # Drop the old logo_filename column if it exists
                if 'logo_filename' in columns:
                    print("Dropping logo_filename column...")
                    connection.execute(db.text("ALTER TABLE companies DROP COLUMN logo_filename"))
                
                # Add new logo columns if they don't exist
                if 'logo_data' not in columns:
                    print("Adding logo_data column...")
                    connection.execute(db.text("ALTER TABLE companies ADD COLUMN logo_data LONGBLOB"))
                
                if 'logo_mimetype' not in columns:
                    print("Adding logo_mimetype column...")
                    connection.execute(db.text("ALTER TABLE companies ADD COLUMN logo_mimetype VARCHAR(100)"))
                
                connection.commit()
                print("Migration completed successfully!")
                
                # Show final structure
                print("\nFinal table structure:")
                result = connection.execute(db.text("DESCRIBE companies"))
                for row in result:
                    print(f"  {row}")
                    
        except Exception as e:
            print(f"Error during migration: {e}")
            raise

if __name__ == "__main__":
    migrate_to_binary_logo()