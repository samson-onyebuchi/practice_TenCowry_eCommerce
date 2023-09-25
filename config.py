import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

# creating a configuration class
class Config(object):    
    TENCOWRY_KEY = os.environ.get('TENCOWRY_KEY')
    

