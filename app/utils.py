
from functools import wraps
from flask import Flask, jsonify, request, make_response
from config import Config

def token_required(f):
    @wraps(f)
    # the new, post-decoration function. Note *args and **kwargs here.
    def decorated(*args, **kwargs):
        token = None

        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        
        if not token:
            return {"status": False, "message": "Token is missing at " + request.url, "data": None}, 401

        if token == Config.TENCOWRY_KEY:
            return f(*args, **kwargs)
        else:
            return {"status": False, "message": "Invalid token at " + request.url, "data": None}, 401

    return decorated
