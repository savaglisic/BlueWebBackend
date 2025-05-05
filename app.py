import csv
from datetime import datetime
from difflib import get_close_matches
import io
from zoneinfo import ZoneInfo
from flask import Flask, Response, make_response, request, jsonify, stream_with_context
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
from models import APIKey, Genotype, OptionConfig, db, User, EmailWhitelist, Rank, Yield, Score, FQ , PlantData
from functools import wraps
import os
from sqlalchemy import Integer, case, desc, func, or_

app = Flask(__name__)
CORS(app)

db_user = os.environ.get('DB_USER', 'devuser')
db_password = os.environ.get('DB_PASS', 'Sava2290!')
db_host = os.environ.get('DB_HOST', 'localhost')
db_name = os.environ.get('DB_NAME', 'blueweb')

app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+mysqlconnector://devuser:Sava2290!@localhost:3306/blueweb"
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

@app.route('/option_config/<int:id>', methods=['PUT'])
def update_option_config(id):
    data = request.json
    option_text = data.get('option_text')

    if not option_text:
        return jsonify({'status': 'error', 'message': 'option_text is required'}), 400

    option = OptionConfig.query.filter_by(id=id).first()

    if not option:
        return jsonify({'status': 'error', 'message': 'OptionConfig not found'}), 404

    option.option_text = option_text
    db.session.commit()

    return jsonify({'status': 'success', 'message': 'OptionConfig updated successfully'}), 200

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

    if not barcode:
        return jsonify({'status': 'error', 'message': 'Barcode is required.'}), 400

    barcode = barcode.strip()

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
    
    barcode = barcode.strip()

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
    
@app.route('/delete_plant_data', methods=['DELETE'])
def delete_plant_data():
    data = request.json
    barcode = data.get('barcode')

    if not barcode:
        return jsonify({'status': 'error', 'message': 'Barcode is required.'}), 400

    try:
        # Find the plant record by barcode
        plant_data = PlantData.query.filter_by(barcode=barcode).first()

        if plant_data:
            db.session.delete(plant_data)
            db.session.commit()
            return jsonify({'status': 'success', 'message': 'Plant data deleted successfully!'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Plant data not found.'}), 404

    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 400


from flask import request, jsonify
from sqlalchemy import or_

@app.route('/get_plant_data', methods=['GET'])
def get_plant_data():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    import json
    filters_str = request.args.get('filters', '[]')
    try:
        filters = json.loads(filters_str)
    except:
        filters = []

    query = PlantData.query

    includes_list = []
    excludes_list = []

    for f in filters:
        field = f.get('field', '').strip()
        operator = f.get('operator', 'includes')
        value = f.get('value', '').strip()

        if not field or not value:
            # Skip invalid filters
            continue

        if not hasattr(PlantData, field):
            # Skip unknown fields
            continue

        col = getattr(PlantData, field)

        if operator == 'includes':
            includes_list.append(col.ilike(f"%{value}%"))
        elif operator == 'excludes':
            excludes_list.append(col.ilike(f"%{value}%"))

    # Apply include filters (OR condition)
    if includes_list:
        query = query.filter(or_(*includes_list))
    
    # Apply exclude filters (negated OR condition)
    if excludes_list:
        query = query.filter(~or_(*excludes_list))

    # 🔥 Apply default sorting by timestamp (newest first)
    query = query.order_by(PlantData.timestamp.desc())

    # Paginate results
    paginated_result = query.paginate(page=page, per_page=per_page, error_out=False)

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
            'box': plant.box,
            'week': plant.week,
            'timestamp': plant.timestamp, 
            'fruitfirm_timestamp': plant.fruitfirm_timestamp
        }

    plant_data_list = [serialize_plant_data(p) for p in paginated_result.items]
    
    response = {
        'total': paginated_result.total,
        'pages': paginated_result.pages,
        'current_page': paginated_result.page,
        'per_page': paginated_result.per_page,
        'has_next': paginated_result.has_next,
        'has_prev': paginated_result.has_prev,
        'results': plant_data_list,
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

    # Ensure barcode exists and clean the input
    barcode = data.get('barcode')
    if not barcode:
        return jsonify({'status': 'error', 'message': 'Barcode is required.'}), 400

    barcode = barcode.strip()  # Trim spaces

    # Normalize other received fields (trim spaces if string, keep None values)
    avg_firmness = data.get('avg_firmness')
    avg_diameter = data.get('avg_diameter')
    sd_firmness = data.get('sd_firmness')
    sd_diameter = data.get('sd_diameter')

    # Ensure at least one relevant field is provided
    if all(value is None for value in [avg_firmness, avg_diameter, sd_firmness, sd_diameter]):
        return jsonify({'status': 'error', 'message': 'At least one of avg_firmness, avg_diameter, sd_firmness, or sd_diameter is required.'}), 400

    try:
        # Check if barcode exists and update instead of inserting a duplicate
        plant_data = PlantData.query.filter(PlantData.barcode == barcode).first()

        if plant_data:
            # Update only fields that were provided (ignore None values)
            if avg_firmness is not None:
                plant_data.avg_firmness = avg_firmness
            if avg_diameter is not None:
                plant_data.avg_diameter = avg_diameter
            if sd_firmness is not None:
                plant_data.sd_firmness = sd_firmness
            if sd_diameter is not None:
                plant_data.sd_diameter = sd_diameter

            eastern_time = datetime.now(ZoneInfo("America/New_York"))
            plant_data.fruitfirm_timestamp = eastern_time
            db.session.commit()
            return jsonify({'status': 'success', 'message': 'Plant firmness and diameter data updated successfully!'}), 200
        else:
            # Insert a new plant data record safely
            eastern_time = datetime.now(ZoneInfo("America/New_York"))
            new_plant_data = PlantData(
                barcode=barcode,
                avg_firmness=avg_firmness,
                avg_diameter=avg_diameter,
                sd_firmness=sd_firmness,
                sd_diameter=sd_diameter,
                fruitfirm_timestamp=eastern_time
            )

            db.session.add(new_plant_data)
            db.session.commit()
            return jsonify({'status': 'success', 'message': 'New plant data created successfully!'}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 400
    
@app.route('/download_plant_data_csv', methods=['GET'])
def download_plant_data_csv():
    def generate_csv():
        # Create an in-memory text stream for CSV data
        data = io.StringIO()
        writer = csv.writer(data)
        # Define the CSV header (adjust field names as needed)
        header = [
            'id', 'barcode', 'genotype', 'stage', 'site', 'block', 'project',
            'post_harvest', 'bush_plant_number', 'notes', 'mass', 'x_berry_mass',
            'number_of_berries', 'ph', 'brix', 'juicemass', 'tta', 'mladded',
            'avg_firmness', 'avg_diameter', 'sd_firmness', 'sd_diameter', 'box',
            'week', 'timestamp', 'fruitfirm_timestamp'
        ]
        writer.writerow(header)
        # Yield the header row
        yield data.getvalue()
        data.seek(0)
        data.truncate(0)
        
        # Get total count for progress tracking (if needed for logging)
        total = PlantData.query.count()
        count = 0
        
        # Use yield_per to avoid loading the entire table into memory at once
        query = PlantData.query.yield_per(100)
        for plant in query:
            row = [
                plant.id,
                plant.barcode,
                plant.genotype,
                plant.stage,
                plant.site,
                plant.block,
                plant.project,
                plant.post_harvest,
                plant.bush_plant_number,
                plant.notes,
                plant.mass,
                plant.x_berry_mass,
                plant.number_of_berries,
                plant.ph,
                plant.brix,
                plant.juicemass,
                plant.tta,
                plant.mladded,
                plant.avg_firmness,
                plant.avg_diameter,
                plant.sd_firmness,
                plant.sd_diameter,
                plant.box,
                plant.week,
                plant.timestamp,
                plant.fruitfirm_timestamp
            ]
            writer.writerow(row)
            count += 1

            # Optionally, log progress to the server console
            if count % 100 == 0:
                app.logger.info(f"Processed {count} of {total} records")
            
            # Yield the current chunk of CSV data
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)
    
    headers = {
        "Content-Disposition": "attachment; filename=plant_data.csv",
        "Content-Type": "text/csv"
    }
    return Response(stream_with_context(generate_csv()), headers=headers)


@app.route('/download_yield', methods=['GET'])
def download_yield():
    # 1. Pull out distinct weeks, ordered
    weeks = [w for (w,) in
             db.session.query(PlantData.week)
                       .distinct()
                       .order_by(PlantData.week)
                       .all()]

    # 2. Exclude week 100 and build aggregates
    pivot_weeks = [w for w in weeks if w != 100]
    week_aggregates = [
        func.sum(
            case(
                (PlantData.week == week, PlantData.mass.cast(Integer)),
                else_=0
            )
        ).label(f"Week{week}")
        for week in pivot_weeks
    ]
    total_mass = func.sum(PlantData.mass.cast(Integer)).label("TotalMass")

    # 3. Execute the query, excluding null/empty genotypes
    qry = (
        db.session
          .query(
              PlantData.genotype,
              PlantData.site,
              *week_aggregates,
              total_mass
          )
          .filter(
              PlantData.genotype.isnot(None),
              PlantData.genotype != ''
          )
          .group_by(PlantData.genotype, PlantData.site)
          .order_by(desc("TotalMass"))
    )
    rows = qry.all()

    # 4. Build DataFrame manually
    columns = ["genotype", "site"] + [f"Week{w}" for w in pivot_weeks] + ["TotalMass"]
    df = pd.DataFrame(rows, columns=columns)

    # 5. Write out CSV to a StringIO buffer
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    # 6. Send as CSV attachment
    resp = make_response(csv_buffer.getvalue())
    resp.headers['Content-Disposition'] = 'attachment; filename=yield_data.csv'
    resp.headers['Content-Type'] = 'text/csv'
    return resp


@app.route('/pivot_fruit_quality', methods=['GET'])
def pivot_fruit_quality():
    # Pagination & search params
    page      = int(request.args.get('page', 1))
    page_size = int(request.args.get('pageSize', 10))
    search    = request.args.get('search', '').strip()

    # 1. Get weeks and build aggregates
    weeks = [w for (w,) in
             db.session.query(PlantData.week)
                       .distinct()
                       .order_by(PlantData.week)
                       .all()]
    pivot_weeks = [w for w in weeks if w != 100]
    week_aggregates = [
        func.sum(
            case(
                (PlantData.week == week, PlantData.mass.cast(Integer)),
                else_=0
            )
        ).label(f"Week{week}")
        for week in pivot_weeks
    ]
    total_mass = func.sum(PlantData.mass.cast(Integer)).label("TotalMass")

    # 2. Base query (exclude null/empty genotypes)
    base_q = (
        db.session
          .query(
              PlantData.genotype,
              PlantData.site,
              *week_aggregates,
              total_mass
          )
          .filter(
              PlantData.genotype.isnot(None),
              PlantData.genotype != ''
          )
    )

    # 3. Apply search filter if present
    if search:
        base_q = base_q.filter(PlantData.genotype.ilike(f"%{search}%"))

    # 4. Count distinct (genotype, site) for pagination
    count_q = (
        db.session
          .query(PlantData.genotype, PlantData.site)
          .filter(
              PlantData.genotype.isnot(None),
              PlantData.genotype != ''
          )
          .distinct()
    )
    if search:
        count_q = count_q.filter(PlantData.genotype.ilike(f"%{search}%"))
    total_rows = db.session.query(func.count()).select_from(count_q.subquery()).scalar()

    # 5. Apply ordering, LIMIT/OFFSET
    results = (
        base_q.group_by(PlantData.genotype, PlantData.site)
              .order_by(desc("TotalMass"))
              .limit(page_size)
              .offset((page - 1) * page_size)
              .all()
    )

    # 6. Serialize rows into dicts
    columns = ["genotype", "site"] + [f"Week{w}" for w in pivot_weeks] + ["TotalMass"]
    data = [dict(zip(columns, row)) for row in results]

    return jsonify({
        "data":  data,
        "total": total_rows
    })

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
    app.run(debug=True, port=5001)


