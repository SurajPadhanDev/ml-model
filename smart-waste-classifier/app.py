import os
import io
import base64
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS
from PIL import Image
import numpy as np

# Load environment variables from .env file
load_dotenv()

# Initialize the Flask app
app = Flask(__name__)
CORS(app) # Enable Cross-Origin Resource Sharing for all routes
socketio = SocketIO(app, async_mode='eventlet')

# --- Model Loading ---
# This is a placeholder for your actual model loading logic.
# The application will look for the model file specified in the .env file.
model_path = os.getenv('MODEL_PATH')
try:
    # Replace this with your actual model loading code, e.g., using joblib or tensorflow
    # model = joblib.load(model_path)
    print(f"--- Model would be loaded from path: {model_path} ---")
    # For demonstration, we'll use a placeholder object.
    model = "YOUR_ML_MODEL_OBJECT"
except FileNotFoundError:
    print(f"--- WARNING: Model file not found at {model_path}. Using mock predictions. ---")
    model = None

# --- Prediction Logic ---
def predict_image(image_data):
    """
    This function takes a Pillow Image object, processes it, and returns a prediction.
    Replace the logic inside with your actual model's prediction code.
    """
    # Example preprocessing: resize image to what the model expects
    # image_data = image_data.resize((224, 224))
    # image_array = np.array(image_data)
    # image_array = image_array / 255.0
    # image_array = np.expand_dims(image_array, axis=0)

    # --- Replace this section with your model's inference call ---
    if model is None:
        # Mock prediction if the model file isn't found
        import random
        prediction = random.choice(['Recyclable', 'Not Recyclable'])
        confidence = random.uniform(0.75, 0.98)
    else:
        # prediction = model.predict(image_array)
        # For now, we'll return a mock result.
        prediction = "Recyclable"
        confidence = 0.95
    # --- End of model inference section ---

    return {'prediction': prediction, 'confidence': f"{confidence:.2f}"}

# --- HTTP Routes ---
@app.route('/')
def index():
    """Renders the main web page."""
    return render_template('index.html')

@app.route('/predict/upload', methods=['POST'])
def predict_upload():
    """Handles static image uploads and returns a JSON prediction."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        try:
            # Read the image file, convert to RGB, and get prediction
            image = Image.open(file.stream).convert("RGB")
            result = predict_image(image)
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': f'Could not process image: {e}'}), 500

# --- WebSocket Event Handlers ---
@socketio.on('video_frame')
def handle_video_frame(data_url):
    """
    Handles incoming video frames from the client, sent over WebSockets.
    It decodes the frame, gets a prediction, and sends the result back.
    """
    try:
        # The client sends a base64-encoded data URL, so we strip the header
        image_data = base64.b64decode(data_url.split(',')[1])
        image = Image.open(io.BytesIO(image_data))
        result = predict_image(image)
        # Emit the result back to the specific client that sent the frame
        socketio.emit('prediction_result', result)
    except Exception as e:
        # Silently ignore errors to prevent spamming logs on bad frames
        pass

# --- Main Execution ---
if __name__ == '__main__':
    print("Starting Flask development server...")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)

# --- DEPLOYMENT INSTRUCTIONS ---
#
# 1. To run in development mode (for testing on your own machine):
#    - Ensure you have all packages from requirements.txt installed.
#    - Simply run this script: python app.py
#    - The app will be available at http://127.0.0.1:5000
#
# 2. To deploy on your local network (for access from other devices like phones):
#    - You must use gunicorn, as the Flask dev server is not suitable for this.
#    - Find your computer's local IP address (e.g., 192.168.1.10).
#    - Run the following command in your terminal:
#
#    gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 app:app
#
#    - Explanation of the command:
#      - `gunicorn`: The server program.
#      - `--worker-class eventlet`: CRITICAL for enabling WebSocket (Socket.IO) support.
#      - `-w 1`: Use a single worker process.
#      - `--bind 0.0.0.0:5000`: Bind to all network interfaces on port 5000, making it accessible across the network.
#      - `app:app`: Tells Gunicorn to run the 'app' object from the 'app.py' file.
#
#    - Other devices on the same Wi-Fi can now access the app by navigating to http://<YOUR_LOCAL_IP>:5000 in their browser.
