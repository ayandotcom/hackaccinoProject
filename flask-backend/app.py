from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
import jwt
import os
from datetime import datetime, timedelta
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')

# Configure CORS with specific origins
allowed_origins = os.getenv('ALLOWED_ORIGINS', '').split(',')
CORS(app, resources={r"/*": {
    "origins": allowed_origins,
    "methods": ["GET", "POST"],
    "allow_headers": ["Content-Type", "Authorization"]
}})

# Configure rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[f"{os.getenv('API_RATE_LIMIT', '100')}/hour"]
)

# JWT Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            token = token.split(' ')[1]  # Remove 'Bearer ' prefix
            data = jwt.decode(token, os.getenv('JWT_SECRET_KEY'), algorithms=["HS256"])
        except:
            return jsonify({'message': 'Token is invalid'}), 401
            
        return f(*args, **kwargs)
    
    return decorated

# Login route
@app.route('/login', methods=['POST'])
@limiter.limit("5/minute")
def login():
    auth = request.authorization
    
    if not auth or not auth.username or not auth.password:
        return jsonify({'message': 'Could not verify'}), 401
    
    # Here you should verify against your user database
    # This is a simplified example
    if auth.username == "user" and auth.password == "password":
        token = jwt.encode({
            'user': auth.username,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, os.getenv('JWT_SECRET_KEY'))
        
        return jsonify({'token': token})
    
    return jsonify({'message': 'Could not verify'}), 401

def run_exercise_safely(exercise_script):
    """Safely execute exercise scripts with proper validation"""
    allowed_scripts = {
        'jumpingjacks.py': 'exercises/jumpingjacks.py',
        'squats.py': 'exercises/squats.py',
        'pushups.py': 'exercises/pushups.py'
    }
    
    if exercise_script not in allowed_scripts:
        raise ValueError("Invalid exercise script")
        
    try:
        result = subprocess.run(
            ['python3', allowed_scripts[exercise_script]], 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            timeout=30  # Set timeout for script execution
        )
        return result.stdout.decode()
    except subprocess.TimeoutExpired:
        raise RuntimeError("Exercise script timed out")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Exercise script failed: {e.stderr.decode()}")

# Exercise routes with authentication and rate limiting
@app.route('/jumpingjacks', methods=['GET'])
@token_required
@limiter.limit("30/minute")
def jumping_jacks():
    try:
        result = run_exercise_safely('jumpingjacks.py')
        return jsonify({'status': 'success', 'data': result}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/squats', methods=['GET'])
@token_required
@limiter.limit("30/minute")
def squats():
    try:
        result = run_exercise_safely('squats.py')
        return jsonify({'status': 'success', 'data': result}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/pushups', methods=['GET'])
@token_required
@limiter.limit("30/minute")
def pushups():
    try:
        result = run_exercise_safely('pushups.py')
        return jsonify({'status': 'success', 'data': result}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/fullworkout', methods=['GET'])
@token_required
@limiter.limit("10/minute")
def full_workout():
    try:
        exercises = ['jumpingjacks.py', 'pushups.py', 'squats.py']
        results = []
        
        for exercise in exercises:
            result = run_exercise_safely(exercise)
            results.append(result)
            
        return jsonify({
            'status': 'success',
            'message': 'Full workout completed',
            'data': results
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Error handlers
@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({'status': 'error', 'message': 'Rate limit exceeded'}), 429

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

if __name__ == '__main__':
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    app.run(
        host='0.0.0.0', 
        port=5001, 
        debug=debug_mode,
        ssl_context='adhoc'  # Enable HTTPS in development
    )
