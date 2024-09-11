import json
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Flask app and SQLAlchemy setup
app = Flask(__name__)

# SQLAlchemy configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://devuser:Sava2290!@localhost:3306/blueweb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define the Score table model
class Score(db.Model):
    __tablename__ = 'fq_scores'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    avg_firm = db.Column(db.Float, nullable=True)
    avg_size = db.Column(db.Float, nullable=True)
    brix = db.Column(db.Float, nullable=True)
    genotype = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(50), nullable=True)
    ph = db.Column(db.Float, nullable=True)
    season = db.Column(db.String(10), nullable=True)
    tta = db.Column(db.Float, nullable=True)
    weight = db.Column(db.Float, nullable=True)

# Function to parse and load JSON data into MySQL
def load_json_to_db(json_file):
    with open(json_file) as f:
        data = json.load(f)
    
    for entry in data:
        # Handle missing or empty fields
        avg_firm = float(entry.get('avg_firm', 0) or 0)
        avg_size = float(entry.get('avg_size', 0) or 0)
        brix = float(entry.get('brix', 0) or 0)
        genotype = entry.get('genotype', '')
        location = entry.get('location', '')
        ph = float(entry.get('ph', 0) or 0)
        season = entry.get('season', '')
        tta = float(entry.get('tta', 0) or 0) if entry.get('tta') else None
        weight = float(entry.get('weight', 0) or 0)
        
        # Create a new Score object
        score = Score(
            avg_firm=avg_firm,
            avg_size=avg_size,
            brix=brix,
            genotype=genotype,
            location=location,
            ph=ph,
            season=season,
            tta=tta,
            weight=weight
        )
        
        # Add the score object to the database session
        db.session.add(score)
    
    # Commit all the changes to the database
    db.session.commit()

# Create the database table
with app.app_context():
    db.create_all()  # Create the table if it doesn't exist

    # Load data from scores.json to the MySQL database
    load_json_to_db('scores.json')

    print("Data has been loaded into the MySQL database.")
