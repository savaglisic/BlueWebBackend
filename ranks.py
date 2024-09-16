import json
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Flask app and SQLAlchemy setup
app = Flask(__name__)

# SQLAlchemy configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://devuser:Sava2290!@localhost:3306/blueweb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define the Rank table model based on the JSON structure
class Rank(db.Model):
    __tablename__ = 'ranks'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Flavor_Mean_plus = db.Column(db.Float, nullable=True)
    Selection_Index_2022 = db.Column(db.Float, nullable=True)
    Yield_Greens_plus = db.Column(db.Float, nullable=True)
    avg_firm_plus = db.Column(db.Float, nullable=True)
    brix_plus = db.Column(db.Float, nullable=True)
    genotype = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(50), nullable=True)
    ph_plus = db.Column(db.Float, nullable=True)
    ranking_SI22 = db.Column(db.Float, nullable=True)
    rkn_Flavor_Mean_plus = db.Column(db.Float, nullable=True)
    rkn_Yield_Greens_plus = db.Column(db.Float, nullable=True)
    rkn_avg_firm_plus = db.Column(db.Float, nullable=True)
    rkn_brix_plus = db.Column(db.Float, nullable=True)
    rkn_ph_plus = db.Column(db.Float, nullable=True)
    rkn_weight_plus = db.Column(db.Float, nullable=True)
    season = db.Column(db.String(10), nullable=True)
    weight_plus = db.Column(db.Float, nullable=True)

# Function to parse and load JSON data into MySQL
def load_json_to_db(json_file):
    with open(json_file) as f:
        data = json.load(f)
    
    for entry in data:
        # Parse each field with appropriate type conversion
        Flavor_Mean_plus = float(entry.get('Flavor_Mean(+)') or 0)
        Selection_Index_2022 = float(entry.get('Selection Index 2022') or 0)
        Yield_Greens_plus = float(entry.get('Yield_Greens(+)') or 0)
        avg_firm_plus = float(entry.get('avg_firm(+)') or 0)
        brix_plus = float(entry.get('brix(+)') or 0)
        genotype = entry.get('genotype', '')
        location = entry.get('location', '')
        ph_plus = float(entry.get('ph(+)') or 0)
        ranking_SI22 = float(entry.get('ranking_SI22') or 0)
        rkn_Flavor_Mean_plus = float(entry.get('rkn_Flavor_Mean(+)') or 0)
        rkn_Yield_Greens_plus = float(entry.get('rkn_Yield_Greens(+)') or 0)
        rkn_avg_firm_plus = float(entry.get('rkn_avg_firm(+)') or 0)
        rkn_brix_plus = float(entry.get('rkn_brix(+)') or 0)
        rkn_ph_plus = float(entry.get('rkn_ph(+)') or 0)
        rkn_weight_plus = float(entry.get('rkn_weight(+)') or 0)
        season = entry.get('season', '')
        weight_plus = float(entry.get('weight(+)') or 0)
        
        # Create a new Rank object
        rank = Rank(
            Flavor_Mean_plus=Flavor_Mean_plus,
            Selection_Index_2022=Selection_Index_2022,
            Yield_Greens_plus=Yield_Greens_plus,
            avg_firm_plus=avg_firm_plus,
            brix_plus=brix_plus,
            genotype=genotype,
            location=location,
            ph_plus=ph_plus,
            ranking_SI22=ranking_SI22,
            rkn_Flavor_Mean_plus=rkn_Flavor_Mean_plus,
            rkn_Yield_Greens_plus=rkn_Yield_Greens_plus,
            rkn_avg_firm_plus=rkn_avg_firm_plus,
            rkn_brix_plus=rkn_brix_plus,
            rkn_ph_plus=rkn_ph_plus,
            rkn_weight_plus=rkn_weight_plus,
            season=season,
            weight_plus=weight_plus
        )
        
        # Add the rank object to the database session
        db.session.add(rank)
    
    # Commit all the changes to the database
    db.session.commit()

# Create the database table
with app.app_context():
    db.create_all()  # Create the table if it doesn't exist

    # Load data from ranks.json to the MySQL database
    load_json_to_db('ranks.json')

    print("Data has been loaded into the MySQL database.")





