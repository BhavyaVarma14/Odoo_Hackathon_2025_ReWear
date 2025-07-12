import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the MySQL database
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    raise ValueError("DATABASE_URL environment variable is required")

if database_url.startswith("mysql://"):
    # Replace mysql:// with mysql+pymysql:// for SQLAlchemy
    database_url = database_url.replace("mysql://", "mysql+pymysql://")
    # Ensure SSL is properly configured
    if "ssl-mode=REQUIRED" in database_url:
        database_url = database_url.replace("ssl-mode=REQUIRED", "ssl_disabled=false")

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the app with the extension
db.init_app(app)

# Create tables and import models
with app.app_context():
    import models  # Import models so tables are created
    db.create_all()

# Import routes after app creation
from routes import *


