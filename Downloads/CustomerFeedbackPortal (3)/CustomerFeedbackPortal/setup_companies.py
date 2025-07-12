"""
Setup script to create the initial companies with proper industry categories
"""
from app import app, db
from models import Company, create_company

def setup_companies():
    """Create the test companies with proper industry categories"""
    
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Check if companies already exist
        existing_companies = Company.query.all()
        if existing_companies:
            print(f"Found {len(existing_companies)} existing companies")
            for company in existing_companies:
                print(f"- {company.name} (industry: {getattr(company, 'industry', 'not set')})")
            return
        
        # Create the test companies
        companies_data = [
            {
                "name": "Camp Dilly",
                "website": "https://campdilly.com",
                "google_review_url": "https://g.page/r/campdilly",
                "industry": "resort"
            },
            {
                "name": "Camp Unity", 
                "website": "https://campunity.com",
                "google_review_url": "https://g.page/r/campunity",
                "industry": "resort"
            },
            {
                "name": "Dilly's Veg Kitchen",
                "website": "https://dillysvegkitchen.com", 
                "google_review_url": "https://g.page/r/dillysvegkitchen",
                "industry": "food"
            }
        ]
        
        for company_data in companies_data:
            try:
                company = create_company(
                    name=company_data["name"],
                    website=company_data["website"],
                    google_review_url=company_data["google_review_url"],
                    industry=company_data["industry"]
                )
                print(f"Created company: {company.name} ({company.industry})")
            except Exception as e:
                print(f"Error creating company {company_data['name']}: {e}")
        
        print("Company setup completed!")

if __name__ == "__main__":
    setup_companies()