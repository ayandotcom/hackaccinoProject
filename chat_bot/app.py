from flask import Flask, request, jsonify
from flask_cors import CORS
import tensorflow as tf
import pickle
import numpy as np
from keras.preprocessing.sequence import pad_sequences
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

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
    "methods": ["POST"],
    "allow_headers": ["Content-Type"]
}})

# Load the trained model and tokenizer
try:
    model = tf.keras.models.load_model('fitness_classifier.h5')
    with open('tokenizer.pkl', 'rb') as f:
        tokenizer = pickle.load(f)
except Exception as e:
    print(f"Error loading model or tokenizer: {e}")
    model = None
    tokenizer = None

goal_labels = {
    0: 'weight_loss',
    1: 'muscle_gain',
    2: 'endurance',
    3: 'flexibility',
    4: 'maintenance'
}

def validate_numeric_input(value, min_val, max_val, field_name):
    """Validate numeric input within acceptable range"""
    try:
        num_val = float(value)
        if not min_val <= num_val <= max_val:
            raise ValueError(
                f"{field_name} must be between {min_val} and {max_val}"
            )
        return num_val
    except (TypeError, ValueError):
        raise ValueError(f"Invalid {field_name} value")

def _calculate_pushups(bmi):
    """Calculate safe number of pushups based on BMI"""
    if bmi < 18.5:  # Underweight
        return "2 sets of 5-8 reps"
    elif 18.5 <= bmi < 25:  # Normal weight
        return "3 sets of 8-12 reps"
    elif 25 <= bmi < 30:  # Overweight
        return "2 sets of 6-10 reps"
    else:  # Obese
        return "2 sets of 4-8 reps"

def generate_plan(height, weight, goal):
    """Generate exercise plan with input validation"""
    # Validate height (40cm to 250cm)
    height = validate_numeric_input(height, 40, 250, "height")
    
    # Validate weight (20kg to 300kg)
    weight = validate_numeric_input(weight, 20, 300, "weight")
    
    # Validate goal
    if goal not in goal_labels.values():
        raise ValueError("Invalid goal specified")
    
    # Calculate BMI
    bmi = weight / ((height / 100) ** 2)
    
    # Generate safe exercise plan based on BMI and goal
    plans = {
        'weight_loss': {
            'exercise': 'Cardio, Push-ups',
            'sets_reps': _calculate_pushups(bmi),
            'frequency': '5 days a week'
        },
        'muscle_gain': {
            'exercise': 'Strength Training, Push-ups',
            'sets_reps': '4 sets of 8-10 reps',
            'frequency': '4-5 days a week'
        },
        'endurance': {
            'exercise': 'Running, HIIT',
            'sets_reps': '30 mins per session',
            'frequency': '5 days a week'
        },
        'flexibility': {
            'exercise': 'Yoga, Stretching',
            'sets_reps': '20 mins per session',
            'frequency': '3-4 days a week'
        },
        'maintenance': {
            'exercise': 'Mixed exercises',
            'sets_reps': '3 sets of 12-15 reps',
            'frequency': '3 days a week'
        }
    }
    
    return plans[goal]

@app.route('/chat', methods=['POST'])
def chat():
    if not model or not tokenizer:
        return jsonify({
            'error': 'Model not initialized'
        }), 500
        
    try:
        data = request.get_json()
        
        if not data or not isinstance(data, dict):
            return jsonify({
                'error': 'Invalid request format'
            }), 400
            
        # Validate required fields
        required_fields = ['message', 'height', 'weight']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Process message
        message = str(data['message']).strip()
        if not message:
            return jsonify({
                'error': 'Empty message'
            }), 400
            
        # Validate and process height and weight
        try:
            height = validate_numeric_input(
                data['height'], 40, 250, "height"
            )
            weight = validate_numeric_input(
                data['weight'], 20, 300, "weight"
            )
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        
        # Tokenize and pad the message
        sequence = tokenizer.texts_to_sequences([message])
        padded_sequence = pad_sequences(
            sequence,
            maxlen=100,
            padding='post'
        )
        
        # Get model prediction
        prediction = model.predict(padded_sequence)
        predicted_goal = goal_labels[np.argmax(prediction[0])]
        
        # Generate exercise plan
        try:
            plan = generate_plan(height, weight, predicted_goal)
            return jsonify({
                'goal': predicted_goal,
                'plan': plan
            })
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
            
    except Exception as e:
        return jsonify({
            'error': f'Internal server error: {str(e)}'
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    
    # Use proper SSL in production
    ssl_context = None
    if os.getenv('FLASK_ENV') == 'production':
        ssl_context = (
            os.getenv('SSL_CERT_PATH'),
            os.getenv('SSL_KEY_PATH')
        )
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug_mode,
        ssl_context=ssl_context
    )
