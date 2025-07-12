"""
Data models for the feedback system using SQLAlchemy.
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from app import db

class Company(db.Model):
    """Company model for storing company information"""
    __tablename__ = 'companies'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    website = db.Column(db.String(255))
    google_review_url = db.Column(db.String(255))
    industry = db.Column(db.String(100), default='general')  # 'food', 'resort', 'general'
    logo_data = db.Column(db.LargeBinary)
    logo_mimetype = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to feedback
    feedback = db.relationship('Feedback', backref='company', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'website': self.website,
            'google_review_url': self.google_review_url,
            'industry': self.industry,
            'has_logo': self.logo_data is not None,
            'logo_mimetype': self.logo_mimetype,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Feedback(db.Model):
    """Feedback model for storing customer feedback"""
    __tablename__ = 'feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    customer_name = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'company_id': self.company_id,
            'rating': self.rating,
            'comment': self.comment,
            'customer_name': self.customer_name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# Storage utilities using SQLAlchemy
def get_company(company_id: int) -> Optional[Company]:
    """Get company by ID"""
    return Company.query.get(company_id)

def get_all_companies() -> List[Company]:
    """Get all companies"""
    return Company.query.order_by(Company.created_at.desc()).all()

def create_company(name: str, website: str, google_review_url: str, industry: str = 'general', logo_data: Optional[bytes] = None, logo_mimetype: Optional[str] = None) -> Company:
    """Create a new company"""
    from app import db
    
    company = Company(
        name=name,
        website=website,
        google_review_url=google_review_url,
        industry=industry,
        logo_data=logo_data,
        logo_mimetype=logo_mimetype
    )
    
    db.session.add(company)
    db.session.commit()
    
    return company

def create_feedback(company_id: int, rating: int, comment: str = "", customer_name: str = "") -> Feedback:
    """Create new feedback"""
    from app import db
    
    feedback = Feedback(
        company_id=company_id,
        rating=rating,
        comment=comment,
        customer_name=customer_name
    )
    
    db.session.add(feedback)
    db.session.commit()
    
    return feedback

def get_company_feedback(company_id: int) -> List[Feedback]:
    """Get all feedback for a company"""
    return Feedback.query.filter_by(company_id=company_id).order_by(Feedback.created_at.desc()).all()
