"""
Database migration script to add industry column to companies table
"""
import os
from sqlalchemy import create_engine, text

def add_industry_column():
    """Add industry column to companies table and update existing companies"""
    
    # Get database URL
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("Error: DATABASE_URL environment variable not set")
        return False
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Add industry column
            try:
                conn.execute(text("ALTER TABLE companies ADD COLUMN industry VARCHAR(100) DEFAULT 'general'"))
                print("Added industry column to companies table")
            except Exception as e:
                if "Duplicate column name" in str(e) or "already exists" in str(e):
                    print("Industry column already exists")
                else:
                    raise e
            
            # Update existing companies based on their names
            updates = [
                ("Camp Dilly", "resort"),
                ("Camp Unity", "resort"), 
                ("Dilly's Veg Kitchen", "food")
            ]
            
            for company_name, industry in updates:
                result = conn.execute(
                    text("UPDATE companies SET industry = :industry WHERE name = :name"),
                    {"industry": industry, "name": company_name}
                )
                if result.rowcount > 0:
                    print(f"Updated {company_name} to {industry} industry")
                else:
                    print(f"Company {company_name} not found")
            
            conn.commit()
            print("Migration completed successfully!")
            return True
            
    except Exception as e:
        print(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    add_industry_column()