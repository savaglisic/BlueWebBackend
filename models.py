from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy (db) instance here, but actual app configuration happens in main file
db = SQLAlchemy()

# Define the User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # Increased size to 255

# Define the EmailWhitelist model
class EmailWhitelist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)

# Define the Rank model
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

# Define the Yield model
class Yield(db.Model):
    __tablename__ = 'yield'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cumulative = db.Column(db.Float, nullable=True)
    genotype = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(50), nullable=True)
    season = db.Column(db.String(10), nullable=True)

# Define the Score model
class Score(db.Model):
    __tablename__ = 'scores'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    flavor_mean = db.Column(db.Float, nullable=True)
    genotype = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(50), nullable=True)
    season = db.Column(db.String(10), nullable=True)

# Define the Fruit Quality (FQ) model
class FQ(db.Model):
    __tablename__ = 'fruit_quality'
    
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
