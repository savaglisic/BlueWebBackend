from app import app, db
from models import EmailWhitelist, OptionConfig

# Create the tables and initialize defaults
with app.app_context():
    db.create_all()
    OptionConfig.initialize_defaults()
    EmailWhitelist.initialize_defaults()