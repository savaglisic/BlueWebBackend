from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
from models import db, User, EmailWhitelist, Rank, Yield, Score, FQ  # Import models from models.py

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


