import json
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Flask app and SQLAlchemy setup
app = Flask(__name__)

# SQLAlchemy configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://devuser:Sava2290!@localhost:3306/blueweb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define the Yield table model
class Yield(db.Model):
    __tablename__ = 'yield'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cumulative = db.Column(db.Float, nullable=True)
    genotype = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(50), nullable=True)
    season = db.Column(db.String(10), nullable=True)

# Function to parse and load JSON data into MySQL
def load_yield_json_to_db(json_file):
    with open(json_file) as f:
        data = json.load(f)
    
    for entry in data:
        # Parse fields from the JSON file
        cumulative = float(entry.get('cumulative', 0) or 0)
        genotype = entry.get('genotype', '')
        location = entry.get('location', '')
        season = entry.get('season', '')
        
        # Create a new Yield object
        yield_data = Yield(
            cumulative=cumulative,
            genotype=genotype,
            location=location,
            season=season
        )
        
        # Add the yield_data object to the database session
        db.session.add(yield_data)
    
    # Commit all the changes to the database
    db.session.commit()

# Create the database table and load data
with app.app_context():
    db.create_all()  # Create the table if it doesn't exist

    # Load data from yield.json to the MySQL database
    load_yield_json_to_db('yield.json')

    print("Yield data has been loaded into the MySQL database.")
