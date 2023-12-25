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
from bson.objectid import ObjectId

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
        new_password = data['new_password']

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
            registered_emails_collection.update_one({'_id': ObjectId(user_id)}, {'$set': {'password': new_password}})

            return {"status": True, "message": "Password updated successfully", "data": None}, 200
        else:
            return {"status": False, "message": "Invalid or expired OTP", "data": None}, 400

api.add_resource(VerifyOTPResource, '/api/v1/ecommerce/verify-otp')


