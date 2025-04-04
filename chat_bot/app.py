from flask import Flask, request, jsonify
from flask_cors import CORS
import tensorflow as tf
import pickle
import numpy as np
from keras.preprocessing.sequence import pad_sequences

app = Flask(__name__)  # Initialize the Flask app
CORS(app)  # Enable CORS for all routes

# Load the trained model and tokenizer
model = tf.keras.models.load_model('fitness_classifier.h5')
with open('tokenizer.pkl', 'rb') as f:
    tokenizer = pickle.load(f)

goal_labels = {
    0: 'weight_loss',
    1: 'muscle_gain',
    2: 'endurance',
    3: 'flexibility',
    4: 'maintenance'
}

def generate_plan(height, weight, goal):
    bmi = weight / ((height / 100) ** 2)

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

def _calculate_pushups(bmi):
    if bmi < 18.5:
        return '2 sets of 5-8 reps'
    elif bmi <= 24.9:
        return '3 sets of 10-12 reps'
    else:
        return '4 sets of 8-10 reps'

@app.route('/chatbot', methods=['POST'])
def chatbot():
    data = request.json
    print("Received data:", data)  # Log incoming JSON data for debugging
    height = float(data['height'])  # Convert to float for calculations
    weight = float(data['weight'])
    query = data['query']

    # Predict goal using the NLP model
    sequence = tokenizer.texts_to_sequences([query])
    padded = pad_sequences(sequence, maxlen=10)  # Adjust maxlen based on model input
    prediction = np.argmax(model.predict(padded), axis=1)[0]  # Predict the goal

    # Map the predicted index to the corresponding goal label
    goal = goal_labels[prediction]
    print("Predicted goal:", goal)

    # Generate a fitness plan based on height, weight, and predicted goal
    plan = generate_plan(height, weight, goal)
    print(plan)

    # Return the generated plan as JSON
    return jsonify({'plan': plan})

if __name__ == '__main__':
    app.run(debug=True)
