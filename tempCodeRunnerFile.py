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