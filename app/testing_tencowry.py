# from functools import wraps
# from flask import Flask, request, abort
# from app.utils import *

# app = Flask(__name__)



# @app.route('/api/testing_for_access_token', methods=['GET'])
# @token_required
# def get_answer():
#     return jsonify({"status": True, "message": "Access granted to protected route", "data": None}), 200



# from flask import Flask, request
# from flask_restful import Api, Resource
# from werkzeug.security import generate_password_hash, check_password_hash
# from pymongo import MongoClient
# import pymongo
# import os

# app = Flask(__name__)
# api = Api(app)


# client = pymongo.MongoClient(os.getenv("MONGO_URI"))
# db = client["TenCowry"]
# users_collection = db["Users"]

# class ChangePasswordResource(Resource):
#     def post(self):
#         data = request.get_json()

#         email = data.get('email')
#         current_password = data.get('currentPassword')
#         new_password = data.get('newPassword')

#         if not email or not current_password or not new_password:
#             return {"error": "Missing required fields"}, 400

#         user = users_collection.find_one({"email": email})

#         try:
#             if user:
#                 stored_hashed_password = user["password"]

#                 if check_password_hash(stored_hashed_password, current_password):
#                     hashed_new_password = generate_password_hash(f"a{new_password}z")

#                     users_collection.update_one({"email": user["email"]}, {"$set": {"password": hashed_new_password}})
#                     return {"message": "Password changed successfully"}
#                 else:
#                     return {"error": "Invalid current password"}, 401
#             else:
#                 return {"error": "Invalid email"}, 401
#         except Exception as e:            
#             return {"error": "Internal Server Error"}, 500
# api.add_resource(ChangePasswordResource, '/api/v1/ecommerce/change-password')


from flask import Flask, request
from flask_restful import Api, Resource
from flask_mail import Mail, Message
import random
import os
from pymongo import MongoClient
from datetime import datetime, timedelta

app = Flask(__name__)
api = Api(app)

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
            return {'error': 'Email address is required'}, 400

        email = data['email']

        # Check if the email exists in the MongoDB collection
        if registered_emails_collection.find_one({'email': email}) is None:
            return {'error': 'Email does not exist'}, 404

        otp = generate_otp()

        timestamp = datetime.now()
        otp_storage[email] = {'otp': otp, 'timestamp': timestamp}

        # Send OTP via email
        msg = Message('Your OTP is {}'.format(otp), sender=os.getenv("MAIL_USERNAME"), recipients=[email])
        mail.send(msg)

        return {'message': 'OTP sent successfully'}, 200
api.add_resource(RequestOTPResource, '/api/v1/ecommerce/request-otp')


class VerifyOTPResource(Resource):
    def post(self):
        data = request.json

        if 'email' not in data or 'entered_otp' not in data:
            return {'error': 'Email and entered_otp are required in the request body'}, 400

        email = data['email']
        entered_otp = data['entered_otp']

        stored_data = otp_storage.get(email)

        if not stored_data:
            return {'error': 'OTP not found'}, 404

        stored_otp = stored_data['otp']
        timestamp = stored_data['timestamp']

        if entered_otp == stored_otp and datetime.now() - timestamp < timedelta(minutes=30):
            return {'message': 'OTP is valid'}, 200
        else:
            return {'error': 'Invalid or expired OTP'}, 400

api.add_resource(VerifyOTPResource, '/api/v1/ecommerce/verify-otp')