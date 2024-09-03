from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# SQLAlchemy Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://devuser:Sava2290!@localhost:3306/blueweb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database connection
db = SQLAlchemy(app)

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

    
@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({"message": "Test successful"}), 200

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


