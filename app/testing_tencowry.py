from functools import wraps
from flask import Flask, request, abort
from app.utils import *

app = Flask(__name__)



@app.route('/api/testing_for_access_token', methods=['GET'])
@token_required
def get_answer():
    return jsonify({"status": True, "message": "Access granted to protected route", "data": None}), 200



