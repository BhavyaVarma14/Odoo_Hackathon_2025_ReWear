"""
Add industry column to existing companies table
"""
from app import app, db
from sqlalchemy import text

def add_industry_column():
    """Add industry column to companies table"""
    with app.app_context():
        try:
            # Add industry column if it doesn't exist
            db.session.execute(text("ALTER TABLE companies ADD COLUMN industry VARCHAR(100) DEFAULT 'general'"))
            db.session.commit()
            print("Added industry column to companies table")
            
            # Update existing companies based on their names
            updates = [
                ("Camp Dilly", "resort"),
                ("Camp Unity", "resort"), 
                ("Dilly's Veg Kitchen", "food")
            ]
            
            for company_name, industry in updates:
                result = db.session.execute(
                    text("UPDATE companies SET industry = :industry WHERE name = :name"),
                    {"industry": industry, "name": company_name}
                )
                if result.rowcount > 0:
                    print(f"Updated {company_name} to {industry} industry")
                else:
                    print(f"Company {company_name} not found")
            
            db.session.commit()
            print("Industry column migration completed!")
            
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("Industry column already exists")
            else:
                print(f"Error: {e}")
                db.session.rollback()

if __name__ == "__main__":
    add_industry_column()