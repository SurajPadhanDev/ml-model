# BOLT INNOVATORS - Smart Waste Classification System

## Project Overview

The Smart Waste Classification System is an innovative web application developed by BOLT INNOVATORS that uses computer vision and machine learning to accurately classify waste items into different categories (Organic, Recyclable, Hazardous, Non-recyclable). The system aims to promote proper waste disposal practices, reduce contamination in recycling streams, and contribute to environmental sustainability.

### Core Objectives

- **Accurate Classification**: Provide reliable identification of waste materials using advanced ML models
- **Accessibility**: Make waste classification technology available to everyone through an easy-to-use web interface
- **Education**: Inform users about proper waste disposal methods for different materials
- **Integration**: Offer flexible integration options for websites, apps, and smart devices
- **Responsive Design**: Ensure the system works seamlessly across desktop and mobile devices

## Features

### Core Functionality
- **Real-time Classification**: Analyze waste items in real-time using webcam
- **Image Upload**: Upload images from your device for classification
- **Camera Capture**: Take photos directly from your mobile device camera
- **Detailed Results**: Get classification results with confidence scores and disposal recommendations
- **Educational Content**: Learn about different waste types and proper disposal methods

### Technical Features
- **Responsive Design**: Works seamlessly on mobile, tablet, and desktop devices
- **Multiple Integration Options**: iframe, JavaScript widget, or direct API integration
- **Customizable Appearance**: Dark/light themes and configurable UI elements
- **Widget Communication**: Bidirectional communication via postMessage API
- **Flexible API**: Support for both file uploads and base64 encoded images
- **Offline Capability**: Core classification can work without internet connection (when properly configured)

## Installation

### Prerequisites

- Python 3.7+ (3.8+ recommended)
- Flask and Flask-CORS
- Pillow (PIL) for image processing
- NumPy for array operations
- TensorFlow 2.x (for the full model version, not required for demo mode)
- Modern web browser with JavaScript enabled
- Camera access (for webcam features)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/bolt-innovators/waste-classification.git
   cd waste-classification
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   # On Windows
   python -m venv venv
   venv\Scripts\activate
   
   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python app.py
   ```

5. Access the application at `http://localhost:8081`

### Environment Variables

The application supports the following environment variables:

- `PORT`: The port to run the server on (default: 8081)
- `DEBUG`: Enable debug mode (default: True for development)
- `MODEL_PATH`: Path to custom model file (optional)
- `CONFIDENCE_THRESHOLD`: Minimum confidence threshold for predictions (default: 0.7)

## System Architecture and Components

### Backend Components

- **Flask Server**: Handles HTTP requests, serves static files, and processes API calls
- **Image Processing Pipeline**: Prepares uploaded or captured images for classification
- **Classification Model**: A machine learning model that identifies waste categories
- **API Layer**: Provides endpoints for classification and integration with external systems

### Frontend Components

- **User Interface**: Responsive HTML/CSS interface with dark/light theme support
- **Camera Module**: JavaScript code for accessing and controlling device cameras
- **Upload Module**: Handles file selection and validation
- **Results Display**: Visualizes classification results and confidence scores
- **Widget Communication**: Manages postMessage API for iframe integration

### Data Flow

1. User captures an image via webcam or uploads a file
2. Image is preprocessed (resized, normalized) in the browser
3. Image data is sent to the server via API
4. Server processes the image and runs it through the classification model
5. Results are returned to the client and displayed to the user

## Integration with Existing Websites

There are three ways to integrate this waste classification system into your existing website:

### 1. JavaScript Widget (Recommended)

The easiest way to integrate the system is using our JavaScript widget:

```html
<!-- 1. Add the container where you want the widget to appear -->
<div id="waste-classifier"></div>

<!-- 2. Include the widget script -->
<script src="http://your-flask-server:8081/static/js/widget.js"></script>

<!-- 3. Initialize the widget with your desired options -->
<script>
  const wasteClassifier = new WasteClassifier('#waste-classifier', {
    theme: 'dark',        // 'dark' or 'light'
    showUpload: true,     // Show file upload option
    showWebcam: true,     // Show webcam option
    autoStart: false,     // Auto-start webcam
    onResult: function(result) {
      console.log('Classification result:', result);
      // Handle the result in your application
      if (result.is_confident) {
        alert(`This item is ${result.class_name} waste with ${result.confidence_percentage}% confidence`);
      } else {
        alert('Could not classify with high confidence. Please try again.');
      }
    }
  });
  
  // Available methods
  wasteClassifier.startCamera();  // Start the camera
  wasteClassifier.stopCamera();   // Stop the camera
  wasteClassifier.captureImage(); // Capture an image from the camera
  wasteClassifier.reset();        // Reset the widget
</script>
```

#### Widget Configuration Options

- `containerId`: ID of the container element (default: 'waste-classifier-widget')
- `width`: Width of the widget (default: '100%')
- `height`: Height of the widget (default: '600px')
- `theme`: 'dark' or 'light' (default: 'dark')
- `showUpload`: Show/hide the file upload section (default: true)
- `showWebcam`: Show/hide the webcam section (default: true)
- `autoStart`: Automatically start the webcam when loaded (default: false)
- `onResult`: Callback function for classification results

#### Widget Methods

```javascript
// Start the camera
classifier.startCamera();

// Stop the camera
classifier.stopCamera();

// Capture an image and classify it
classifier.captureImage();
```

### 2. iframe Embedding

You can embed the application in an iframe with customization options:

```html
<iframe 
    src="http://your-flask-server:8081/?widget=true&theme=dark&showUpload=true&showWebcam=true&autoStart=false" 
    width="100%" 
    height="600px" 
    frameborder="0">
</iframe>

<script>
  // Listen for messages from the iframe
  window.addEventListener('message', function(event) {
    // Verify the origin of the message
    if (event.origin !== 'http://your-flask-server:8081') return;
    
    console.log('Received result:', event.data);
    // Handle the result in your application
    if (event.data.type === 'classification_result') {
      const result = event.data.result;
      document.getElementById('result-display').innerHTML = `
        <h3>Classification Result:</h3>
        <p>Type: ${result.class_name}</p>
        <p>Confidence: ${result.confidence_percentage}%</p>
      `;
    }
  });
  
  // You can also send messages to the iframe
  function sendMessageToWidget(message) {
    const iframe = document.querySelector('iframe');
    iframe.contentWindow.postMessage(message, 'http://your-flask-server:8081');
  }
  
  // Example: Reset the widget
  function resetWidget() {
    sendMessageToWidget({ action: 'reset' });
  }
</script>

<!-- Optional: Add controls to interact with the widget -->
<div>
  <button onclick="resetWidget()">Reset Widget</button>
  <div id="result-display"></div>
</div>
```

#### iframe Customization Options

You can customize the iframe by adding query parameters to the URL:

- `widget=true` - Enables widget mode (required)
- `theme=dark|light` - Sets the color theme
- `showUpload=true|false` - Shows/hides the upload option
- `showWebcam=true|false` - Shows/hides the webcam option
- `autoStart=true|false` - Automatically starts the webcam

### 3. Direct API Integration

Use the API directly in your application:

```javascript
// Example 1: Classify an image from base64 data
async function classifyImageFromBase64(base64Image) {
    try {
        const response = await fetch('http://your-flask-server:8081/api/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                image_data: base64Image // Base64 string without the prefix (e.g., remove 'data:image/jpeg;base64,')
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        const result = await response.json();
        console.log(`Classified as ${result.class_name} with ${result.confidence_percentage}% confidence`);
        return result;
    } catch (error) {
        console.error('Classification error:', error);
        throw error;
    }
}

// Example 2: Classify an image from a file input
async function classifyImageFromFile(file) {
    try {
        const formData = new FormData();
        formData.append('image', file);
        
        const response = await fetch('http://your-flask-server:8081/api/predict', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        const result = await response.json();
        console.log(`Classified as ${result.class_name} with ${result.confidence_percentage}% confidence`);
        return result;
    } catch (error) {
        console.error('Classification error:', error);
        throw error;
    }
}

// Example 3: Using the API with async/await in a React component
import React, { useState } from 'react';

function WasteClassifier() {
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    
    const handleFileUpload = async (event) => {
        const file = event.target.files[0];
        if (!file) return;
        
        setLoading(true);
        setError(null);
        
        try {
            const formData = new FormData();
            formData.append('image', file);
            
            const response = await fetch('http://your-flask-server:8081/api/predict', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            const data = await response.json();
            setResult(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };
    
    return (
        <div>
            <h2>Waste Classifier</h2>
            <input type="file" accept="image/*" onChange={handleFileUpload} />
            
            {loading && <p>Classifying image...</p>}
            {error && <p>Error: {error}</p>}
            
            {result && (
                <div>
                    <h3>Classification Result:</h3>
                    <p>Type: {result.class_name}</p>
                    <p>Confidence: {result.confidence_percentage}%</p>
                    {result.is_confident ? (
                        <p>This classification is reliable.</p>
                    ) : (
                        <p>This classification has low confidence. Please try again with a clearer image.</p>
                    )}
                </div>
            )}
        </div>
    );
}

## Demo and Integration Guide

To see a live demonstration of the integration options and learn more about how to integrate the waste classification system into your website, visit the integration demo page at:

```
http://127.0.0.1:8081/integration-demo
```

This page provides interactive examples and code snippets that you can copy and paste into your own website.

#### Predict from Base64 Image

```javascript
async function classifyImage(base64Image) {
    // Remove data URL prefix if present
    if (base64Image.includes('base64,')) {
        base64Image = base64Image.split('base64,')[1];
    }
    
    try {
        const response = await fetch('http://your-flask-server:5000/api/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                image_data: base64Image
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Classification error:', error);
        throw error;
    }
}
```

#### Predict from File Upload

```javascript
async function classifyImageFile(file) {
    try {
        const formData = new FormData();
        formData.append('image', file);
        
        const response = await fetch('http://your-flask-server:5000/api/predict', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Classification error:', error);
        throw error;
    }
}
```

## API Documentation

### POST /api/predict

Classifies an image and returns the prediction result.

#### Request

The API accepts two types of requests:

1. **JSON with Base64 Image Data**

```json
{
    "image_data": "base64_encoded_image_data"
}
```

Note: The base64 string should not include the prefix (e.g., `data:image/jpeg;base64,`)

2. **Multipart Form Data with Image File**

Field name: `image` or `file`
Value: Image file (JPEG, PNG, etc.)

#### Response

```json
{
    "class": "R",                  // Class code (R, O, H)
    "class_name": "Organic",      // Human-readable class name
    "confidence": 0.95,           // Confidence score (0-1)
    "confidence_percentage": 95.0, // Confidence as percentage
    "is_confident": true,         // Whether confidence exceeds threshold
    "timestamp": "12345678"       // Unique identifier for this prediction
}
```

## Deployment

For production deployment, you should consider:

1. Using a production WSGI server like Gunicorn:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

2. Setting up a reverse proxy with Nginx or Apache

3. Implementing proper security measures (HTTPS, API keys, etc.)

## Customization

### Changing the Confidence Threshold

You can modify the confidence threshold in `app.py`:

```python
CONFIDENCE_THRESHOLD = 0.7  # Change this value (0-1)
```

### Styling

The application uses CSS variables for easy styling. You can modify the colors and other styles in `static/css/style.css`.

## Troubleshooting

### Camera Access Issues

- Make sure your browser has permission to access the camera
- Try using a different browser if you encounter issues
- For mobile devices, ensure you're using HTTPS as most browsers require it for camera access
- Check that your device has a working camera and it's not being used by another application

### Classification Issues

- Ensure good lighting for better classification results
- Position objects clearly in the center of the frame
- If classification seems inaccurate, try capturing from different angles
- Make sure the image is clear and not blurry
- Try with different waste items to verify the system is working correctly

## Contribution Guidelines

We welcome contributions to improve the Smart Waste Classification System! Here's how you can contribute:

### Reporting Issues

- Use the GitHub issue tracker to report bugs
- Include detailed steps to reproduce the issue
- Mention your browser/device and operating system
- Add screenshots if applicable

### Submitting Changes

1. Fork the repository
2. Create a new branch for your feature or bugfix (`git checkout -b feature/your-feature-name`)
3. Make your changes
4. Run tests to ensure your changes don't break existing functionality
5. Commit your changes with clear, descriptive commit messages
6. Push to your branch (`git push origin feature/your-feature-name`)
7. Submit a Pull Request

### Code Style Guidelines

- Follow PEP 8 style guide for Python code
- Use consistent indentation (4 spaces for Python, 2 spaces for JavaScript/HTML/CSS)
- Add comments for complex logic
- Write clear function and variable names
- Include docstrings for Python functions

### Adding New Features

Before developing a new feature, please open an issue to discuss it. This ensures your work aligns with the project's goals and direction.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

```
MIT License

Copyright (c) 2023 BOLT INNOVATORS

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## External AI API Integration

You can enhance the classification accuracy of the Smart Waste Classification System by integrating external AI APIs from Google's Gemini or OpenAI's ChatGPT. This section provides detailed instructions for implementing these integrations.

### 1. API Key Acquisition and Configuration

#### Google Gemini API

1. **Create a Google AI Studio account**:
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Sign in with your Google account
   - Navigate to the API keys section

2. **Generate an API key**:
   - Click on "Create API Key"
   - Copy and securely store your API key

3. **Add to environment variables**:
   - Add the following to your `.env` file:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

#### OpenAI ChatGPT API

1. **Create an OpenAI account**:
   - Visit [OpenAI Platform](https://platform.openai.com/signup)
   - Complete the registration process

2. **Generate an API key**:
   - Navigate to [API Keys](https://platform.openai.com/api-keys)
   - Click "Create new secret key"
   - Name your key and copy it (note: it will only be shown once)

3. **Add to environment variables**:
   - Add the following to your `.env` file:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

### 2. Required Dependencies and Installation Steps

Update your `requirements.txt` file to include the necessary packages:

```
# External AI API Dependencies
google-generativeai>=0.3.0  # For Gemini API
openai>=1.0.0               # For ChatGPT API
requests>=2.28.0            # For API requests
python-dotenv>=1.0.0        # For environment variable management
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

### 3. Code Implementation Examples

#### Setting Up API Clients

Create a new file called `ai_integration.py` in your project root:

```python
import os
import base64
from io import BytesIO
import requests
import google.generativeai as genai
from openai import OpenAI
from dotenv import load_dotenv
from PIL import Image

# Load environment variables
load_dotenv()

# Initialize API clients
gemini_api_key = os.getenv("GEMINI_API_KEY")
if gemini_api_key:
    genai.configure(api_key=gemini_api_key)

openai_api_key = os.getenv("OPENAI_API_KEY")
if openai_api_key:
    openai_client = OpenAI(api_key=openai_api_key)

# Function to check if API keys are configured
def check_api_availability():
    apis_available = {
        "gemini": bool(gemini_api_key),
        "openai": bool(openai_api_key)
    }
    return apis_available

# Function to encode image for API requests
def encode_image(image):
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')
```

#### Implementing Gemini Vision API for Image Classification

Add the following to `ai_integration.py`:

```python
async def classify_with_gemini(image, model_name="gemini-pro-vision"):
    """Classify waste image using Google's Gemini Vision API"""
    try:
        # Prepare the model
        model = genai.GenerativeModel(model_name)
        
        # Prepare the prompt
        prompt = """
        Analyze this image and classify the waste item into one of these categories:
        - Organic: Food waste, plant materials, compostable items
        - Recyclable: Paper, cardboard, glass, certain plastics, metals
        - Hazardous: Batteries, chemicals, electronic waste, medical waste
        - Non-recyclable: Mixed materials, certain plastics, contaminated items
        
        Provide your classification as a JSON object with these fields:
        - category: The waste category (Organic, Recyclable, Hazardous, or Non-recyclable)
        - confidence: Your confidence level as a percentage (0-100)
        - reasoning: Brief explanation for this classification
        """
        
        # Generate content
        response = await model.generate_content_async([prompt, image])
        
        # Extract and parse the response
        result_text = response.text
        
        # Basic parsing (in production, use proper JSON parsing with error handling)
        import json
        try:
            # Try to extract JSON from the response
            json_str = result_text[result_text.find('{'):result_text.rfind('}')+1]
            result = json.loads(json_str)
        except:
            # Fallback to structured response
            result = {
                "category": "Unknown",
                "confidence": 0,
                "reasoning": "Could not parse the response"
            }
            
        return {
            "source": "gemini",
            "class_name": result.get("category", "Unknown"),
            "confidence": float(result.get("confidence", 0)) / 100,
            "reasoning": result.get("reasoning", "")
        }
        
    except Exception as e:
        return {
            "source": "gemini",
            "error": str(e),
            "class_name": "Error",
            "confidence": 0
        }
```

#### Implementing OpenAI Vision API for Image Classification

Add the following to `ai_integration.py`:

```python
def classify_with_openai(image, model_name="gpt-4-vision-preview"):
    """Classify waste image using OpenAI's Vision API"""
    try:
        # Encode image to base64
        base64_image = encode_image(image)
        
        # Prepare the prompt
        response = openai_client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": "You are a waste classification expert. Analyze the image and classify the waste item."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": """Classify this waste item into one of these categories:
                        - Organic: Food waste, plant materials, compostable items
                        - Recyclable: Paper, cardboard, glass, certain plastics, metals
                        - Hazardous: Batteries, chemicals, electronic waste, medical waste
                        - Non-recyclable: Mixed materials, certain plastics, contaminated items
                        
                        Respond with a JSON object containing:
                        {"category": "[category name]", "confidence": [0-100], "reasoning": "[brief explanation]"}
                        """}, 
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        }
                    ]
                }
            ],
            max_tokens=300
        )
        
        # Extract and parse the response
        result_text = response.choices[0].message.content
        
        # Parse JSON from response
        import json
        try:
            # Try to extract JSON from the response
            json_str = result_text[result_text.find('{'):result_text.rfind('}')+1]
            result = json.loads(json_str)
        except:
            # Fallback to structured response
            result = {
                "category": "Unknown",
                "confidence": 0,
                "reasoning": "Could not parse the response"
            }
            
        return {
            "source": "openai",
            "class_name": result.get("category", "Unknown"),
            "confidence": float(result.get("confidence", 0)) / 100,
            "reasoning": result.get("reasoning", "")
        }
        
    except Exception as e:
        return {
            "source": "openai",
            "error": str(e),
            "class_name": "Error",
            "confidence": 0
        }
```

#### Integrating with the Main Application

Modify your `app.py` file to include the external API integration:

```python
# Add these imports at the top of app.py
from ai_integration import check_api_availability, classify_with_gemini, classify_with_openai
import asyncio

# Add a new route for enhanced prediction
@app.route('/api/predict/enhanced', methods=['POST'])
async def predict_enhanced():
    if 'image' not in request.files and 'image_data' not in request.json and 'file' not in request.files and 'file' not in request.form:
        return jsonify({"error": "No image provided"}), 400
    
    try:
        # Process the image (similar to the existing predict route)
        # ... [existing image processing code] ...
        
        # Get the image object
        img = None  # Replace with actual image object from your processing
        
        # Check which APIs are available
        apis = check_api_availability()
        results = []
        
        # Get base model prediction
        base_result = process_image(img_array)  # Your existing model
        results.append({
            "source": "base_model",
            "class_name": base_result["class_name"],
            "confidence": base_result["confidence"]
        })
        
        # Get predictions from available external APIs
        if apis["gemini"]:
            gemini_result = await classify_with_gemini(img)
            results.append(gemini_result)
            
        if apis["openai"]:
            openai_result = classify_with_openai(img)
            results.append(openai_result)
        
        # Combine results (simple averaging for this example)
        # In a production system, you might use a more sophisticated ensemble method
        combined_result = ensemble_predictions(results)
        
        return jsonify(combined_result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Helper function to combine predictions
def ensemble_predictions(results):
    # Simple implementation - you can replace with more sophisticated logic
    valid_results = [r for r in results if "error" not in r]
    
    if not valid_results:
        return {"error": "No valid predictions available"}
    
    # Count votes for each class
    class_votes = {}
    class_confidence = {}
    
    for result in valid_results:
        class_name = result["class_name"]
        confidence = result["confidence"]
        
        if class_name in class_votes:
            class_votes[class_name] += 1
            class_confidence[class_name] += confidence
        else:
            class_votes[class_name] = 1
            class_confidence[class_name] = confidence
    
    # Find the class with the most votes
    max_votes = 0
    selected_class = None
    
    for class_name, votes in class_votes.items():
        if votes > max_votes:
            max_votes = votes
            selected_class = class_name
    
    # Calculate average confidence for the selected class
    avg_confidence = class_confidence[selected_class] / class_votes[selected_class]
    
    return {
        "class": selected_class[:1],  # First letter as class code
        "class_name": selected_class,
        "confidence": avg_confidence,
        "confidence_percentage": round(avg_confidence * 100, 1),
        "is_confident": avg_confidence >= CONFIDENCE_THRESHOLD,
        "sources": [r["source"] for r in valid_results],
        "timestamp": os.path.basename(str(random.randint(10000000, 99999999)))
    }
```

### 4. Error Handling and Best Practices

#### Error Handling

1. **API Connection Failures**:
   - Implement timeouts for API requests (typically 10-30 seconds)
   - Add retry logic for transient failures
   - Gracefully fall back to the base model when external APIs are unavailable

2. **Rate Limiting**:
   - Implement token bucket or similar rate limiting to avoid exceeding API quotas
   - Cache results for identical or similar images to reduce API calls

3. **Response Parsing**:
   - Use robust JSON parsing with error handling
   - Validate responses against expected schemas
   - Implement fallback logic when responses don't match expected formats

#### Best Practices

1. **Asynchronous Processing**:
   - Use asynchronous requests to avoid blocking the main application
   - Consider implementing a job queue for high-traffic applications

2. **Caching**:
   - Cache API responses to reduce costs and improve performance
   - Consider using Redis or a similar in-memory cache for fast access

3. **Monitoring**:
   - Log API usage and response times
   - Set up alerts for API failures or unusual patterns
   - Track costs and usage to avoid unexpected bills

4. **Testing**:
   - Create mock responses for testing without consuming API credits
   - Implement integration tests with small API quotas
   - Test fallback mechanisms by simulating API failures

### 5. Security Considerations for API Usage

1. **API Key Management**:
   - NEVER hardcode API keys in your source code
   - Store API keys in environment variables or a secure vault
   - Rotate API keys periodically
   - Use different API keys for development and production

2. **Data Privacy**:
   - Be aware that data sent to external APIs may be stored by the provider
   - Inform users that their images may be processed by third-party services
   - Consider implementing local preprocessing to remove sensitive information
   - Review the privacy policies of the API providers

3. **Access Control**:
   - Implement authentication for your enhanced API endpoints
   - Consider using API keys or OAuth for your own API consumers
   - Restrict access to the enhanced prediction features if needed

4. **Network Security**:
   - Use HTTPS for all API communications
   - Implement proper CORS policies to prevent unauthorized access
   - Consider using a VPN or private network for API calls in sensitive environments

5. **Cost Protection**:
   - Implement usage quotas to prevent abuse
   - Set up billing alerts with your API providers
   - Consider implementing a credit system for your users

## Acknowledgments

- BOLT INNOVATORS team for the original waste classification system
- TensorFlow and MobileNetV2 for the machine learning framework and model architecture
- Flask team for the web framework
- Open source community for various libraries and tools used in this project
- Google Gemini and OpenAI for providing powerful vision API services
- All contributors who have helped improve this project