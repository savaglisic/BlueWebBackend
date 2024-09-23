from difflib import get_close_matches
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
from models import Genotype, OptionConfig, db, User, EmailWhitelist, Rank, Yield, Score, FQ , PlantData

app = Flask(__name__)
CORS(app)

# SQLAlchemy Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://devuser:Sava2290!@localhost:3306/blueweb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database connection
db.init_app(app)  # Use the db instance from models.py

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email').lower()
    password = data.get('password')

    # Check if the email is in the whitelist
    whitelisted_email = EmailWhitelist.query.filter_by(email=email).first()

    if not whitelisted_email:
        return jsonify({'status': 'email_not_whitelisted'}), 400

    # Check if the user exists and the password is correct
    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password, password):
        return jsonify({'status': 'login_successful'}), 200
    elif user:
        return jsonify({'status': 'incorrect_password'}), 401
    else:
        # Email is whitelisted but no user exists, prompt for account creation
        return jsonify({'status': 'user_not_found_but_whitelisted'}), 200

@app.route('/update_user', methods=['PUT'])
def update_user():
    data = request.json
    email = data.get('email').lower()  # Normalize email to lowercase
    new_user_name = data.get('user_name')
    new_password = data.get('password')

    # Check if the email is in the whitelist
    whitelisted_email = EmailWhitelist.query.filter_by(email=email).first()
    if not whitelisted_email:
        return jsonify({'status': 'email_not_whitelisted'}), 400

    # Check if the user exists
    user = User.query.filter_by(email=email).first()
    if user:
        # Update existing user
        user.user_name = new_user_name if new_user_name else user.user_name
        if new_password:
            user.password = generate_password_hash(new_password)
        db.session.commit()
        return jsonify({'status': 'update_successful'}), 200
    else:
        # Create a new user
        if not new_user_name or not new_password:
            return jsonify({'status': 'missing_user_info'}), 400
        
        new_user = User(
            user_name=new_user_name,
            email=email,
            password=generate_password_hash(new_password)
        )
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'status': 'user_created_successfully'}), 201
  
@app.route('/search_genotype', methods=['GET'])
def search_genotype():
    # Get the search term from the request arguments
    genotype_query = request.args.get('genotype', '').lower()

    if not genotype_query:
        return jsonify({"error": "Genotype parameter is missing"}), 400

    # Using SQLAlchemy's ilike for case-insensitive partial matching
    search_pattern = f"%{genotype_query}%"

    # Query each table for matching genotype
    rank_results = Rank.query.filter(Rank.genotype.ilike(search_pattern)).all()
    yield_results = Yield.query.filter(Yield.genotype.ilike(search_pattern)).all()
    score_results = Score.query.filter(Score.genotype.ilike(search_pattern)).all()
    fq_results = FQ.query.filter(FQ.genotype.ilike(search_pattern)).all()

    # Helper function to serialize a model instance into a dictionary
    def serialize_model(model):
        # Use Python-friendly attribute names, especially for columns with special characters
        serialized_data = {}
        for column in model.__table__.columns:
            # Use the attribute key that maps to the column in the database
            column_name = column.key
            serialized_data[column_name] = getattr(model, column_name)
        return serialized_data

    # Serialize the results
    rank_data = [serialize_model(r) for r in rank_results]
    yield_data = [serialize_model(y) for y in yield_results]
    score_data = [serialize_model(s) for s in score_results]
    fq_data = [serialize_model(f) for f in fq_results]

    # Combine all results into one response
    response_data = {
        "rank_results": rank_data,
        "yield_results": yield_data,
        "score_results": score_data,
        "fq_results": fq_data
    }

    return jsonify(response_data), 200

@app.route('/populate_genotypes', methods=['POST'])
def populate_genotypes():
    # Get distinct genotypes from each table
    rank_genotypes = db.session.query(Rank.genotype).distinct()
    yield_genotypes = db.session.query(Yield.genotype).distinct()
    score_genotypes = db.session.query(Score.genotype).distinct()
    fq_genotypes = db.session.query(FQ.genotype).distinct()

    # Combine all genotypes into a set to remove duplicates
    all_genotypes = set()
    all_genotypes.update([r.genotype for r in rank_genotypes])
    all_genotypes.update([y.genotype for y in yield_genotypes])
    all_genotypes.update([s.genotype for s in score_genotypes])
    all_genotypes.update([f.genotype for f in fq_genotypes])

    # Insert unique genotypes into the Genotypes table
    for genotype_str in all_genotypes:
        if not Genotype.query.filter_by(genotype=genotype_str).first():
            new_genotype = Genotype(genotype=genotype_str)
            db.session.add(new_genotype)

    db.session.commit()

    return jsonify({"message": "Genotypes table populated with unique values"}), 201

@app.route('/email_whitelist', methods=['GET'])
def get_email_whitelist():
    emails = EmailWhitelist.query.with_entities(EmailWhitelist.email).all()
    email_list = [email[0] for email in emails]   
    return jsonify({'emails': email_list}), 200

@app.route('/email_whitelist', methods=['POST'])
def add_email_to_whitelist():
    data = request.json
    email = data.get('email')

    if not email:
        return jsonify({'status': 'error', 'message': 'Email is required'}), 400

    existing_email = EmailWhitelist.query.filter_by(email=email).first()
    if existing_email:
        return jsonify({'status': 'error', 'message': 'Email already whitelisted'}), 400

    new_email = EmailWhitelist(email=email)
    db.session.add(new_email)
    db.session.commit()

    return jsonify({'status': 'success', 'message': 'Email added to whitelist'}), 201

@app.route('/email_whitelist/<string:email>', methods=['DELETE'])
def delete_email_from_whitelist(email):
    email_record = EmailWhitelist.query.filter_by(email=email).first()

    if not email_record:
        return jsonify({'status': 'error', 'message': 'Email not found in whitelist'}), 404

    db.session.delete(email_record)
    db.session.commit()

    return jsonify({'status': 'success', 'message': 'Email removed from whitelist'}), 200

@app.route('/option_config/<int:id>', methods=['DELETE'])
def delete_option_config(id):
    option = OptionConfig.query.filter_by(id=id).first()

    if not option:
        return jsonify({'status': 'error', 'message': 'OptionConfig not found'}), 404

    db.session.delete(option)
    db.session.commit()

    return jsonify({'status': 'success', 'message': 'OptionConfig deleted successfully'}), 200

@app.route('/option_config', methods=['GET'])
def get_option_configs():
    options = OptionConfig.query.all()
    options_list = [
        {
            'id': option.id,
            'option_type': option.option_type,
            'option_text': option.option_text
        } for option in options
    ]
    
    return jsonify({'options': options_list}), 200

@app.route('/option_config', methods=['POST'])
def add_option_config():
    data = request.json
    option_type = data.get('option_type')
    option_text = data.get('option_text')

    if not option_type or not option_text:
        return jsonify({'status': 'error', 'message': 'option_type and option_text are required'}), 400

    new_option = OptionConfig(option_type=option_type, option_text=option_text)
    db.session.add(new_option)
    db.session.commit()

    return jsonify({'status': 'success', 'id': new_option.id, 'message': 'OptionConfig added successfully'}), 201

@app.route('/add_plant_data', methods=['POST'])
def add_plant_data():
    data = request.json
    barcode = data.get('barcode')

    if not barcode:
        return jsonify({'status': 'error', 'message': 'Barcode is required.'}), 400

    try:
        # Check if a plant with the given barcode already exists
        plant_data = PlantData.query.filter_by(barcode=barcode).first()

        if plant_data:
            # Update the existing plant entry
            plant_data.genotype = data.get('genotype')
            plant_data.stage = data.get('stage')
            plant_data.site = data.get('site')
            plant_data.block = data.get('block')
            plant_data.project = data.get('project')
            plant_data.post_harvest = data.get('post_harvest')
            plant_data.bush_plant_number = data.get('bush_plant_number')
            plant_data.notes = data.get('notes')
            plant_data.mass = data.get('mass')
            plant_data.x_berry_mass = data.get('x_berry_mass')
            plant_data.number_of_berries = data.get('number_of_berries')
            plant_data.ph = data.get('ph')
            plant_data.brix = data.get('brix')
            plant_data.juicemass = data.get('juicemass')
            plant_data.tta = data.get('tta')
            plant_data.mladded = data.get('mladded')
            plant_data.avg_firmness = data.get('avg_firmness')
            plant_data.avg_diameter = data.get('avg_diameter')
            plant_data.sd_firmness = data.get('sd_firmness')
            plant_data.sd_diameter = data.get('sd_diameter')
            plant_data.box = data.get('box')

            db.session.commit()

            return jsonify({'status': 'success', 'message': 'Plant data updated successfully!'}), 200
        else:
            new_plant_data = PlantData(
                barcode=barcode,
                genotype=data.get('genotype'),
                stage=data.get('stage'),
                site=data.get('site'),
                block=data.get('block'),
                project=data.get('project'),
                post_harvest=data.get('post_harvest'),
                bush_plant_number=data.get('bush_plant_number'),
                notes=data.get('notes'),
                mass=data.get('mass'),
                x_berry_mass=data.get('x_berry_mass'),
                number_of_berries=data.get('number_of_berries'),
                ph=data.get('ph'),
                brix=data.get('brix'),
                juicemass=data.get('juicemass'),
                tta=data.get('tta'),
                mladded=data.get('mladded'),
                avg_firmness=data.get('avg_firmness'),
                avg_diameter=data.get('avg_diameter'),
                sd_firmness=data.get('sd_firmness'),
                sd_diameter=data.get('sd_diameter'),
                box=data.get('box'),
            )

            db.session.add(new_plant_data)
            db.session.commit()

            return jsonify({'status': 'success', 'message': 'Plant data added successfully!'}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 400
    
@app.route('/check_barcode', methods=['POST'])
def check_barcode():
    barcode = request.json.get('barcode')
    try:
        plant_data = PlantData.query.filter_by(barcode=barcode).first()
        if plant_data:
            return jsonify({
                'status': 'success',
                'data': {
                    'genotype': plant_data.genotype,
                    'stage': plant_data.stage,
                    'site': plant_data.site,
                    'block': plant_data.block,
                    'project': plant_data.project,
                    'post_harvest': plant_data.post_harvest,
                    'bush_plant_number': plant_data.bush_plant_number,
                    'notes': plant_data.notes,
                    'mass': plant_data.mass,
                    'number_of_berries': plant_data.number_of_berries,
                    'x_berry_mass' : plant_data.x_berry_mass,
                    'ph': plant_data.ph,
                    'brix': plant_data.brix,
                    'juicemass': plant_data.juicemass,
                    'tta': plant_data.tta,
                    'mladded': plant_data.mladded,
                    'avg_firmness': plant_data.avg_firmness,
                    'avg_diameter': plant_data.avg_diameter,
                    'sd_firmness': plant_data.sd_firmness,
                    'sd_diameter': plant_data.sd_diameter,
                    'box': plant_data.box
                }
            }), 200
        else:
            return jsonify({'status': 'not_found'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
@app.route('/spell_check', methods=['POST'])
def spell_check():
    data = request.get_json()
    input_string = data.get('input_string', '')

    if not input_string:
        return jsonify({"error": "Input string is required"}), 400

    exact_match = Genotype.query.filter(db.func.lower(Genotype.genotype) == input_string.lower()).first()

    if exact_match:
        return jsonify({"message": "Exact match found", "genotype": exact_match.genotype}), 200

    all_genotypes = [genotype.genotype for genotype in Genotype.query.all()]

    closest_matches = get_close_matches(input_string, all_genotypes, n=1, cutoff=0.6)

    if closest_matches:
        return jsonify({"message": "Partial match found", "genotype": closest_matches[0], "note": "Partial match"}), 200
    else:
        return jsonify({"message": "No match found"}), 404

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

if __name__ == '__main__':
    # Use the app context to avoid "Working outside of application context" errors
    with app.app_context():
        db.create_all()  # Create the database tables if they don't exist
    app.run(debug=True, port=5000)


