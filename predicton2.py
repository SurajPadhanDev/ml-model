import tensorflow as tf
from tensorflow.keras.models import load_model
import numpy as np
import cv2
import os
import re
from collections import deque
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
import base64
from io import BytesIO

# -----------------------------
# Load trained model
# -----------------------------
model_path = "/Users/surajpadhan/Desktop/mode code web/best_mobilenetv2_model.keras"
model = load_model(model_path)
print("✅ Model loaded successfully!")

# Classes
classes = ["O", "R", "H"]
class_names = {"R": "Organic", "O": "Harzdious", "H": "Recycle"}
confidence_threshold = 0.7
pred_buffer = deque(maxlen=10)

# Default camera settings
camera_ip = "172.60.1.30"  # Default IP address
camera_source = f"http://{camera_ip}:4747/video"

# IP address validation function
def validate_ip_address(ip):
    """Validate IP address format using regex pattern"""
    pattern = r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    return bool(re.match(pattern, ip))

# -----------------------------
# Resize with padding
# -----------------------------
def resize_with_padding(img, target_size=(224,224)):
    h, w = img.shape[:2]
    scale = min(target_size[0]/h, target_size[1]/w)
    nh, nw = int(h*scale), int(w*scale)
    img_resized = cv2.resize(img, (nw, nh))
    top = (target_size[0]-nh)//2
    bottom = target_size[0]-nh-top
    left = (target_size[1]-nw)//2
    right = target_size[1]-nw-left
    img_padded = cv2.copyMakeBorder(img_resized, top, bottom, left, right,
                                    cv2.BORDER_CONSTANT, value=[0,0,0])
    return img_padded

# -----------------------------
# Predict frame
# -----------------------------
def predict_frame(frame):
    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img_resized = resize_with_padding(img_rgb)
    img_array = np.expand_dims(img_resized.astype(np.float32), axis=0)
    img_array = preprocess_input(img_array)

    predictions = model.predict(img_array, verbose=0)[0]
    pred_buffer.append(predictions)
    avg_pred = np.mean(pred_buffer, axis=0)

    predicted_idx = np.argmax(avg_pred)
    predicted_class = classes[predicted_idx]
    confidence = avg_pred[predicted_idx]
    
    # Update confidence label in GUI
    confidence_percentage = confidence * 100
    confidence_label.config(text=f"Confidence: {confidence_percentage:.1f}%")
    
    # Set color based on confidence
    if confidence_percentage > 90:
        confidence_label.config(fg="#50fa7b")  # Green for high confidence
    elif confidence_percentage > 70:
        confidence_label.config(fg="#f1fa8c")  # Yellow for medium confidence
    else:
        confidence_label.config(fg="#ff5555")  # Red for low confidence
    
    # Add visual indicator to the frame
    h, w = frame.shape[:2]
    text_position = (10, h - 20)
    
    # Draw classification result on the frame
    if confidence < confidence_threshold:
        label = f"Unrecognized ({confidence*100:.1f}%)"
        cv2.putText(frame, label, text_position, cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    else:
        # Color coding for different waste types
        if predicted_class == "O":  # Hazardous
            color = (0, 0, 255)  # Red
            label = f"HAZARDOUS ({confidence*100:.1f}%)"
        elif predicted_class == "R":  # Organic
            color = (0, 255, 0)  # Green
            label = f"ORGANIC ({confidence*100:.1f}%)"
        else:  # Recycle
            color = (255, 0, 0)  # Blue
            label = f"RECYCLABLE ({confidence*100:.1f}%)"
        
        # Draw colored rectangle at the bottom of the frame
        cv2.rectangle(frame, (0, h-40), (w, h), color, -1)
        cv2.putText(frame, label, text_position, cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    return label

# -----------------------------
# Optimized local model prediction for ensemble system
# -----------------------------
def predict_local_model(image):
    """
    Run prediction on an image using the local model and return standardized result.
    
    Args:
        image: The image to analyze (PIL Image, numpy array, or file path)
        
    Returns:
        Dictionary with standardized prediction result
    """
    try:
        # Convert to numpy array if needed
        if isinstance(image, Image.Image):
            # Convert PIL Image to numpy array
            img_np = np.array(image.convert('RGB'))
        elif isinstance(image, str) and os.path.exists(image):
            # Load image from file
            img_np = cv2.imread(image)
            img_np = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)
        else:
            # Assume it's already a numpy array
            img_np = image
            
        # Validate image
        if img_np is None or img_np.size == 0 or len(img_np.shape) < 2:
            return None
            
        # Apply enhanced preprocessing
        # 1. Resize with padding to maintain aspect ratio
        img_resized = resize_with_padding(img_np)
        
        # 2. Apply additional preprocessing techniques
        # - Normalize lighting conditions
        img_normalized = normalize_lighting(img_resized)
        
        # - Convert to model input format
        img_array = np.expand_dims(img_normalized.astype(np.float32), axis=0)
        img_array = preprocess_input(img_array)

        # Make prediction with error handling
        predictions = model.predict(img_array, verbose=0)[0]
        
        # Apply temporal smoothing with prediction buffer
        pred_buffer.append(predictions)
        avg_pred = np.mean(pred_buffer, axis=0)

        # Get predicted class and confidence
        predicted_idx = np.argmax(avg_pred)
        predicted_class = classes[predicted_idx]
        confidence = float(avg_pred[predicted_idx])
        
        # Return standardized result format for ensemble system
        return {
            "source": "local",
            "class_name": class_names.get(predicted_class, "Unknown"),
            "confidence": confidence,
            "reasoning": f"Local model prediction with {confidence*100:.1f}% confidence"
        }
        
    except Exception as e:
        print(f"Error in local model prediction: {e}")
        return {
            "source": "local",
            "error": str(e),
            "class_name": "Error",
            "confidence": 0
        }

# Helper function for enhanced image preprocessing
def normalize_lighting(image):
    """
    Normalize lighting conditions in the image to improve prediction accuracy.
    
    Args:
        image: Input image as numpy array
        
    Returns:
        Normalized image
    """
    # Convert to LAB color space
    lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
    
    # Split channels
    l, a, b = cv2.split(lab)
    
    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) to L channel
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    
    # Merge channels back
    limg = cv2.merge((cl, a, b))
    
    # Convert back to RGB color space
    normalized = cv2.cvtColor(limg, cv2.COLOR_LAB2RGB)
    
    return normalized

# Function to connect to camera
def connect_to_camera(camera_source):
    global cap
    # Release previous capture if it exists
    if 'cap' in globals():
        cap.release()
    
    # Connect to the new camera source
    return cv2.VideoCapture(camera_source)

# -----------------------------
# Tkinter Jarvis-like GUI
# -----------------------------
root = tk.Tk()
root.title("BOLT INNOVATORS - Smart Waste Classification")
root.configure(bg="#1E1E2E")
root.geometry("900x700")  # Larger window size

# Create a style for ttk widgets
style = ttk.Style()
style.theme_use('clam')
style.configure('TButton', font=('Helvetica', 10, 'bold'), borderwidth=0, background='#6272a4', foreground='white')
style.map('TButton', background=[('active', '#8be9fd'), ('pressed', '#44475a')], foreground=[('active', '#282a36')])
style.configure('TEntry', fieldbackground='#44475a', foreground='white', insertcolor='white')

# Logo and title frame
title_frame = tk.Frame(root, bg="#1E1E2E", height=100)
title_frame.pack(fill=tk.X, pady=10)

# Create a logo frame
logo_frame = tk.Frame(title_frame, bg="#1E1E2E")
logo_frame.pack(pady=5)

# Add a recycling symbol logo
logo_canvas = tk.Canvas(logo_frame, width=60, height=60, bg="#1E1E2E", highlightthickness=0)
logo_canvas.pack(side=tk.LEFT, padx=10)
logo_canvas.create_oval(5, 5, 55, 55, fill="#50fa7b", outline="#8be9fd", width=2)
logo_canvas.create_polygon(30, 10, 15, 40, 45, 40, fill="#1E1E2E", outline="#8be9fd", width=2)

# BOLT INNOVATORS Logo text next to the symbol
logo_label = tk.Label(logo_frame, text="BOLT INNOVATORS", font=("Arial", 28, "bold"), fg="#8be9fd", bg="#1E1E2E")
logo_label.pack(side=tk.LEFT, padx=10)

# Subtitle
subtitle_label = tk.Label(title_frame, text="Smart Waste Classification System", font=("Arial", 14), fg="#f8f8f2", bg="#1E1E2E")
subtitle_label.pack(pady=5)

# Add a description
description_label = tk.Label(title_frame, text="AI-Powered • Real-time • Eco-friendly", font=("Arial", 10), fg="#f8f8f2", bg="#1E1E2E")
description_label.pack(pady=2)

# Status frame with modern styling
status_frame = tk.Frame(root, bg="#282a36", height=30)
status_frame.pack(fill=tk.X, pady=5)

# Connection status indicator with improved styling
connection_status = tk.Label(status_frame, text="Camera: Connecting...", font=("Helvetica", 10),
                           fg="#f1fa8c", bg="#282a36", padx=10, pady=5)
connection_status.pack(side=tk.LEFT, padx=10)

# Instructions label with improved styling
instructions = tk.Label(status_frame, text="Place objects in front of camera for classification", 
                      font=("Helvetica", 10), fg="#f8f8f2", bg="#282a36", padx=10, pady=5)
instructions.pack(side=tk.RIGHT, padx=10)

# Camera controls frame with modern styling
camera_frame = tk.Frame(root, bg="#282a36", padx=10, pady=10)
camera_frame.pack(fill=tk.X, pady=10)

# IP Address entry with validation
ip_control_frame = tk.Frame(camera_frame, bg="#282a36")
ip_control_frame.pack(side=tk.LEFT, padx=10)

ip_label = tk.Label(ip_control_frame, text="Phone IP:", font=("Helvetica", 10, "bold"), fg="#f8f8f2", bg="#282a36")
ip_label.pack(side=tk.LEFT)

ip_entry = ttk.Entry(ip_control_frame, width=15, font=("Helvetica", 10), style="TEntry")
ip_entry.insert(0, camera_ip)  # Default value
ip_entry.pack(side=tk.LEFT, padx=5)

# IP validation status indicator
ip_status = tk.Label(ip_control_frame, text="", font=("Helvetica", 8), fg="#50fa7b", bg="#282a36")
ip_status.pack(side=tk.LEFT, padx=5)

# Function to validate IP on entry change
def validate_ip_entry(event=None):
    ip = ip_entry.get().strip()
    if validate_ip_address(ip):
        ip_status.config(text="✓ Valid", fg="#50fa7b")
        connect_button.config(state=tk.NORMAL)
        return True
    else:
        ip_status.config(text="✗ Invalid format", fg="#ff5555")
        connect_button.config(state=tk.DISABLED)
        return False

# Bind validation to entry changes
ip_entry.bind("<KeyRelease>", validate_ip_entry)

# Connect button with improved styling and validation
def connect_to_ip_camera():
    ip = ip_entry.get().strip()
    if validate_ip_address(ip):
        global camera_source, connection_attempts
        camera_source = f"http://{ip}:4747/video"
        connection_attempts = 0
        global cap
        cap = connect_to_camera(camera_source)
        connection_status.config(text="Camera: Reconnecting...", fg="#f1fa8c")
    else:
        messagebox.showerror("Invalid IP", "Please enter a valid IP address")

# Button frame for better organization
button_frame = tk.Frame(camera_frame, bg="#282a36")
button_frame.pack(side=tk.RIGHT, padx=10)

connect_button = ttk.Button(button_frame, text="Connect to Phone", command=connect_to_ip_camera, style="TButton")
connect_button.pack(side=tk.LEFT, padx=5)

# Switch to webcam button with improved styling
def switch_to_webcam():
    global camera_source, connection_attempts
    camera_source = 0
    connection_attempts = 0
    global cap
    cap = connect_to_camera(camera_source)
    connection_status.config(text="Camera: Switching to webcam...", fg="#f1fa8c")

webcam_button = ttk.Button(button_frame, text="Use Webcam", command=switch_to_webcam, style="TButton")
webcam_button.pack(side=tk.LEFT, padx=5)

# Run initial IP validation
validate_ip_entry()

# Create main content frame
main_content = tk.Frame(root, bg="#1E1E2E")
main_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

# Video display with border
video_frame = tk.Frame(main_content, bg="#44475a", bd=2, relief=tk.GROOVE, padx=5, pady=5)
video_frame.pack(pady=10)

video_label = tk.Label(video_frame, bg="black")
video_label.pack()

# Prediction display with improved styling
prediction_frame = tk.Frame(main_content, bg="#282a36", bd=2, relief=tk.GROOVE, padx=20, pady=10)
prediction_frame.pack(fill=tk.X, pady=10)

prediction_title = tk.Label(prediction_frame, text="Classification Result", font=("Helvetica", 12, "bold"), 
                          fg="#bd93f9", bg="#282a36")
prediction_title.pack(pady=(5, 10))

prediction_label = tk.Label(prediction_frame, text="Initializing...", 
                          font=("Helvetica", 16), fg="#f8f8f2", bg="#282a36")
prediction_label.pack(pady=5)

# Confidence indicator (will be updated in the prediction function)
confidence_label = tk.Label(prediction_frame, text="", font=("Helvetica", 10), 
                          fg="#8be9fd", bg="#282a36")
confidence_label.pack(pady=5)

# Camera options:
# Option 1: Use IP Webcam app on your Android phone
# 1. Install IP Webcam app on your Android phone
# 2. Connect your phone and Mac to the same WiFi network
# 3. Open the app and start the server
# 4. Note the IP address shown in the app (e.g., http://192.168.1.100:4747)
# 5. Replace the IP address in the entry field with your phone's IP address

# Initialize camera
cap = connect_to_camera(camera_source)

# Frame counter for connection stability
connection_attempts = 0
max_attempts = 30

def update_frame():
    global connection_attempts
    ret, frame = cap.read()
    
    if ret:
        # Reset connection attempts counter on successful frame read
        connection_attempts = 0
        
        # Update connection status with improved styling
        connection_status.config(text="Camera: Connected", fg="#50fa7b")
        
        # Get prediction label
        label = predict_frame(frame)

        # Update GUI label
        prediction_label.config(text=label)

        # Convert for Tkinter
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        img = img.resize((640, 480), Image.LANCZOS)  # Consistent size with LANCZOS resampling
        imgtk = ImageTk.PhotoImage(image=img)
        video_label.imgtk = imgtk
        video_label.configure(image=imgtk)
    else:
        # Increment connection attempts
        connection_attempts += 1
        
        if connection_attempts < max_attempts:
            # Still trying to connect
            connection_status.config(text=f"Camera: Connecting... ({connection_attempts}/{max_attempts})", fg="#f1fa8c")
        else:
            # Connection failed
            connection_status.config(text="Camera: Failed to connect", fg="#ff5555")
            prediction_label.config(text="Camera connection failed. Please check your camera settings.")
            instructions.config(text="Make sure your phone and Mac are on the same WiFi network", fg="#ff5555")
        
    root.after(10, update_frame)

update_frame()
root.mainloop()

cap.release()
cv2.destroyAllWindows()
