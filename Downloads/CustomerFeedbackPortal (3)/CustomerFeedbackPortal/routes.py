import os
import qrcode
from io import BytesIO
from werkzeug.utils import secure_filename
from flask import render_template, request, redirect, url_for, flash, jsonify, send_file, Response
from app import app
from models import get_company, get_all_companies, create_company, create_feedback, get_company_feedback

# Configure upload settings
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_logo(file):
    """Process uploaded logo file and return binary data and mimetype"""
    if file and file.filename and allowed_file(file.filename):
        # Read file content as binary data
        logo_data = file.read()
        logo_mimetype = file.mimetype or 'image/jpeg'
        return logo_data, logo_mimetype
    return None, None

@app.route('/')
def index():
    """Home page showing all companies"""
    companies = get_all_companies()
    return render_template('index.html', companies=companies)

@app.route('/admin')
def admin():
    """Admin page for managing companies"""
    companies = get_all_companies()
    return render_template('admin.html', companies=companies)

@app.route('/admin/add_company', methods=['POST'])
def add_company():
    """Add a new company"""
    name = request.form.get('name', '').strip()
    website = request.form.get('website', '').strip()
    google_review_url = request.form.get('google_review_url', '').strip()
    industry = request.form.get('industry', 'general').strip()
    
    if not name:
        flash('Company name is required', 'error')
        return redirect(url_for('admin'))
    
    if website and not website.startswith(('http://', 'https://')):
        website = 'https://' + website
    
    if google_review_url and not google_review_url.startswith(('http://', 'https://')):
        google_review_url = 'https://' + google_review_url
    
    # Handle logo upload
    logo_data, logo_mimetype = None, None
    if 'logo' in request.files:
        logo_file = request.files['logo']
        if logo_file.filename:
            logo_data, logo_mimetype = process_logo(logo_file)
            if logo_data is None:
                flash('Invalid logo file. Please upload PNG, JPG, JPEG, GIF, SVG, or WEBP files only.', 'error')
                return redirect(url_for('admin'))
    
    company = create_company(name, website, google_review_url, industry, logo_data, logo_mimetype)
    
    # Generate QR code
    generate_qr_code(company.id)
    
    flash(f'Company "{name}" added successfully!', 'success')
    return redirect(url_for('admin'))

@app.route('/review/<int:company_id>')
def review_page(company_id):
    """Customer feedback page for a specific company"""
    company = get_company(company_id)
    if not company:
        flash('Company not found', 'error')
        return redirect(url_for('index'))
    
    return render_template('review.html', company=company)

@app.route('/google-style-review/<int:company_id>')
def google_style_review(company_id):
    """Google-style review page for low ratings"""
    company = get_company(company_id)
    if not company:
        flash('Company not found', 'error')
        return redirect(url_for('index'))
    
    return render_template('google_review.html', company=company)

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    """Submit customer feedback"""
    company_id = int(request.form.get('company_id'))
    rating = int(request.form.get('rating'))
    comment = request.form.get('comment', '').strip()
    customer_name = request.form.get('customer_name', '').strip()
    
    company = get_company(company_id)
    if not company:
        return jsonify({'success': False, 'message': 'Company not found'}), 404
    
    # Create feedback
    feedback = create_feedback(company_id, rating, comment, customer_name)
    
    response_data = {
        'success': True,
        'rating': rating,
        'company_name': company.name
    }
    
    # Add Google review URL if rating >= 4
    if rating >= 4:
        response_data['google_review_url'] = company.google_review_url
        response_data['review_message'] = f"I had a great experience with {company.name}! Their service was excellent and I would highly recommend them to others."
    
    return jsonify(response_data)

@app.route('/embed/<int:company_id>')
def embed_reviews(company_id):
    """Embeddable reviews page for company websites"""
    company = get_company(company_id)
    if not company:
        return "Company not found", 404
    
    feedback_list = get_company_feedback(company_id)
    # Filter only positive feedback (rating >= 4) for public display
    positive_feedback = [f for f in feedback_list if f.rating >= 4]
    
    return render_template('embed.html', company=company, feedback=positive_feedback)

@app.route('/qr/<int:company_id>')
def download_qr(company_id):
    """Download QR code for a company"""
    company = get_company(company_id)
    if not company:
        return "Company not found", 404

    # Generate the QR code in memory
    img_io = generate_qr_code(company_id)

    return send_file(
        img_io,
        mimetype='image/png',
        as_attachment=True,
        download_name=f"{company.name}_qr_code.png"
    )

def generate_qr_code(company_id):
    """Generate QR code for a company and return BytesIO stream"""
    # Generate QR code URL
    review_url = url_for('review_page', company_id=company_id, _external=True)

    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(review_url)
    qr.make(fit=True)

    # Create QR code image
    img = qr.make_image(fill_color="black", back_color="white")

    # Save to in-memory file
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)

    return img_io

@app.route('/admin/delete_company/<int:company_id>', methods=['POST'])
def delete_company(company_id):
    """Delete a company and all its related data"""
    from app import db
    
    company = get_company(company_id)
    if not company:
        flash('Company not found', 'error')
        return redirect(url_for('admin'))
    
    company_name = company.name
    
    # Delete logo file if exists
    if company.logo_filename:
        logo_path = os.path.join(UPLOAD_FOLDER, company.logo_filename)
        if os.path.exists(logo_path):
            os.remove(logo_path)
    
    # Delete QR code file if exists
    qr_path = f"static/qr/company_{company_id}.png"
    if os.path.exists(qr_path):
        os.remove(qr_path)
    
    # Delete company (feedback will be deleted automatically due to cascade)
    db.session.delete(company)
    db.session.commit()
    
    flash(f'Company "{company_name}" and all related data deleted successfully!', 'success')
    return redirect(url_for('admin'))

@app.route('/company/<int:company_id>/logo')
def company_logo(company_id):
    """Serve company logo from database"""
    company = get_company(company_id)
    if not company or not company.logo_data:
        # Return a default image or 404
        return '', 404
    
    return Response(
        company.logo_data,
        mimetype=company.logo_mimetype or 'image/jpeg',
        headers={'Cache-Control': 'max-age=3600'}  # Cache for 1 hour
    )

@app.route('/company/<int:company_id>/feedback')
def company_feedback(company_id):
    """Get feedback for a company (JSON API)"""
    company = get_company(company_id)
    if not company:
        return jsonify({'error': 'Company not found'}), 404
    
    feedback_list = get_company_feedback(company_id)
    feedback_data = [f.to_dict() for f in feedback_list]
    
    # Calculate stats
    total_feedback = len(feedback_list)
    avg_rating = sum(f.rating for f in feedback_list) / total_feedback if total_feedback > 0 else 0
    
    return jsonify({
        'company': company.to_dict(),
        'feedback': feedback_data,
        'stats': {
            'total_feedback': total_feedback,
            'average_rating': round(avg_rating, 2)
        }
    })

@app.errorhandler(404)
def not_found(error):
    return render_template('index.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('index.html'), 500
