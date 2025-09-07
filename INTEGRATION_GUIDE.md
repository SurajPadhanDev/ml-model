# BOLT INNOVATORS - Waste Classification Integration Guide

## Quick Start Guide for Website Integration

This guide provides step-by-step instructions for integrating the waste classification system into your existing website. The system now features enhanced AI capabilities through Gemini API integration.

## Option 1: Embed as an iframe (Simplest)

### Step 1: Deploy the Flask Application

1. Set up the Flask application on a server or cloud platform
2. Make sure it's accessible via a URL (e.g., `http://your-flask-server:5000`)

### Step 2: Add the iframe to Your Website

Add the following HTML code to the page where you want the waste classifier to appear:

```
<iframe 
  src="http://your-flask-server:5000" 
  width="800" 
  height="600" 
  frameborder="0"
  allow="camera"
  title="Waste Classification System with Gemini AI">
</iframe>
```

Adjust the width and height as needed to fit your website design.

**Note:** For the camera to work, you must use HTTPS if your website is served over HTTPS.

## Option 2: JavaScript Widget (Recommended)

### Step 1: Include Required Files

Add the following to the `<head>` section of your HTML:

```html
<!-- Add Font Awesome for icons -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">

<!-- Add the waste classifier script -->
<script src="http://your-flask-server:5000/static/js/main.js"></script>
```

### Step 2: Add Container Element

Add a container element where you want the widget to appear:

```html
<div id="waste-classifier-container"></div>
```

### Step 3: Initialize the Widget

Add the following JavaScript code before the closing `</body>` tag:

```html
<script>
  document.addEventListener('DOMContentLoaded', function() {
    // Initialize the widget
    const widget = WasteClassifierWidget.init('waste-classifier-container', {
      apiEndpoint: 'http://your-flask-server:5000/api/predict',
      onResult: function(result) {
        console.log('Classification result:', result);
        // You can handle the result here
        // For example, update your website's UI or save to database
      }
    });
    
    // Optional: You can control the widget programmatically
    // document.getElementById('my-start-button').addEventListener('click', function() {
    //   widget.start(); // Start the camera
    // });
    // 
    // document.getElementById('my-stop-button').addEventListener('click', function() {
    //   widget.stop();  // Stop the camera
    // });
    // 
    // document.getElementById('my-capture-button').addEventListener('click', function() {
    //   widget.capture(); // Capture and classify an image
    // });
  });
</script>
```

### Step 4: Customize Styling (Optional)

You can customize the appearance of the widget by adding CSS:

```html
<style>
  #waste-classifier-container {
    max-width: 800px;
    margin: 0 auto;
    border: 1px solid #ddd;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);

## AI Integration Options

### Gemini API Integration

The system now supports Google's Gemini API for enhanced waste classification accuracy. This integration provides state-of-the-art image recognition capabilities.

#### Configuration

To enable Gemini API integration, you need to:

1. Obtain a Gemini API key from Google AI Studio
2. Configure your environment variables:

```
GEMINI_API_KEY=your_api_key_here
PRIORITIZE_EXTERNAL_AI=true
```

#### API Endpoint

The system automatically uses the Gemini API when available. You can also directly access the classification endpoint:

```
POST /api/classify
Content-Type: multipart/form-data

# Form parameters
image: [binary image data]
api: "gemini" # Optional, defaults to system preference
```

#### Response Format

```json
{
  "classification": "recyclable", 
  "confidence": 0.95,
  "source": "gemini_api",
  "processing_time": 0.45
}
```
  }
  
  /* Override widget colors if needed */
  #waste-classifier-container .result-container {
    background-color: #f9f9f9;
  }
</style>
```

### Real-Time Image Upload Detection

The system now includes real-time image upload detection with automatic classification. This feature allows for seamless processing of images as they are uploaded to your platform.

#### Configuration

To enable real-time image upload detection:

```javascript
// Initialize the image upload detector
const uploadDetector = new ImageUploadDetector({
  targetSelector: '#file-upload-area', // The file upload area selector
  onImageDetected: function(imageData) {
    console.log('Image detected and being processed automatically');
  },
  onClassificationComplete: function(result) {
    console.log('Classification result:', result);
    // Handle the classification result
    displayResult(result);
  }
});

// Start monitoring for uploads
uploadDetector.start();
```

#### Event Handlers

You can register custom event handlers for various stages of the process:

```javascript
uploadDetector.registerEventHandler('image_detected', function(imageData) {
  // Show loading indicator
  showLoadingSpinner();
});

uploadDetector.registerEventHandler('classification_complete', function(result) {
  // Hide loading indicator
  hideLoadingSpinner();
  // Show classification result
  showClassificationResult(result);
});
```

#### Statistics Tracking

The detector also provides statistics tracking:

```javascript
const stats = uploadDetector.getStatistics();
console.log(`Total images processed: ${stats.totalProcessed}`);
console.log(`Average processing time: ${stats.averageProcessingTime}ms`);
```

## Option 3: Direct API Integration (Advanced)

For complete control over the UI and functionality, you can integrate directly with the API.

### Step 1: Set Up Your UI

Create your own UI elements for camera access, image upload, and result display.

### Step 2: Implement API Calls

#### Example: Classify from Webcam

```javascript
// Access the camera
async function startCamera() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ 
      video: { 
        width: { ideal: 640 },
        height: { ideal: 480 },
        facingMode: 'environment' 
      } 
    });
    document.getElementById('my-video').srcObject = stream;
    return stream;
  } catch (error) {
    console.error('Error accessing camera:', error);
    throw error;
  }
}

// Capture and classify image
async function captureAndClassify() {
  const video = document.getElementById('my-video');
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
        image_data: imageData,
        api_preference: 'gemini'  // Specify to use Gemini API instead of local model
      })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    
    const result = await response.json();
    displayResult(result);
    return result;
  } catch (error) {
    console.error('Classification error:', error);
    throw error;
  }
}

// Display the result in your custom UI
function displayResult(result) {
  const resultElement = document.getElementById('my-result');
  
  // Create result HTML with enhanced information
  const resultHTML = `
    <div class="result-card">
      <h3>Classification Result</h3>
      <p class="classification">Type: ${result.class_name}</p>
      <p class="confidence">Confidence: ${result.confidence_percentage.toFixed(1)}%</p>
      <p class="source">Source: ${result.source || 'Local Model'}</p>
      <p class="time">Processing Time: ${result.processing_time || '0.00'}s</p>
    </div>
  `;
  
  resultElement.innerHTML = resultHTML;
  
  // Apply styling based on waste type
  resultElement.className = 'result';
  if (result.class === 'O') {
    resultElement.classList.add('organic');
  } else if (result.class === 'R') {
    resultElement.classList.add('recyclable');
  } else if (result.class === 'H') {
    resultElement.classList.add('hazardous');
  }
}
```

#### Example: Classify from File Upload

```javascript
// Handle file upload
document.getElementById('my-file-input').addEventListener('change', async function(e) {
  const file = e.target.files[0];
  if (!file) return;
  
  try {
    const result = await classifyImageFile(file);
    displayResult(result);
  } catch (error) {
    console.error('Error:', error);
    alert('Error classifying image. Please try again.');
  }
});

// Classify image file
async function classifyImageFile(file) {
  const formData = new FormData();
  formData.append('image', file);
  
  try {
    const response = await fetch('http://your-flask-server:5000/api/predict', {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Classification error:', error);
    throw error;
  }
}
```

## Security Considerations

1. **CORS Configuration**: By default, the API allows requests from any origin. For production, configure the `CORS_ALLOWED_ORIGINS` environment variable to restrict access to your domain.

2. **HTTPS**: Always use HTTPS in production for secure communication and to enable camera access on modern browsers.

3. **API Authentication**: For production use, consider implementing API keys or other authentication mechanisms.

## Troubleshooting

### Camera Not Working

- Ensure your website is served over HTTPS
- Check browser permissions for camera access
- Try a different browser (Chrome or Firefox recommended)

### Classification Issues

- Ensure good lighting for better classification results
- Position objects clearly in the center of the frame
- If classification seems inaccurate, try capturing from different angles

### CORS Errors

If you see CORS errors in the browser console:

1. Make sure the Flask server has CORS properly configured
2. Check that your domain is included in the `CORS_ALLOWED_ORIGINS` setting
3. For testing, you can temporarily set `CORS_ALLOWED_ORIGINS=*` to allow all origins

## Need Help?

For additional assistance, refer to the full documentation or contact the BOLT INNOVATORS team.