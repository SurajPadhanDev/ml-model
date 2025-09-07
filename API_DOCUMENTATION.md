# BOLT INNOVATORS - Waste Classification API Documentation

## Overview

This document provides detailed information about the API endpoints available for integrating the waste classification system into your existing website.

## Base URL

All API endpoints are relative to the base URL where the Flask application is hosted:

```
http://your-flask-server:5000
```

Replace `your-flask-server` with the domain or IP address where your Flask application is running.

## Authentication

Currently, the API does not require authentication. If you're integrating this into a production environment, you should implement appropriate authentication mechanisms.

## Endpoints

### 1. Predict Waste Classification

**Endpoint:** `/api/predict`

**Method:** POST

**Description:** Classifies an image and returns the prediction result.

**Request Formats:**

The API accepts two types of requests:

#### Option 1: JSON with Base64 Image Data

**Content-Type:** `application/json`

**Request Body:**

```json
{
    "image_data": "base64_encoded_image_data"
}
```

**Example:**

```javascript
fetch('http://your-flask-server:5000/api/predict', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        image_data: base64ImageString
    })
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));
```

#### Option 2: Multipart Form Data with Image File

**Content-Type:** `multipart/form-data`

**Form Field:**
- Name: `image`
- Value: Image file (JPEG, PNG, etc.)

**Example:**

```javascript
const formData = new FormData();
formData.append('image', imageFile);

fetch('http://your-flask-server:5000/api/predict', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));
```

**Response:**

```json
{
    "class": "R",                  // Class code (R, O, H)
    "class_name": "Recyclable",    // Human-readable class name
    "confidence": 0.95,           // Confidence score (0-1)
    "confidence_percentage": 95.0, // Confidence as percentage
    "is_confident": true          // Whether confidence exceeds threshold
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| class | string | The class code: "O" (Organic), "R" (Recyclable), or "H" (Hazardous) |
| class_name | string | Human-readable class name |
| confidence | float | Confidence score between 0 and 1 |
| confidence_percentage | float | Confidence as a percentage (0-100) |
| is_confident | boolean | Whether the confidence exceeds the threshold (default: 0.7) |

**Status Codes:**

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid input (missing image, invalid format, etc.) |
| 500 | Server Error - Error processing the image or making prediction |

## Integration Examples

### Example 1: Basic Image Upload Form

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Waste Classification</title>
    <style>
        .result {
            margin-top: 20px;
            padding: 15px;
            border-radius: 5px;
        }
        .result.organic { background-color: #a8e6cf; }
        .result.recyclable { background-color: #dcedc1; }
        .result.hazardous { background-color: #ffd3b6; }
    </style>
</head>
<body>
    <h1>Waste Classification</h1>
    
    <form id="upload-form">
        <input type="file" id="image-input" accept="image/*">
        <button type="submit">Classify</button>
    </form>
    
    <div id="result-container" style="display: none;" class="result">
        <h2>Result: <span id="class-name"></span></h2>
        <p>Confidence: <span id="confidence"></span>%</p>
    </div>

    <script>
        document.getElementById('upload-form').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const fileInput = document.getElementById('image-input');
            if (!fileInput.files[0]) {
                alert('Please select an image file');
                return;
            }
            
            const formData = new FormData();
            formData.append('image', fileInput.files[0]);
            
            try {
                const response = await fetch('http://your-flask-server:5000/api/predict', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                
                const result = await response.json();
                
                // Display result
                const resultContainer = document.getElementById('result-container');
                resultContainer.style.display = 'block';
                
                // Remove previous classes
                resultContainer.classList.remove('organic', 'recyclable', 'hazardous');
                
                // Add appropriate class
                if (result.class === 'O') {
                    resultContainer.classList.add('organic');
                } else if (result.class === 'R') {
                    resultContainer.classList.add('recyclable');
                } else if (result.class === 'H') {
                    resultContainer.classList.add('hazardous');
                }
                
                document.getElementById('class-name').textContent = result.class_name;
                document.getElementById('confidence').textContent = result.confidence_percentage.toFixed(1);
                
            } catch (error) {
                console.error('Error:', error);
                alert('Error classifying image. Please try again.');
            }
        });
    </script>
</body>
</html>
```

### Example 2: Webcam Integration

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Waste Classification - Webcam</title>
    <style>
        #video-container {
            position: relative;
            max-width: 640px;
            margin: 0 auto;
        }
        #video {
            width: 100%;
            border: 1px solid #ccc;
        }
        .result {
            margin-top: 20px;
            padding: 15px;
            border-radius: 5px;
        }
        .result.organic { background-color: #a8e6cf; }
        .result.recyclable { background-color: #dcedc1; }
        .result.hazardous { background-color: #ffd3b6; }
        .controls {
            margin: 15px 0;
        }
    </style>
</head>
<body>
    <h1>Waste Classification - Webcam</h1>
    
    <div id="video-container">
        <video id="video" autoplay playsinline></video>
    </div>
    
    <div class="controls">
        <button id="start-btn">Start Camera</button>
        <button id="capture-btn" disabled>Capture & Classify</button>
        <button id="stop-btn" disabled>Stop Camera</button>
    </div>
    
    <div id="result-container" style="display: none;" class="result">
        <h2>Result: <span id="class-name"></span></h2>
        <p>Confidence: <span id="confidence"></span>%</p>
    </div>

    <script>
        // DOM Elements
        const video = document.getElementById('video');
        const startBtn = document.getElementById('start-btn');
        const captureBtn = document.getElementById('capture-btn');
        const stopBtn = document.getElementById('stop-btn');
        const resultContainer = document.getElementById('result-container');
        const className = document.getElementById('class-name');
        const confidence = document.getElementById('confidence');
        
        // Global variables
        let stream = null;
        
        // Start camera
        startBtn.addEventListener('click', async () => {
            try {
                stream = await navigator.mediaDevices.getUserMedia({ 
                    video: { 
                        width: { ideal: 640 },
                        height: { ideal: 480 },
                        facingMode: 'environment' 
                    } 
                });
                video.srcObject = stream;
                
                startBtn.disabled = true;
                captureBtn.disabled = false;
                stopBtn.disabled = false;
                
            } catch (error) {
                console.error('Error accessing camera:', error);
                alert('Error accessing camera. Please make sure you have granted camera permissions.');
            }
        });
        
        // Stop camera
        stopBtn.addEventListener('click', () => {
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
                video.srcObject = null;
                
                startBtn.disabled = false;
                captureBtn.disabled = true;
                stopBtn.disabled = true;
            }
        });
        
        // Capture and classify
        captureBtn.addEventListener('click', async () => {
            if (!video.srcObject) return;
            
            // Create canvas and draw video frame
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            
            // Convert to base64
            const imageData = canvas.toDataURL('image/jpeg').split(',')[1];
            
            try {
                const response = await fetch('http://your-flask-server:5000/api/predict', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        image_data: imageData
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                
                const result = await response.json();
                
                // Display result
                resultContainer.style.display = 'block';
                
                // Remove previous classes
                resultContainer.classList.remove('organic', 'recyclable', 'hazardous');
                
                // Add appropriate class
                if (result.class === 'O') {
                    resultContainer.classList.add('organic');
                } else if (result.class === 'R') {
                    resultContainer.classList.add('recyclable');
                } else if (result.class === 'H') {
                    resultContainer.classList.add('hazardous');
                }
                
                className.textContent = result.class_name;
                confidence.textContent = result.confidence_percentage.toFixed(1);
                
            } catch (error) {
                console.error('Error:', error);
                alert('Error classifying image. Please try again.');
            }
        });
    </script>
</body>
</html>
```

## Error Handling

The API returns appropriate HTTP status codes and error messages in case of failures:

```json
{
    "error": "Error message describing what went wrong"
}
```

## Cross-Origin Resource Sharing (CORS)

The API supports CORS, allowing it to be called from different domains. By default, all origins are allowed (`*`), but you can restrict this by setting the `CORS_ALLOWED_ORIGINS` environment variable.

## Rate Limiting

Currently, there is no rate limiting implemented. If you're deploying this in a production environment, consider implementing rate limiting to prevent abuse.

## Versioning

This is version 1.0 of the API. Future versions will be announced with appropriate migration guides.

## Support

For any issues or questions regarding the API, please contact the BOLT INNOVATORS team.