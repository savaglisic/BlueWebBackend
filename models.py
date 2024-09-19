import datetime
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

class PlantData(db.Model):
    __tablename__ = 'plant_data'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    barcode = db.Column(db.String(100), nullable=False)  
    genotype = db.Column(db.String(100), nullable=True) 
    stage = db.Column(db.String(50), nullable=True)  
    site = db.Column(db.String(50), nullable=True)  
    block = db.Column(db.String(50), nullable=True)  
    project = db.Column(db.String(50), nullable=True)  
    post_harvest = db.Column(db.String(50), nullable=True)  
    bush_plant_number = db.Column(db.String(100), nullable=True)  
    notes = db.Column(db.String(255), nullable=True)  
    mass = db.Column(db.Float, nullable=True)  
    number_of_berries = db.Column(db.Integer, nullable=True)
    box = db.Column(db.Integer, nullable=True)    
    bush = db.Column(db.Integer, nullable=True)  
    ph = db.Column(db.Float, nullable=True)
    brix = db.Column(db.Float, nullable=True)
    juicemass = db.Column(db.Float, nullable=True)
    tta = db.Column(db.Float, nullable=True)
    mladded = db.Column(db.Float, nullable=True)
    avg_firmness = db.Column(db.Float, nullable=True)
    avg_diameter = db.Column(db.Float, nullable=True)
    sd_firmness = db.Column(db.Float, nullable=True)
    sd_diameter = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now, nullable=False)
    week = db.Column(db.Integer, nullable=False, default=lambda: datetime.datetime.now().isocalendar()[1])

    def __init__(self, barcode, genotype, stage=None, site=None, block=None, project=None, post_harvest=None, bush_plant_number=None, notes=None, mass=None, number_of_berries=None, ph=None, brix=None, juicemass=None, tta=None, mladded=None, avg_diamater=None, avg_firmness=None, sd_firmness=None, sd_diamater=None, box=None, bush=None):
        self.barcode = barcode
        self.genotype = genotype
        self.stage = stage
        self.site = site
        self.block = block
        self.project = project
        self.post_harvest = post_harvest
        self.bush_plant_number = bush_plant_number
        self.notes = notes
        self.mass = mass
        self.number_of_berries = number_of_berries
        self.ph = ph
        self.brix = brix
        self.juicemass = juicemass
        self.tta = tta
        self.mladded = mladded
        self.avg_firmness = avg_firmness
        self.avg_diameter = avg_diamater
        self.sd_firmness = sd_firmness
        self.sd_diameter = sd_diamater
        box = box
        bush = bush
        self.timestamp = datetime.datetime.now()
        self.week = datetime.datetime.now().isocalendar()[1]

