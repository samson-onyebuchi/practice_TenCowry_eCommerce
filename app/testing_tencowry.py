# # from functools import wraps
# # from flask import Flask, request, abort
# # from app.utils import *

# # app = Flask(__name__)



# # @app.route('/api/testing_for_access_token', methods=['GET'])
# # @token_required
# # def get_answer():
# #     return jsonify({"status": True, "message": "Access granted to protected route", "data": None}), 200



from flask import Flask, request, make_response
from flask_restful import Api, Resource
from flask_mail import Mail, Message
import random
import os
from pymongo import MongoClient
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt

app = Flask(__name__)
api = Api(app)
bcrypt = Bcrypt()

# Configure email settings
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("EMAIL_PASSWORD")

mail = Mail(app)

# MongoDB connection
mongo_uri = os.getenv("MONGO_URI") 
client = MongoClient(mongo_uri)
db = client['TenCowry']  
registered_emails_collection = db['Users']

otp_storage = {}

# Generate a random 6-digit OTP
def generate_otp():
    return str(random.randint(100000, 999999))

class RequestOTPResource(Resource):
    def post(self):
        data = request.json

        if 'email' not in data:
            return {"status": False, "message": "Email address is required in the payload", "data": None}, 400

        if len(data) > 1:
            return {"status": False, "message": "Only one payload (email) is allowed", "data": None}, 400

        email = data['email']

        if registered_emails_collection.find_one({'email': email}) is None:
            return {"status": False, "message": "Email does not exist", "data": None}, 404

        otp = generate_otp()

        timestamp = datetime.now()
        otp_storage[email] = {'otp': otp, 'timestamp': timestamp}

        msg = Message('Your OTP is {}'.format(otp), sender=os.getenv("MAIL_USERNAME"), recipients=[email])
        mail.send(msg)

        return {"status": True, "message": "OTP sent successfully", "data": None}, 200

api.add_resource(RequestOTPResource, '/api/v1/ecommerce/request-otp')


class VerifyOTPResource(Resource):
    def post(self):
        data = request.json

        if 'email' not in data or 'entered_otp' not in data or 'new_password' not in data:
            return {"status": False, "message": "Email, entered_otp, and new_password are required in the request body", "data": None}, 400

        email = data['email']
        entered_otp = data['entered_otp']
        new_password = generate_password_hash(f"a{data.get('new_password')}z")  # Hash the new password

        user = registered_emails_collection.find_one({'email': email})

        if not user:
            return {"status": False, "message": "User not found", "data": None}, 404

        stored_data = otp_storage.get(email)

        if not stored_data:
            return {"status": False, "message": "OTP not found", "data": None}, 404

        stored_otp = stored_data['otp']
        timestamp = stored_data['timestamp']

        if entered_otp == stored_otp and datetime.now() - timestamp < timedelta(minutes=30):
            user_id = user['_id']
            
            # Update the password with the hashed password
            registered_emails_collection.update_one({'_id': ObjectId(user_id)}, {'$set': {'password': new_password}})

            return {"status": True, "message": "Password updated successfully", "data": None}, 200
        else:
            return {"status": False, "message": "Invalid or expired OTP", "data": None}, 400

api.add_resource(VerifyOTPResource, '/api/v1/ecommerce/verify-otp')


class UpdatePasswordResource(Resource):
    def put(self):
        # Get user input from request
        email = request.json.get('email')
        old_password = request.json.get('old_password')
        new_password = request.json.get('new_password')

        # Retrieve user from the database based on email
        user = registered_emails_collection.find_one({'email': email})

        # Check if the user exists
        if user is None:
            response = {"status": False, "message": "User not found", "data": None}
            return make_response(response, 404)

        # Check if the old password matches the stored hash
        stored_hash = user['password']
        input_hash = generate_password_hash(f"a{old_password}z")

        if not check_password_hash(stored_hash, input_hash):
            response = {"status": False, "message": "Incorrect old password", "data": None}
            return make_response(response, 400)

        # Hash the new password before updating
        hashed_new_password = generate_password_hash(f"a{new_password}z")

        # Update the password in the database
        registered_emails_collection.update_one({'email': email}, {'$set': {'password': hashed_new_password}})

        response = {"status": True, "message": "Password updated successfully", "data": None}
        return make_response(response, 200)

# Add the resource to the API with a specified endpoint
api.add_resource(UpdatePasswordResource, '/update_password')