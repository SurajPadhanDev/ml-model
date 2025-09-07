/**
 * BOLT INNOVATORS - Smart Waste Classification System
 * Main JavaScript for webcam handling and API interactions
 * 
 * This file supports both standalone mode and widget integration mode
 */

// Check if running in widget mode
const urlParams = new URLSearchParams(window.location.search);
const isWidget = urlParams.get('widget') === 'true';
const autoStart = urlParams.get('autoStart') === 'true';
const showWebcam = urlParams.get('showWebcam') !== 'false';
const showUpload = urlParams.get('showUpload') !== 'false';

// DOM Elements
const webcamElement = document.getElementById('webcam');
const canvasElement = document.getElementById('canvas');
const startCameraBtn = document.getElementById('start-camera');
const stopCameraBtn = document.getElementById('stop-camera');
const captureImageBtn = document.getElementById('capture-image');
const predictionResult = document.getElementById('prediction-result');
const confidenceValue = document.getElementById('confidence-value');
const confidenceBar = document.getElementById('confidence-bar');
const cameraStatus = document.getElementById('camera-status').querySelector('span');
const predictionOverlay = document.getElementById('prediction-overlay');
const fileInput = document.getElementById('file-input');
const fileName = document.getElementById('file-name');
const uploadForm = document.getElementById('upload-form');
const previewContainer = document.getElementById('preview-container');
const imagePreview = document.getElementById('image-preview');

// Global variables
let stream = null;
let isClassifying = false;
let classificationInterval = null;
let mobileStream = null;

// Camera capture elements
let mobileCamera = document.getElementById('mobile-camera');
let mobileCaptureBtn = document.getElementById('mobile-capture-btn');
let retakeBtn = document.getElementById('retake-btn');
let uploadTab = document.getElementById('upload-tab');
let captureTab = document.getElementById('capture-tab');
let uploadContent = document.getElementById('upload-content');
let captureContent = document.getElementById('capture-content');

// API endpoint
const API_ENDPOINT = '/api/predict';

// Hide elements based on widget configuration
document.addEventListener('DOMContentLoaded', function() {
    // Hide webcam section if not needed
    if (!showWebcam) {
        const videoContainer = document.querySelector('.video-container');
        if (videoContainer) {
            videoContainer.style.display = 'none';
        }
    }
    
    // Hide upload section if not needed
    if (!showUpload) {
        const uploadContainer = document.querySelector('.upload-container');
        if (uploadContainer) {
            uploadContainer.style.display = 'none';
        }
    }
    
    // Auto start camera if configured
    if (autoStart && showWebcam) {
        setTimeout(() => {
            startCamera();
        }, 1000);
    }
});

// Widget communication
if (isWidget) {
    // Listen for messages from parent window
    window.addEventListener('message', function(event) {
        // Verify origin if needed for security
        // if (event.origin !== "https://allowed-parent-domain.com") return;
        
        const data = event.data;
        
        if (data.action === 'startCamera') {
            startCamera();
        } else if (data.action === 'stopCamera') {
            stopCamera();
        } else if (data.action === 'captureImage') {
            captureImage();
        }
    });
    
    // Function to send results to parent window
    function sendResultToParent(result) {
        if (window.parent && window.parent !== window) {
            window.parent.postMessage({
                type: 'classification-result',
                result: result
            }, '*');
        }
    }
}

/**
 * Start the webcam
 */
async function startCamera() {
    try {
        cameraStatus.textContent = 'Connecting...';
        cameraStatus.style.color = 'var(--warning-color)';
        
        stream = await navigator.mediaDevices.getUserMedia({
            video: {
                width: { ideal: 640 },
                height: { ideal: 480 },
                facingMode: 'environment' // Use back camera on mobile if available
            },
            audio: false
        });
        
        webcamElement.srcObject = stream;
        
        // Wait for video to be ready
        await new Promise(resolve => {
            webcamElement.onloadedmetadata = () => {
                resolve();
            };
        });
        
        // Update UI
        cameraStatus.textContent = 'Connected';
        cameraStatus.style.color = 'var(--primary-color)';
        startCameraBtn.disabled = true;
        stopCameraBtn.disabled = false;
        captureImageBtn.disabled = false;
        
        // Start continuous classification if checkbox is checked
        startContinuousClassification();
        
    } catch (error) {
        console.error('Error accessing camera:', error);
        cameraStatus.textContent = 'Error: ' + (error.message || 'Could not access camera');
        cameraStatus.style.color = 'var(--danger-color)';
    }
}

/**
 * Stop the webcam
 */
function stopCamera() {
    try {
        // Disable the stop button during processing to prevent multiple clicks
        stopCameraBtn.disabled = true;
        
        if (stream) {
            // Stop all tracks
            stream.getTracks().forEach(track => {
                try {
                    track.stop();
                } catch (trackError) {
                    console.error('Error stopping track:', trackError);
                }
            });
            
            webcamElement.srcObject = null;
            stream = null;
            
            // Stop continuous classification
            stopContinuousClassification();
            
            // Update UI
            cameraStatus.textContent = 'Disconnected';
            cameraStatus.style.color = 'var(--warning-color)';
            startCameraBtn.disabled = false;
            stopCameraBtn.disabled = true;
            captureImageBtn.disabled = true;
            predictionOverlay.style.display = 'none';
            
            // Clear any previous results
            predictionResult.textContent = 'Waiting for image...';
            predictionResult.className = '';
            confidenceValue.textContent = '0%';
            confidenceBar.style.width = '0%';
        } else {
            // Camera is already stopped, just update UI
            cameraStatus.textContent = 'Not connected';
            cameraStatus.style.color = 'var(--warning-color)';
            startCameraBtn.disabled = false;
            stopCameraBtn.disabled = true;
            captureImageBtn.disabled = true;
        }
    } catch (error) {
        console.error('Error stopping camera:', error);
        
        // Even if there's an error, try to reset the UI state
        cameraStatus.textContent = 'Error: ' + (error.message || 'Failed to stop camera');
        cameraStatus.style.color = 'var(--danger-color)';
        startCameraBtn.disabled = false;
        stopCameraBtn.disabled = false; // Allow retry
        captureImageBtn.disabled = true;
        
        // Try to clean up as much as possible
        if (stream) {
            try {
                stream.getTracks().forEach(track => track.stop());
                webcamElement.srcObject = null;
                stream = null;
            } catch (cleanupError) {
                console.error('Error during cleanup:', cleanupError);
            }
        }
        
        // Stop continuous classification
        stopContinuousClassification();
    }
}

/**
 * Capture image from webcam
 */
function captureImage() {
    try {
        // Check if stream is available
        if (!stream) {
            console.error('Camera stream not available');
            cameraStatus.textContent = 'Error: Camera not active';
            cameraStatus.style.color = 'var(--danger-color)';
            return;
        }
        
        // Disable the capture button during processing to prevent multiple clicks
        captureImageBtn.disabled = true;
        
        // Visual feedback that capture is in progress
        captureImageBtn.classList.add('processing');
        
        const context = canvasElement.getContext('2d');
        canvasElement.width = webcamElement.videoWidth;
        canvasElement.height = webcamElement.videoHeight;
        context.drawImage(webcamElement, 0, 0, canvasElement.width, canvasElement.height);
        
        // Get image data as base64
        const imageData = canvasElement.toDataURL('image/jpeg');
        
        // Classify the captured image
        classifyImage(imageData)
            .finally(() => {
                // Re-enable the capture button when processing is complete
                captureImageBtn.disabled = false;
                captureImageBtn.classList.remove('processing');
            });
    } catch (error) {
        console.error('Error capturing image:', error);
        predictionResult.textContent = 'Error: ' + (error.message || 'Failed to capture image');
        predictionResult.className = 'result-uncertain';
        
        // Re-enable the button
        captureImageBtn.disabled = false;
        captureImageBtn.classList.remove('processing');
        
        // Update status
        cameraStatus.textContent = 'Error: ' + (error.message || 'Capture failed');
        cameraStatus.style.color = 'var(--danger-color)';
    }
}

/**
 * Start continuous classification
 */
function startContinuousClassification() {
    if (classificationInterval) {
        clearInterval(classificationInterval);
    }
    
    // Classify every 1 second
    classificationInterval = setInterval(() => {
        if (!isClassifying && stream) {
            captureImage();
        }
    }, 1000);
}

/**
 * Stop continuous classification
 */
function stopContinuousClassification() {
    if (classificationInterval) {
        clearInterval(classificationInterval);
        classificationInterval = null;
    }
}

/**
 * Classify image using API
 */
async function classifyImage(imageData) {
    if (isClassifying) return;
    isClassifying = true;
    
    // Add visual feedback for classification in progress
    predictionOverlay.textContent = 'Processing...';
    predictionOverlay.style.display = 'block';
    predictionOverlay.className = 'overlay processing';
    
    try {
        // Show loading state
        predictionResult.textContent = 'Classifying...';
        predictionResult.className = '';
        
        // Handle different types of input
        let fetchOptions = {};
        
        if (typeof imageData === 'string' && imageData.startsWith('data:image')) {
            // Handle base64 image data
            const requestData = {
                image_data: imageData.split(',')[1] // Remove data URL prefix
            };
            
            fetchOptions = {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            };
        } else {
            // Handle FormData (file upload)
            fetchOptions = {
                method: 'POST',
                body: imageData
            };
        }
        
        // Call API
        const response = await fetch(API_ENDPOINT, fetchOptions);
        
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        const result = await response.json();
        displayResult(result);
        
    } catch (error) {
        console.error('Classification error:', error);
        predictionResult.textContent = 'Error: ' + (error.message || 'Classification failed');
        predictionResult.className = 'result-uncertain';
        confidenceValue.textContent = '0%';
        confidenceBar.style.width = '0%';
    } finally {
        isClassifying = false;
    }
}

/**
 * Display classification result
 */
function displayResult(result) {
    // Update confidence meter
    const confidencePercentage = result.confidence_percentage;
    confidenceValue.textContent = `${confidencePercentage}%`;
    confidenceBar.style.width = `${confidencePercentage}%`;
    
    // Set color based on confidence
    if (confidencePercentage > 90) {
        confidenceBar.style.backgroundColor = 'var(--primary-color)';
    } else if (confidencePercentage > 70) {
        confidenceBar.style.backgroundColor = 'var(--warning-color)';
    } else {
        confidenceBar.style.backgroundColor = 'var(--danger-color)';
    }
    
    // Update prediction text
    let resultText = '';
    let resultClass = '';
    
    if (!result.is_confident) {
        resultText = `Uncertain (${confidencePercentage}%)`;
        resultClass = 'result-uncertain';
    } else {
        switch (result.class) {
            case 'R':
                resultText = `ORGANIC (${confidencePercentage}%)`;
                resultClass = 'result-organic';
                break;
            case 'H':
                resultText = `RECYCLABLE (${confidencePercentage}%)`;
                resultClass = 'result-recyclable';
                break;
            case 'O':
                resultText = `HAZARDOUS (${confidencePercentage}%)`;
                resultClass = 'result-hazardous';
                break;
            default:
                resultText = `${result.class_name} (${confidencePercentage}%)`;
        }
    }
    
    predictionResult.textContent = resultText;
    predictionResult.className = resultClass;
    predictionResult.classList.add('highlight');
    
    // Show overlay on video
    predictionOverlay.textContent = resultText;
    predictionOverlay.style.display = 'block';
    predictionOverlay.className = 'overlay ' + resultClass;
    
    // Remove highlight animation after it completes
    setTimeout(() => {
        predictionResult.classList.remove('highlight');
    }, 1000);
    
    // If in widget mode, send result to parent window
    if (isWidget) {
        sendResultToParent(result);
    }
}

/**
 * Handle file input change
 */
fileInput.addEventListener('change', function() {
    if (this.files && this.files[0]) {
        const file = this.files[0];
        fileName.textContent = file.name;
        
        // Show preview
        const reader = new FileReader();
        reader.onload = function(e) {
            imagePreview.src = e.target.result;
            previewContainer.style.display = 'block';
        };
        reader.readAsDataURL(file);
    } else {
        fileName.textContent = 'No file chosen';
        previewContainer.style.display = 'none';
    }
});

/**
 * Handle form submission for file upload
 */
uploadForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    if (!fileInput.files || !fileInput.files[0]) {
        alert('Please select an image file first.');
        return;
    }
    
    try {
        // Show loading state
        predictionResult.textContent = 'Classifying...';
        predictionResult.className = '';
        
        // Prepare form data
        const formData = new FormData();
        formData.append('image', fileInput.files[0]);
        
        // Call API
        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        const result = await response.json();
        displayResult(result);
        
    } catch (error) {
        console.error('Classification error:', error);
        predictionResult.textContent = 'Error: ' + (error.message || 'Classification failed');
        predictionResult.className = 'result-uncertain';
        confidenceValue.textContent = '0%';
        confidenceBar.style.width = '0%';
    }
});

// Event listeners with debounce to prevent multiple rapid clicks
let startCameraBtnClickTimeout = null;
startCameraBtn.addEventListener('click', function(e) {
    // Prevent multiple rapid clicks
    if (startCameraBtnClickTimeout) return;
    
    // Disable button immediately to prevent double clicks
    startCameraBtn.disabled = true;
    
    // Set a short timeout to prevent multiple clicks
    startCameraBtnClickTimeout = setTimeout(function() {
        startCamera();
        startCameraBtnClickTimeout = null;
    }, 100);
});

let stopCameraBtnClickTimeout = null;
stopCameraBtn.addEventListener('click', function(e) {
    // Prevent multiple rapid clicks
    if (stopCameraBtnClickTimeout) return;
    
    // Disable button immediately to prevent double clicks
    stopCameraBtn.disabled = true;
    
    // Set a short timeout to prevent multiple clicks
    stopCameraBtnClickTimeout = setTimeout(function() {
        stopCamera();
        stopCameraBtnClickTimeout = null;
    }, 100);
});

let captureImageBtnClickTimeout = null;
captureImageBtn.addEventListener('click', function(e) {
    // Prevent multiple rapid clicks
    if (captureImageBtnClickTimeout) return;
    
    // Disable button immediately to prevent double clicks
    captureImageBtn.disabled = true;
    captureImageBtn.classList.add('processing');
    
    // Set a short timeout to prevent multiple clicks
    captureImageBtnClickTimeout = setTimeout(function() {
        captureImage();
        captureImageBtnClickTimeout = null;
    }, 100);
});

// Function to capture image from mobile camera
function captureMobileImage() {
    try {
        if (!mobileStream) {
            console.error('Mobile camera stream not available');
            return;
        }
        
        // Disable the capture button during processing
        if (mobileCaptureBtn) {
            mobileCaptureBtn.disabled = true;
            mobileCaptureBtn.classList.add('processing');
        }
        
        // Create a temporary canvas
        const tempCanvas = document.createElement('canvas');
        const context = tempCanvas.getContext('2d');
        tempCanvas.width = mobileCamera.videoWidth;
        tempCanvas.height = mobileCamera.videoHeight;
        context.drawImage(mobileCamera, 0, 0, tempCanvas.width, tempCanvas.height);
        
        // Get image data as base64
        const imageData = tempCanvas.toDataURL('image/jpeg');
        
        // Show preview
        imagePreview.src = imageData;
        imagePreview.style.display = 'block';
        mobileCamera.style.display = 'none';
        
        if (mobileCaptureBtn) mobileCaptureBtn.style.display = 'none';
        if (retakeBtn) retakeBtn.style.display = 'inline-block';
        if (classifyBtn) classifyBtn.style.display = 'inline-block';
        
        // Stop the camera stream
        stopMobileCamera();
        
    } catch (error) {
        console.error('Error capturing mobile image:', error);
        
        // Show error message
        const errorMessage = document.createElement('div');
        errorMessage.className = 'camera-error';
        errorMessage.textContent = 'Capture failed: ' + (error.message || 'Unknown error');
        
        // Insert error message
        if (mobileCamera.parentNode) {
            mobileCamera.parentNode.insertBefore(errorMessage, mobileCamera);
        }
        
        // Re-enable the button
        if (mobileCaptureBtn) {
            mobileCaptureBtn.disabled = false;
            mobileCaptureBtn.classList.remove('processing');
        }
    }
}

// Add debounce mechanism to mobile capture button
if (mobileCaptureBtn) {
    let mobileCaptureTimeout = null;
    mobileCaptureBtn.addEventListener('click', function() {
        // Prevent multiple rapid clicks
        if (mobileCaptureTimeout) return;
        
        // Disable button immediately
        mobileCaptureBtn.disabled = true;
        mobileCaptureBtn.classList.add('processing');
        
        // Set a short timeout to prevent multiple clicks
        mobileCaptureTimeout = setTimeout(function() {
            captureMobileImage();
            mobileCaptureTimeout = null;
        }, 100);
    });
}

// Function to stop mobile camera
function stopMobileCamera() {
    try {
        if (mobileStream) {
            // Stop all tracks
            mobileStream.getTracks().forEach(track => {
                try {
                    track.stop();
                } catch (trackError) {
                    console.error('Error stopping mobile track:', trackError);
                }
            });
            
            // Clear the stream
            mobileStream = null;
            
            // Clear the video source if it exists
            if (mobileCamera) {
                mobileCamera.srcObject = null;
            }
        }
    } catch (error) {
        console.error('Error stopping mobile camera:', error);
        // Even if there's an error, try to clean up as much as possible
        mobileStream = null;
        if (mobileCamera) mobileCamera.srcObject = null;
        
        // Show error message
        const errorMessage = document.createElement('div');
        errorMessage.className = 'camera-error';
        errorMessage.textContent = 'Error stopping camera: ' + (error.message || 'Unknown error');
        
        if (mobileCamera && mobileCamera.parentNode) {
            mobileCamera.parentNode.insertBefore(errorMessage, mobileCamera);
        }
    }
}

// Retake photo
if (retakeBtn) {
    retakeBtn.addEventListener('click', function() {
        try {
            // Hide preview and show camera
            imagePreview.style.display = 'none';
            retakeBtn.style.display = 'none';
            mobileCamera.style.display = 'block';
            mobileCaptureBtn.style.display = 'block';
            
            // Remove any error messages
            const errorMessages = document.querySelectorAll('.camera-error');
            errorMessages.forEach(msg => msg.remove());
            
            // Restart mobile camera
            startMobileCamera();
        } catch (error) {
            console.error('Error retaking photo:', error);
            
            // Show error message
            const errorMessage = document.createElement('div');
            errorMessage.className = 'camera-error';
            errorMessage.textContent = 'Failed to retake photo: ' + (error.message || 'Unknown error');
            
            if (mobileCamera.parentNode) {
                mobileCamera.parentNode.insertBefore(errorMessage, mobileCamera);
            }
        }
    });
}

// Tab switching
if (uploadTab && captureTab) {
    uploadTab.addEventListener('click', function() {
        uploadTab.classList.add('active');
        captureTab.classList.remove('active');
        uploadContent.style.display = 'block';
        captureContent.style.display = 'none';
        
        // Stop mobile camera if it's running
        if (mobileStream) {
            mobileStream.getTracks().forEach(track => track.stop());
            mobileStream = null;
        }
    });
    
    captureTab.addEventListener('click', function() {
        captureTab.classList.add('active');
        uploadTab.classList.remove('active');
        captureContent.style.display = 'block';
        uploadContent.style.display = 'none';
        
        // Start mobile camera
        startMobileCamera();
    });
}

// Function to start mobile camera
async function startMobileCamera() {
    if (mobileCamera && navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        try {
            // Show loading state
            if (mobileCaptureBtn) mobileCaptureBtn.disabled = true;
            
            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: 'environment'
                },
                audio: false
            });
            
            mobileStream = stream;
            mobileCamera.srcObject = stream;
            await mobileCamera.play();
            
            // Enable capture button once camera is ready
            if (mobileCaptureBtn) mobileCaptureBtn.disabled = false;
            
        } catch (error) {
            console.error('Error accessing mobile camera:', error);
            
            // Show error message to user
            const errorMessage = document.createElement('div');
            errorMessage.className = 'camera-error';
            errorMessage.textContent = 'Camera access failed: ' + (error.message || 'Please check permissions');
            
            // Insert error message before the camera element
            if (mobileCamera.parentNode) {
                mobileCamera.parentNode.insertBefore(errorMessage, mobileCamera);
            }
            
            // Re-enable tab switching
            if (uploadTab) uploadTab.disabled = false;
        }
    }
}

// Check if browser supports getUserMedia
if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    cameraStatus.textContent = 'Camera not supported in this browser';
    cameraStatus.style.color = 'var(--danger-color)';
    startCameraBtn.disabled = true;
    
    if (captureTab) {
        captureTab.disabled = true;
        captureTab.style.opacity = 0.5;
        captureTab.title = 'Camera not supported on your device';
    }
}

// Create a standalone widget version for embedding
window.WasteClassifierWidget = {
    init: function(containerId, options = {}) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error('Container element not found:', containerId);
            return;
        }
        
        // Create widget HTML
        const widgetHtml = `
            <div class="waste-classifier-widget">
                <div class="widget-header">
                    <h3>Waste Classification</h3>
                </div>
                <div class="widget-body">
                    <div class="widget-video-container">
                        <video id="widget-webcam-${containerId}" autoplay playsinline></video>
                        <canvas id="widget-canvas-${containerId}" style="display: none;"></canvas>
                        <div class="widget-overlay" id="widget-overlay-${containerId}"></div>
                    </div>
                    <div class="widget-controls">
                        <button id="widget-start-${containerId}" class="widget-btn primary">
                            <i class="fas fa-play"></i> Start
                        </button>
                        <button id="widget-capture-${containerId}" class="widget-btn secondary" disabled>
                            <i class="fas fa-camera"></i> Capture
                        </button>
                        <button id="widget-stop-${containerId}" class="widget-btn danger" disabled>
                            <i class="fas fa-stop"></i> Stop
                        </button>
                    </div>
                    <div class="widget-result" id="widget-result-${containerId}">
                        Waiting for image...
                    </div>
                </div>
            </div>
        `;
        
        // Insert widget HTML
        container.innerHTML = widgetHtml;
        
        // Add widget CSS if not already added
        if (!document.getElementById('waste-classifier-widget-css')) {
            const widgetStyle = document.createElement('style');
            widgetStyle.id = 'waste-classifier-widget-css';
            widgetStyle.textContent = `
                .waste-classifier-widget {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: #1E1E2E;
                    color: #f8f8f2;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    max-width: 100%;
                }
                
                .widget-header {
                    background-color: #282a36;
                    padding: 10px 15px;
                    text-align: center;
                }
                
                .widget-header h3 {
                    margin: 0;
                    font-size: 16px;
                    color: #8be9fd;
                }
                
                .widget-body {
                    padding: 15px;
                }
                
                .widget-video-container {
                    position: relative;
                    margin-bottom: 15px;
                }
                
                .widget-video-container video {
                    width: 100%;
                    border-radius: 8px;
                    background-color: #000;
                    aspect-ratio: 4/3;
                    object-fit: cover;
                }
                
                .widget-overlay {
                    position: absolute;
                    bottom: 0;
                    left: 0;
                    width: 100%;
                    padding: 8px;
                    background-color: rgba(40, 42, 54, 0.8);
                    color: white;
                    border-bottom-left-radius: 8px;
                    border-bottom-right-radius: 8px;
                    display: none;
                    font-size: 14px;
                    text-align: center;
                }
                
                .widget-controls {
                    display: flex;
                    justify-content: center;
                    gap: 8px;
                    margin-bottom: 15px;
                }
                
                .widget-btn {
                    padding: 6px 12px;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-weight: bold;
                    font-size: 12px;
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.3s ease;
                }
                
                .widget-btn i {
                    margin-right: 5px;
                }
                
                .widget-btn.primary {
                    background-color: #50fa7b;
                    color: #282a36;
                }
                
                .widget-btn.secondary {
                    background-color: #8be9fd;
                    color: #282a36;
                }
                
                .widget-btn.danger {
                    background-color: #ff5555;
                    color: white;
                }
                
                .widget-btn:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                }
                
                .widget-result {
                    padding: 10px;
                    background-color: #282a36;
                    border-radius: 4px;
                    text-align: center;
                    min-height: 40px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                
                .widget-result.organic {
                    color: #50fa7b;
                    border-left: 3px solid #50fa7b;
                }
                
                .widget-result.recyclable {
                    color: #8be9fd;
                    border-left: 3px solid #8be9fd;
                }
                
                .widget-result.hazardous {
                    color: #ff5555;
                    border-left: 3px solid #ff5555;
                }
                
                .widget-result.uncertain {
                    color: #f1fa8c;
                    border-left: 3px solid #f1fa8c;
                }
            `;
            document.head.appendChild(widgetStyle);
        }
        
        // Initialize widget functionality
        const widgetElements = {
            webcam: document.getElementById(`widget-webcam-${containerId}`),
            canvas: document.getElementById(`widget-canvas-${containerId}`),
            startBtn: document.getElementById(`widget-start-${containerId}`),
            captureBtn: document.getElementById(`widget-capture-${containerId}`),
            stopBtn: document.getElementById(`widget-stop-${containerId}`),
            result: document.getElementById(`widget-result-${containerId}`),
            overlay: document.getElementById(`widget-overlay-${containerId}`)
        };
        
        let widgetStream = null;
        let widgetClassifying = false;
        let widgetInterval = null;
        
        // Start camera function
        async function widgetStartCamera() {
            try {
                widgetElements.result.textContent = 'Connecting camera...';
                widgetElements.result.className = '';
                
                widgetStream = await navigator.mediaDevices.getUserMedia({
                    video: {
                        width: { ideal: 640 },
                        height: { ideal: 480 },
                        facingMode: 'environment'
                    },
                    audio: false
                });
                
                widgetElements.webcam.srcObject = widgetStream;
                
                // Wait for video to be ready
                await new Promise(resolve => {
                    widgetElements.webcam.onloadedmetadata = () => {
                        resolve();
                    };
                });
                
                // Update UI
                widgetElements.result.textContent = 'Camera ready. Classifying...';
                widgetElements.startBtn.disabled = true;
                widgetElements.stopBtn.disabled = false;
                widgetElements.captureBtn.disabled = false;
                
                // Start continuous classification
                if (widgetInterval) {
                    clearInterval(widgetInterval);
                }
                
                widgetInterval = setInterval(() => {
                    if (!widgetClassifying && widgetStream) {
                        widgetCaptureImage();
                    }
                }, 1000);
                
            } catch (error) {
                console.error('Widget camera error:', error);
                widgetElements.result.textContent = 'Error: ' + (error.message || 'Could not access camera');
                widgetElements.result.className = 'widget-result uncertain';
            }
        }
        
        // Stop camera function
        function widgetStopCamera() {
            try {
                // Disable the stop button during processing to prevent multiple clicks
                widgetElements.stopBtn.disabled = true;
                
                if (widgetStream) {
                    // Stop all tracks
                    widgetStream.getTracks().forEach(track => {
                        try {
                            track.stop();
                        } catch (trackError) {
                            console.error('Error stopping widget track:', trackError);
                        }
                    });
                    
                    widgetElements.webcam.srcObject = null;
                    widgetStream = null;
                    
                    if (widgetInterval) {
                        clearInterval(widgetInterval);
                        widgetInterval = null;
                    }
                    
                    // Update UI
                    widgetElements.result.textContent = 'Camera stopped';
                    widgetElements.startBtn.disabled = false;
                    widgetElements.stopBtn.disabled = true;
                    widgetElements.captureBtn.disabled = true;
                    widgetElements.overlay.style.display = 'none';
                } else {
                    // Camera is already stopped, just update UI
                    widgetElements.result.textContent = 'Not connected';
                    widgetElements.startBtn.disabled = false;
                    widgetElements.stopBtn.disabled = true;
                    widgetElements.captureBtn.disabled = true;
                }
            } catch (error) {
                console.error('Error stopping widget camera:', error);
                
                // Even if there's an error, try to reset the UI state
                widgetElements.result.textContent = 'Error: ' + (error.message || 'Failed to stop camera');
                widgetElements.startBtn.disabled = false;
                widgetElements.stopBtn.disabled = false; // Allow retry
                widgetElements.captureBtn.disabled = true;
                
                // Try to clean up as much as possible
                if (widgetStream) {
                    try {
                        widgetStream.getTracks().forEach(track => track.stop());
                        widgetElements.webcam.srcObject = null;
                        widgetStream = null;
                    } catch (cleanupError) {
                        console.error('Error during widget cleanup:', cleanupError);
                    }
                }
                
                // Clear interval if it exists
                if (widgetInterval) {
                    clearInterval(widgetInterval);
                    widgetInterval = null;
                }
            }
        }
        
        // Capture image function
        function widgetCaptureImage() {
            try {
                // Check if stream is available
                if (!widgetStream) {
                    console.error('Widget camera stream not available');
                    widgetElements.result.textContent = 'Error: Camera not active';
                    return;
                }
                
                // Disable the capture button during processing to prevent multiple clicks
                widgetElements.captureBtn.disabled = true;
                widgetElements.captureBtn.classList.add('processing');
                
                const context = widgetElements.canvas.getContext('2d');
                widgetElements.canvas.width = widgetElements.webcam.videoWidth;
                widgetElements.canvas.height = widgetElements.webcam.videoHeight;
                context.drawImage(widgetElements.webcam, 0, 0, widgetElements.canvas.width, widgetElements.canvas.height);
                
                // Get image data
                const imageData = widgetElements.canvas.toDataURL('image/jpeg');
                
                // Classify
                widgetClassifyImage(imageData)
                    .finally(() => {
                        // Re-enable the capture button when processing is complete
                        widgetElements.captureBtn.disabled = false;
                        widgetElements.captureBtn.classList.remove('processing');
                    });
            } catch (error) {
                console.error('Error capturing widget image:', error);
                widgetElements.result.textContent = 'Error: ' + (error.message || 'Failed to capture image');
                
                // Re-enable the button
                widgetElements.captureBtn.disabled = false;
                widgetElements.captureBtn.classList.remove('processing');
            }
        }
        
        // Classify image function
        async function widgetClassifyImage(imageData) {
            if (widgetClassifying) return;
            widgetClassifying = true;
            
            // Add visual feedback for classification in progress
            widgetElements.overlay.textContent = 'Processing...';
            widgetElements.overlay.style.display = 'block';
            widgetElements.overlay.className = 'widget-overlay processing';
            
            try {
                // Prepare data
                const requestData = {
                    image_data: imageData.split(',')[1]
                };
                
                // Call API
                const response = await fetch(options.apiEndpoint || API_ENDPOINT, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(requestData)
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                
                const result = await response.json();
                widgetDisplayResult(result);
                
            } catch (error) {
                console.error('Widget classification error:', error);
                widgetElements.result.textContent = 'Error: Classification failed';
                widgetElements.result.className = 'widget-result uncertain';
            } finally {
                widgetClassifying = false;
            }
        }
        
        // Display result function
        function widgetDisplayResult(result) {
            // Update result text
            let resultText = '';
            let resultClass = '';
            
            if (!result.is_confident) {
                resultText = `Uncertain (${result.confidence_percentage}%)`;
                resultClass = 'uncertain';
            } else {
                switch (result.class) {
                    case 'R':
                        resultText = `ORGANIC (${result.confidence_percentage}%)`;
                        resultClass = 'organic';
                        break;
                    case 'H':
                        resultText = `RECYCLABLE (${result.confidence_percentage}%)`;
                        resultClass = 'recyclable';
                        break;
                    case 'O':
                        resultText = `HAZARDOUS (${result.confidence_percentage}%)`;
                        resultClass = 'hazardous';
                        break;
                    default:
                        resultText = `${result.class_name} (${result.confidence_percentage}%)`;
                }
            }
            
            widgetElements.result.textContent = resultText;
            widgetElements.result.className = 'widget-result ' + resultClass;
            
            // Show overlay
            widgetElements.overlay.textContent = resultText;
            widgetElements.overlay.style.display = 'block';
            widgetElements.overlay.className = 'widget-overlay ' + resultClass;
            
            // Trigger callback if provided
            if (typeof options.onResult === 'function') {
                options.onResult(result);
            }
        }
        
        // Add event listeners with debounce to prevent multiple rapid clicks
        widgetElements.startBtn.addEventListener('click', function(e) {
            // Disable button immediately to prevent double clicks
            widgetElements.startBtn.disabled = true;
            widgetStartCamera();
        });
        
        widgetElements.stopBtn.addEventListener('click', function(e) {
            // Disable button immediately to prevent double clicks
            widgetElements.stopBtn.disabled = true;
            widgetStopCamera();
        });
        
        widgetElements.captureBtn.addEventListener('click', function(e) {
            // Disable button immediately to prevent double clicks
            widgetElements.captureBtn.disabled = true;
            widgetCaptureImage();
        });
        
        // Return control methods
        return {
            start: widgetStartCamera,
            stop: widgetStopCamera,
            capture: widgetCaptureImage
        };
    }
};