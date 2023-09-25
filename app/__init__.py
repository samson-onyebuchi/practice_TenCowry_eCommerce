import os
from dotenv import load_dotenv
from flask import Flask
from config import Config
from flask_pymongo import PyMongo
from flask_restful import Api
from flask_cors import CORS


basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

#Initialise Flask
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config.from_object(Config)

# api = Api(app)
# CORS(app)
# mongo = PyMongo(app, Config.MONGO_URI)

# Local base url
#base_url = Config.BASE_URL

from app.testing_tencowry import app