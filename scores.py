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
    __tablename__ = 'scores'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    flavor_mean = db.Column(db.Float, nullable=True)
    genotype = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(50), nullable=True)
    season = db.Column(db.String(10), nullable=True)

# Function to parse and load JSON data into MySQL
def load_json_to_db(json_file):
    with open(json_file) as f:
        data = json.load(f)
    
    for entry in data:
        # Parse fields from the JSON file
        flavor_mean = float(entry.get('Flavor_Mean', 0) or 0)
        genotype = entry.get('genotype', '')
        location = entry.get('location', '')
        season = entry.get('season', '')
        
        # Create a new Score object
        score = Score(
            flavor_mean=flavor_mean,
            genotype=genotype,
            location=location,
            season=season
        )
        
        # Add the score object to the database session
        db.session.add(score)
    
    # Commit all the changes to the database
    db.session.commit()

# Create the database table and load data
with app.app_context():
    db.create_all()  # Create the table if it doesn't exist

    # Load data from scores.json to the MySQL database
    load_json_to_db('scores.json')

    print("Data has been loaded into the MySQL database.")
