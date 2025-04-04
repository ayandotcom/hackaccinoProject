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
import hashlib
import secrets

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Ensure all required environment variables are set
required_env_vars = [
    'FLASK_SECRET_KEY',
    'JWT_SECRET_KEY',
    'ALLOWED_ORIGINS',
    'API_RATE_LIMIT',
    'ADMIN_PASSWORD_HASH'
]

for var in required_env_vars:
    if not os.getenv(var):
        raise EnvironmentError(f'Missing required environment variable: {var}')

app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')

# Security headers configuration
SECURITY_HEADERS = {
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'SAMEORIGIN',
    'X-XSS-Protection': '1; mode=block',
    'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'",
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), payment=()',
    'Cache-Control': 'no-store, max-age=0',
    'Server': 'Custom Server',  # Hide server details
}

# Security headers middleware
@app.after_request
def add_security_headers(response):
    """Add security headers to every response"""
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value
    return response

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

def verify_password(stored_hash, password):
    """Securely verify password against stored hash"""
    salt = stored_hash[:32]  # First 32 chars are salt
    stored_hash = stored_hash[32:]
    pwdhash = hashlib.pbkdf2_hmac(
        'sha256', 
        password.encode('utf-8'), 
        salt.encode('utf-8'), 
        100000
    ).hex()
    return pwdhash == stored_hash

# JWT Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            token = token.split(' ')[1]  # Remove 'Bearer ' prefix
            data = jwt.decode(
                token, 
                os.getenv('JWT_SECRET_KEY'), 
                algorithms=["HS256"]
            )
            
            # Check token expiration
            exp = data.get('exp')
            if not exp or datetime.utcnow() > datetime.fromtimestamp(exp):
                return jsonify({'message': 'Token has expired'}), 401
                
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401
        except Exception as e:
            return jsonify({'message': 'Token validation failed'}), 401
            
        return f(*args, **kwargs)
    
    return decorated

def run_exercise_safely(script_name):
    """Safely run exercise scripts with input validation"""
    allowed_scripts = {'jumpingjacks.py', 'pushups.py', 'squats.py'}
    
    if script_name not in allowed_scripts:
        raise ValueError('Invalid exercise script')
        
    try:
        # Run script in a controlled environment
        result = subprocess.run(
            ['python3', f'exercises/{script_name}'],
            capture_output=True,
            text=True,
            timeout=30,  # 30 second timeout
            check=True
        )
        return result.stdout
    except subprocess.TimeoutExpired:
        raise RuntimeError('Exercise script timed out')
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f'Exercise script failed: {e.stderr}')
    except Exception as e:
        raise RuntimeError(f'Error running exercise: {str(e)}')

# Login route
@app.route('/login', methods=['POST'])
@limiter.limit("5/minute")
def login():
    auth = request.authorization
    
    if not auth or not auth.username or not auth.password:
        return jsonify({'message': 'Invalid credentials'}), 401
    
    stored_hash = os.getenv('ADMIN_PASSWORD_HASH')
    if not stored_hash:
        return jsonify({'message': 'Server configuration error'}), 500
    
    if auth.username == "admin" and verify_password(stored_hash, auth.password):
        token = jwt.encode({
            'user': auth.username,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, os.getenv('JWT_SECRET_KEY'))
        
        return jsonify({'token': token})
    
    return jsonify({'message': 'Invalid credentials'}), 401

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
    # In production, use proper SSL certificates
    ssl_context = None
    if os.getenv('FLASK_ENV') == 'production':
        ssl_context = (
            os.getenv('SSL_CERT_PATH'),
            os.getenv('SSL_KEY_PATH')
        )
    
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=debug_mode,
        ssl_context=ssl_context
    )
