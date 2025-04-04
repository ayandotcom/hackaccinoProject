from flask import Flask, jsonify
import subprocess

app = Flask(__name__)

@app.route('/run_tree_pose', methods=['GET'])
def run_tree_pose():
    try:
        # Run your Python script
        result = subprocess.run(['python', 'yoga_poses/Tree_pose.py'], capture_output=True, text=True)
        return jsonify({'stdout': result.stdout, 'stderr': result.stderr}), result.returncode
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
