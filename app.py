import datetime
from difflib import get_close_matches
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
from models import APIKey, Genotype, OptionConfig, db, User, EmailWhitelist, Rank, Yield, Score, FQ , PlantData
from functools import wraps

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
            password=generate_password_hash(new_password),
            user_group='ops'
        )
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'status': 'user_created_successfully'}), 201
    
@app.route('/get_user_group', methods=['GET'])
def get_user_group():
    email = request.args.get('email').lower()  # Retrieve email from query parameters and normalize it
    user = User.query.filter_by(email=email).first()
    if user:
        return jsonify({'status': 'success', 'user_group': user.user_group}), 200
    else:
        return jsonify({'status': 'user_not_found'}), 404
  
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
                    'box': plant_data.box,
                    'barcode': plant_data.barcode
                }
            }), 200
        else:
            return jsonify({'status': 'not_found'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

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
            # List of fields that can be updated
            fields = [
                'genotype', 'stage', 'site', 'block', 'project', 'post_harvest',
                'bush_plant_number', 'notes', 'mass', 'x_berry_mass', 'number_of_berries',
                'ph', 'brix', 'juicemass', 'tta', 'mladded', 'avg_firmness',
                'avg_diameter', 'sd_firmness', 'sd_diameter', 'box'
            ]

            # Update only the fields provided in the request data
            for field in fields:
                if field in data and data[field] is not None:
                    setattr(plant_data, field, data[field])

            db.session.commit()
            return jsonify({'status': 'success', 'message': 'Plant data updated successfully!'}), 200
        else:
            # Create a new plant record
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
                box=data.get('box')
            )

            db.session.add(new_plant_data)
            db.session.commit()
            return jsonify({'status': 'success', 'message': 'New plant data created successfully!'}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 400
    
@app.route('/get_plant_data', methods=['GET'])
def get_plant_data():
    # Retrieve query parameters for pagination
    page = request.args.get('page', 1, type=int)  # Default page number is 1
    per_page = request.args.get('per_page', 10, type=int)  # Default items per page is 10

    # Optional search parameters
    genotype = request.args.get('genotype')
    barcode = request.args.get('barcode')
    stage = request.args.get('stage')
    site = request.args.get('site')
    block = request.args.get('block')
    project = request.args.get('project')
    post_harvest = request.args.get('post_harvest')

    # Base query
    query = PlantData.query

    # Apply filters based on search parameters
    if genotype:
        query = query.filter(PlantData.genotype.ilike(f"%{genotype}%"))
    if barcode:
        query = query.filter(PlantData.genotype.ilike(f"%{barcode}%"))
    if stage:
        query = query.filter(PlantData.stage.ilike(f"%{stage}%"))
    if site:
        query = query.filter(PlantData.site.ilike(f"%{site}%"))
    if block:
        query = query.filter(PlantData.block.ilike(f"%{block}%"))
    if project:
        query = query.filter(PlantData.project.ilike(f"%{project}%"))
    if post_harvest:
        query = query.filter(PlantData.post_harvest.ilike(f"%{post_harvest}%"))

    # Apply pagination
    paginated_result = query.paginate(page=page, per_page=per_page, error_out=False)

    # Serialize the results
    def serialize_plant_data(plant):
        return {
            'id': plant.id,
            'barcode': plant.barcode,
            'genotype': plant.genotype,
            'stage': plant.stage,
            'site': plant.site,
            'block': plant.block,
            'project': plant.project,
            'post_harvest': plant.post_harvest,
            'bush_plant_number': plant.bush_plant_number,
            'notes': plant.notes,
            'mass': plant.mass,
            'x_berry_mass': plant.x_berry_mass,
            'number_of_berries': plant.number_of_berries,
            'ph': plant.ph,
            'brix': plant.brix,
            'juicemass': plant.juicemass,
            'tta': plant.tta,
            'mladded': plant.mladded,
            'avg_firmness': plant.avg_firmness,
            'avg_diameter': plant.avg_diameter,
            'sd_firmness': plant.sd_firmness,
            'sd_diameter': plant.sd_diameter,
            'box': plant.box
        }

    # Collect the data and metadata for pagination
    plant_data_list = [serialize_plant_data(plant) for plant in paginated_result.items]
    response = {
        'total': paginated_result.total,
        'pages': paginated_result.pages,
        'current_page': paginated_result.page,
        'per_page': paginated_result.per_page,
        'has_next': paginated_result.has_next,
        'has_prev': paginated_result.has_prev,
        'results': plant_data_list
    }

    return jsonify(response), 200
    
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
    
def validate_api_key(fn):
    @wraps(fn)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-KEY')
        if not api_key:
            return jsonify({'status': 'error', 'message': 'API key is missing.'}), 403

        # Check if the API key is valid
        key_record = APIKey.query.filter_by(key=api_key).first()
        if not key_record:
            return jsonify({'status': 'error', 'message': 'Invalid API key.'}), 403

        db.session.commit()

        return fn(*args, **kwargs)

    return decorated
    
@app.route('/fruit_firm', methods=['POST'])
@validate_api_key
def fruit_firm():
    data = request.json
    barcode = data.get('barcode')

    if not barcode:
        return jsonify({'status': 'error', 'message': 'Barcode is required.'}), 400

    # Extract the firmness and diameter fields from the request data
    avg_firmness = data.get('avg_firmness')
    avg_diameter = data.get('avg_diameter')
    sd_firmness = data.get('sd_firmness')
    sd_diameter = data.get('sd_diameter')

    # Check that at least one of the required fields is provided
    if avg_firmness is None and avg_diameter is None and sd_firmness is None and sd_diameter is None:
        return jsonify({'status': 'error', 'message': 'At least one of avg_firmness, avg_diameter, sd_firmness, or sd_diameter is required.'}), 400

    try:
        # Check if a plant with the given barcode already exists
        plant_data = PlantData.query.filter_by(barcode=barcode).first()

        if plant_data:
            # Update only the firmness and diameter fields provided in the request data
            if avg_firmness is not None:
                plant_data.avg_firmness = avg_firmness
            if avg_diameter is not None:
                plant_data.avg_diameter = avg_diameter
            if sd_firmness is not None:
                plant_data.sd_firmness = sd_firmness
            if sd_diameter is not None:
                plant_data.sd_diameter = sd_diameter

            db.session.commit()
            return jsonify({'status': 'success', 'message': 'Plant firmness and diameter data updated successfully!'}), 200
        else:
            # Create a new plant record with only the barcode and firmness/diameter fields
            new_plant_data = PlantData(
                barcode=barcode,
                avg_firmness=avg_firmness,
                avg_diameter=avg_diameter,
                sd_firmness=sd_firmness,
                sd_diameter=sd_diameter
            )

            db.session.add(new_plant_data)
            db.session.commit()
            return jsonify({'status': 'success', 'message': 'New plant data created successfully with firmness and diameter information!'}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 400

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
        OptionConfig.initialize_defaults()
    app.run(debug=True, port=5000)


