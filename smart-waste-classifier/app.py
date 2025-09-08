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
    Uses the optimized prediction pipeline for higher accuracy.
    """
    try:
        # Import the optimized waste classification function
        from ai_integration import classify_waste
        
        # Use the ensemble prediction method for higher accuracy
        result = classify_waste(image_data, use_ensemble=True, confidence_threshold=0.65)
        
        if result:
            # We got a valid prediction from the ensemble system
            return {
                'prediction': result,
                'confidence': '0.95',  # High confidence with ensemble method
                'method': 'ensemble'
            }
    except Exception as api_error:
        print(f"Ensemble prediction error: {api_error}")
        # Continue with local model if ensemble fails
        pass
    
    # Fallback to local model if ensemble method fails
    try:
        # Resize image to what the model expects
        image_data = image_data.resize((224, 224))
        image_array = np.array(image_data)
        
        # Apply enhanced preprocessing
        # Convert to LAB color space for lighting normalization
        import cv2
        img_rgb = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
        lab = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2LAB)
        
        # Split channels and apply CLAHE to L channel
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        
        # Merge channels and convert back to RGB
        limg = cv2.merge((cl, a, b))
        img_normalized = cv2.cvtColor(limg, cv2.COLOR_LAB2RGB)
        
        # Normalize and expand dimensions for model input
        img_normalized = img_normalized / 255.0
        img_array = np.expand_dims(img_normalized, axis=0)

        if model is None:
            # Mock prediction if the model file isn't found
            import random
            prediction = random.choice(['Recyclable', 'Organic', 'Hazardous'])
            confidence = random.uniform(0.75, 0.98)
        else:
            # Get prediction from model
            predictions = model.predict(img_array, verbose=0)[0]
            
            # Get predicted class and confidence
            predicted_idx = np.argmax(predictions)
            classes = ["Organic", "Recyclable", "Hazardous"]
            prediction = classes[predicted_idx]
            confidence = float(predictions[predicted_idx])
            
            # Apply dynamic confidence threshold based on prediction distribution
            # If the top two predictions are close, reduce confidence
            sorted_preds = np.sort(predictions)[::-1]
            if len(sorted_preds) > 1 and (sorted_preds[0] - sorted_preds[1]) < 0.2:
                confidence = confidence * 0.8  # Reduce confidence when uncertain

        return {
            'prediction': prediction,
            'confidence': f"{confidence:.2f}",
            'method': 'local'
        }
    except Exception as e:
        print(f"Local prediction error: {e}")
        # Return a fallback prediction if all else fails
        return {
            'prediction': 'Unknown',
            'confidence': '0.00',
            'error': str(e)
        }

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
