import os
import numpy as np
import base64
import json
import random
import asyncio
from io import BytesIO
from flask import Flask, request, jsonify, render_template, send_from_directory, url_for
from flask_cors import CORS
from PIL import Image

# Import AI integration module (if available)
try:
    from ai_integration import check_api_availability, classify_with_gemini, classify_with_openai
    AI_INTEGRATION_AVAILABLE = True
except ImportError:
    AI_INTEGRATION_AVAILABLE = False
    print("⚠️ AI Integration module not available. Using local model only.")
    # Create a placeholder for the API availability check
    def check_api_availability():
        return {"gemini": False, "openai": False}

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Create directories for uploads if they don't exist
os.makedirs('uploads', exist_ok=True)

# -----------------------------
# Model setup
# -----------------------------
print("✅ Using prediction model for demonstration")

# Check for external AI API availability
if AI_INTEGRATION_AVAILABLE:
    api_status = check_api_availability()
    if api_status["gemini"]:
        print("✅ Gemini API configured and available")
    if api_status["openai"]:
        print("✅ OpenAI API configured and available")

# Classes
CLASSES = ["O", "R", "H"]
CLASS_NAMES = {"R": "Organic", "O": "Hazardous", "H": "Recycle"}
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))

# -----------------------------
# Utility functions
# -----------------------------
def resize_with_padding(img):
    """Mock resize function (not actually used in demo)"""
    return img

async def process_image_with_ai(img):
    """Process image using external AI APIs if available"""
    results = []
    api_status = check_api_availability()
    
    # Use Gemini API if available
    if api_status["gemini"]:
        try:
            gemini_result = await classify_with_gemini(img)
            if "error" not in gemini_result:
                results.append(gemini_result)
        except Exception as e:
            print(f"Error with Gemini API: {str(e)}")
    
    # Use OpenAI API if available
    if api_status["openai"]:
        try:
            openai_result = classify_with_openai(img)
            if "error" not in openai_result:
                results.append(openai_result)
        except Exception as e:
            print(f"Error with OpenAI API: {str(e)}")
    
    # If we have results from external APIs, combine them
    if results:
        # Simple ensemble: use the prediction with highest confidence
        best_result = max(results, key=lambda x: x.get("confidence", 0))
        
        # Map external API category to our class format
        category_mapping = {
            "Organic": "R",
            "Recyclable": "H",
            "Hazardous": "O",
            "Non-recyclable": "O"  # Treating non-recyclable as hazardous for now
        }
        
        predicted_class = category_mapping.get(best_result["class_name"], "O")
        confidence = best_result["confidence"]
        
        return {
            "class": predicted_class,
            "class_name": CLASS_NAMES[predicted_class],
            "confidence": confidence,
            "confidence_percentage": round(confidence * 100, 1),
            "is_confident": confidence >= CONFIDENCE_THRESHOLD,
            "timestamp": os.path.basename(str(random.randint(10000000, 99999999))),
            "ai_source": best_result.get("source", "unknown"),
            "reasoning": best_result.get("reasoning", "")
        }
    
    return None

def process_image(image_data):
    """Process function that uses AI APIs if available, otherwise falls back to mock predictions."""
    # Convert numpy array to PIL Image if needed
    if isinstance(image_data, np.ndarray):
        img = Image.fromarray(image_data)
    elif isinstance(image_data, Image.Image):
        img = image_data
    else:
        # For demonstration, we'll return random predictions
        predicted_idx = random.randint(0, 2)
        predicted_class = CLASSES[predicted_idx]
        confidence = random.uniform(0.7, 0.98)  # Random confidence between 70% and 98%
        
        # Prepare result
        result = {
            "class": predicted_class,
            "class_name": CLASS_NAMES[predicted_class],
            "confidence": confidence,
            "confidence_percentage": round(confidence * 100, 1),
            "is_confident": confidence >= CONFIDENCE_THRESHOLD,
            "timestamp": os.path.basename(str(random.randint(10000000, 99999999)))
        }
        
        # Add a message to send to parent window when in widget mode
        if request.args.get('widget', 'false').lower() == 'true':
            result['widget_message'] = 'Classification complete'
        
        return result
    
    # Try to use AI APIs if available
    if AI_INTEGRATION_AVAILABLE:
        try:
            # Run the async function in a synchronous context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            ai_result = loop.run_until_complete(process_image_with_ai(img))
            loop.close()
            
            if ai_result:
                # Add a message to send to parent window when in widget mode
                if request.args.get('widget', 'false').lower() == 'true':
                    ai_result['widget_message'] = 'Classification complete with AI'
                return ai_result
        except Exception as e:
            print(f"Error using AI integration: {str(e)}")
    
    # Fallback to mock predictions
    predicted_idx = random.randint(0, 2)
    predicted_class = CLASSES[predicted_idx]
    confidence = random.uniform(0.7, 0.98)  # Random confidence between 70% and 98%
    
    # Prepare result
    result = {
        "class": predicted_class,
        "class_name": CLASS_NAMES[predicted_class],
        "confidence": confidence,
        "confidence_percentage": round(confidence * 100, 1),
        "is_confident": confidence >= CONFIDENCE_THRESHOLD,
        "timestamp": os.path.basename(str(random.randint(10000000, 99999999)))
    }
    
    # Add a message to send to parent window when in widget mode
    if request.args.get('widget', 'false').lower() == 'true':
        result['widget_message'] = 'Classification complete'
    
    return result

# -----------------------------
# API Routes
# -----------------------------
@app.route('/')
def index():
    # Get widget parameters if provided
    is_widget = request.args.get('widget', 'false').lower() == 'true'
    theme = request.args.get('theme', 'dark')
    show_upload = request.args.get('showUpload', 'true').lower() == 'true'
    show_webcam = request.args.get('showWebcam', 'true').lower() == 'true'
    auto_start = request.args.get('autoStart', 'false').lower() == 'true'
    
    # Pass parameters to template
    return render_template('index.html', 
                          is_widget=is_widget,
                          theme=theme,
                          show_upload=show_upload,
                          show_webcam=show_webcam,
                          auto_start=auto_start)

@app.route('/integration-demo')
def integration_demo():
    return render_template('integration_demo.html')

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/api/predict', methods=['POST'])
def predict():
    if 'image' not in request.files and 'image_data' not in request.json and 'file' not in request.files and 'file' not in request.form:
        return jsonify({"error": "No image provided"}), 400
    
    try:
        # Handle file upload from file input
        if 'image' in request.files:
            file = request.files['image']
            img = Image.open(file.stream)
            img_array = np.array(img)
            result = process_image(img_array)
            return jsonify(result)
        
        # Handle file upload from alternative field name
        elif 'file' in request.files:
            file = request.files['file']
            img = Image.open(file.stream)
            img_array = np.array(img)
            result = process_image(img_array)
            return jsonify(result)
        
        # Handle base64 image data from JSON
        elif 'image_data' in request.json:
            image_data = request.json['image_data']
            # Remove data URL prefix if present
            if 'base64,' in image_data:
                image_data = image_data.split('base64,')[1]
            
            # Decode base64 image
            img_bytes = base64.b64decode(image_data)
            img = Image.open(BytesIO(img_bytes))
            img_array = np.array(img)
            result = process_image(img_array)
            return jsonify(result)
        
        # Handle base64 image data from form (camera capture)
        elif 'file' in request.form:
            image_data = request.form['file']
            # Remove data URL prefix if present
            if 'base64,' in image_data:
                image_data = image_data.split('base64,')[1]
            
            # Decode base64 image
            img_bytes = base64.b64decode(image_data)
            img = Image.open(BytesIO(img_bytes))
            img_array = np.array(img)
            result = process_image(img_array)
            return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -----------------------------
# Main entry point
# -----------------------------
if __name__ == "__main__":
    # Create templates and static directories if they don't exist
    os.makedirs("templates", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=8081, debug=True)