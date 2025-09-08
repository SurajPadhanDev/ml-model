import tensorflow as tf
from tensorflow.keras.models import load_model
import numpy as np
import cv2
from collections import deque
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from PIL import Image, ImageTk
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
import socket
import netifaces
import threading
import time
import re
import requests
from io import BytesIO

# -----------------------------
# Load trained model
# -----------------------------
MODEL_PATH = r"/Users/surajpadhan/Desktop/mode code web/best_mobilenetv2_model.keras"

try:
    model = load_model(MODEL_PATH)
    print("✅ Model loaded successfully!")
except Exception as e:
    print("❌ Error loading model:", e)
    exit()

# Classes
CLASSES = ["O", "R", "H"]
CLASS_NAMES = {"R": "Organic", "O": "Hazardous", "H": "Recycle"}
CONFIDENCE_THRESHOLD = 0.7
pred_buffer = deque(maxlen=10)


# -----------------------------
# Utility functions
# -----------------------------
def resize_with_padding(img, target_size=(224, 224)):
    """Resize while keeping aspect ratio and pad with black borders."""
    h, w = img.shape[:2]
    scale = min(target_size[0] / h, target_size[1] / w)
    nh, nw = int(h * scale), int(w * scale)
    img_resized = cv2.resize(img, (nw, nh))
    top = (target_size[0] - nh) // 2
    bottom = target_size[0] - nh - top
    left = (target_size[1] - nw) // 2
    right = target_size[1] - nw - left
    img_padded = cv2.copyMakeBorder(
        img_resized, top, bottom, left, right, cv2.BORDER_CONSTANT, value=[0, 0, 0]
    )
    return img_padded

# -----------------------------
# Network and IP Camera Functions
# -----------------------------
def get_local_ip():
    """Get the local IP address of this machine."""
    try:
        # Get all network interfaces
        interfaces = netifaces.interfaces()
        for interface in interfaces:
            # Skip loopback interface
            if interface == 'lo' or interface.startswith('lo'):
                continue
                
            # Get addresses for this interface
            addresses = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addresses:
                for address in addresses[netifaces.AF_INET]:
                    ip = address['addr']
                    # Skip localhost
                    if not ip.startswith('127.'):
                        return ip
        return "127.0.0.1"  # Fallback to localhost
    except Exception as e:
        print(f"Error getting local IP: {e}")
        return "Unknown"

def is_ip_camera_url(url):
    """Check if a URL is a valid IP camera stream URL."""
    # Common IP camera URL patterns
    patterns = [
        r'^http://\d+\.\d+\.\d+\.\d+:\d+/video$',  # http://192.168.1.100:8080/video
        r'^http://\d+\.\d+\.\d+\.\d+/video$',       # http://192.168.1.100/video (DroidCam)
        r'^http://\d+\.\d+\.\d+\.\d+:4747/video$',  # http://192.168.1.100:4747/video (DroidCam specific)
        r'^http://\d+\.\d+\.\d+\.\d+:\d+/videofeed$',  # http://192.168.1.100:8080/videofeed
        r'^http://\d+\.\d+\.\d+\.\d+:\d+/shot\.jpg$',  # http://192.168.1.100:8080/shot.jpg (IP Webcam)
        r'^rtsp://\d+\.\d+\.\d+\.\d+:\d+/.*$',  # RTSP streams
    ]
    
    for pattern in patterns:
        if re.match(pattern, url):
            return True
    return False

def scan_network_for_ip_cameras(base_ip, callback=None):
    """Scan the local network for potential IP cameras.
    Args:
        base_ip: Base IP address (e.g., '192.168.1')
        callback: Function to call with discovered cameras
    """
    discovered_cameras = []
    common_ports = [8080, 8081, 8082, 554]  # Common IP camera ports
    
    def check_ip(ip):
        for port in common_ports:
            # Try common IP camera URL patterns
            urls_to_try = [
                f"http://{ip}:{port}/video",
                f"http://{ip}:{port}/videofeed",
                f"http://{ip}:{port}/shot.jpg",  # IP Webcam app
            ]
            
            for url in urls_to_try:
                try:
                    response = requests.get(url, timeout=0.5)
                    if response.status_code == 200:
                        discovered_cameras.append(url)
                        if callback:
                            callback(url)
                        break
                except:
                    pass  # Connection failed, try next URL
    
    # Extract network prefix from base_ip
    ip_parts = base_ip.split('.')
    if len(ip_parts) >= 3:
        network_prefix = '.'.join(ip_parts[:3])
        
        # Create threads for scanning
        threads = []
        for i in range(1, 255):  # Scan all IPs in the subnet
            ip = f"{network_prefix}.{i}"
            thread = threading.Thread(target=check_ip, args=(ip,))
            thread.daemon = True
            threads.append(thread)
            thread.start()
            
            # Limit concurrent threads
            if len(threads) >= 20:
                for t in threads:
                    t.join(0.1)
                threads = [t for t in threads if t.is_alive()]
        
        # Wait for remaining threads
        for t in threads:
            t.join(0.1)
    
    return discovered_cameras


def predict_frame(frame, return_confidence=False):
    """Run prediction on a frame and return label string.
    Args:
        frame: The image frame to analyze
        return_confidence: If True, returns (label, confidence) tuple instead of just label string
    """
    if frame is None:
        return ("❌ No valid frame to analyze", 0.0) if return_confidence else "❌ No valid frame to analyze"
        
    try:
        # First try using external AI APIs if available
        try:
            from ai_integration import classify_waste
            
            # Try to get prediction from external AI with ensemble method
            external_prediction = classify_waste(frame, use_ensemble=True, confidence_threshold=0.65)
            
            if external_prediction:
                # If we got a valid prediction from external AI, return it
                result = f"🌐 {external_prediction} (AI Ensemble)"
                return (result, 95.0) if return_confidence else result
        except Exception as api_error:
            print(f"External AI error: {api_error}")
            # Continue with local model if external AI fails
            pass
            
        # Enhanced validation for frame format
        if frame is None or not isinstance(frame, np.ndarray) or frame.size == 0 or len(frame.shape) < 2:
            return ("❌ Invalid frame format", 0.0) if return_confidence else "❌ Invalid frame format"
            
        # Convert to RGB if frame is BGR
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        else:
            img_rgb = frame
            
        # Enhanced image preprocessing pipeline
        # 1. Resize with padding to maintain aspect ratio
        img_resized = resize_with_padding(img_rgb)
        
        # 2. Apply lighting normalization for better accuracy in different lighting conditions
        try:
            # Convert to LAB color space
            lab = cv2.cvtColor(img_resized, cv2.COLOR_RGB2LAB)
            
            # Split channels
            l, a, b = cv2.split(lab)
            
            # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) to L channel
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            cl = clahe.apply(l)
            
            # Merge channels back
            limg = cv2.merge((cl, a, b))
            
            # Convert back to RGB color space
            img_normalized = cv2.cvtColor(limg, cv2.COLOR_LAB2RGB)
        except Exception as preprocess_error:
            print(f"Preprocessing error: {preprocess_error}")
            # Fallback to original resized image if preprocessing fails
            img_normalized = img_resized
        
        # 3. Preprocess for MobileNetV2
        img_array = np.expand_dims(img_normalized.astype(np.float32), axis=0)
        img_array = preprocess_input(img_array)

        # Make prediction with enhanced error handling
        try:
            # Use a timeout to prevent hanging on model prediction
            import threading
            import queue
            
            def predict_with_timeout(image_array, result_queue):
                try:
                    predictions = model.predict(image_array, verbose=0)[0]
                    result_queue.put(predictions)
                except Exception as e:
                    result_queue.put(e)
            
            # Create a queue for the result
            result_queue = queue.Queue()
            
            # Start prediction in a separate thread
            prediction_thread = threading.Thread(target=predict_with_timeout, args=(img_array, result_queue))
            prediction_thread.daemon = True
            prediction_thread.start()
            
            # Wait for the prediction with timeout
            try:
                predictions = result_queue.get(timeout=2.0)  # 2 second timeout
                
                # Check if the result is an exception
                if isinstance(predictions, Exception):
                    raise predictions
                    
                # Apply temporal smoothing with prediction buffer
                pred_buffer.append(predictions)
                
                # Use weighted average for temporal smoothing (recent predictions have more weight)
                weights = np.linspace(0.5, 1.0, len(pred_buffer))
                weights = weights / np.sum(weights)  # Normalize weights
                avg_pred = np.average(pred_buffer, axis=0, weights=weights)

                predicted_idx = np.argmax(avg_pred)
                predicted_class = CLASSES[predicted_idx]
                confidence = float(avg_pred[predicted_idx])
                
                # Dynamic confidence threshold based on prediction stability
                stability = np.std([p[predicted_idx] for p in pred_buffer])
                adjusted_threshold = CONFIDENCE_THRESHOLD * (1.0 + stability * 2)  # Increase threshold for unstable predictions

                if confidence < adjusted_threshold:
                    result = f"❓ Uncertain ({confidence*100:.1f}%)"
                else:
                    result = f"{CLASS_NAMES[predicted_class]} ({confidence*100:.1f}%)"
                    
                return (result, confidence*100) if return_confidence else result
                
            except queue.Empty:
                print("Model prediction timed out")
                return ("❌ Model timeout", 0.0) if return_confidence else "❌ Model timeout"
                
        except Exception as model_error:
            print(f"Model prediction error: {model_error}")
            return ("❌ Model error", 0.0) if return_confidence else "❌ Model error"
            
    except Exception as e:
        print(f"Error in prediction: {e}")
        return ("❌ Error analyzing frame", 0.0) if return_confidence else "❌ Error analyzing frame"


# -----------------------------
# Tkinter App Class
# -----------------------------
class BOLT_INOVATOR_WasteClassifier:
    def __init__(self, root):
        self.root = root
        self.root.title("♻️ BOLT INOVATOR Waste Classifier")
        self.root.configure(bg="black")

        # ✅ Fullscreen mode
        self.root.attributes("-fullscreen", True)
        self.root.bind("<Escape>", lambda e: self.exit_fullscreen())
        
        # Network status variables
        self.local_ip = get_local_ip()
        self.discovered_cameras = []
        self.camera_scan_thread = None
        self.ip_camera_url = ""
        self.camera_type = "local"  # "local" or "ip"
        self.path_var = tk.StringVar()
        self.preview_url_var = tk.StringVar()
        
        # Create main frames
        self.main_frame = tk.Frame(root, bg="black")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel for video
        self.left_panel = tk.Frame(self.main_frame, bg="black")
        self.left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Right panel for controls
        self.right_panel = tk.Frame(self.main_frame, bg="black")
        self.right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

        # Video panel
        self.video_label = tk.Label(self.left_panel, bg="black")
        self.video_label.pack(pady=10, expand=True)

        # Prediction text
        self.prediction_label = tk.Label(
            self.left_panel,
            text="Click ▶ Start to begin...",
            font=("Consolas", 22, "bold"),
            fg="cyan",
            bg="black",
        )
        self.prediction_label.pack(pady=20)
        
        # Network status frame
        self.network_frame = tk.LabelFrame(self.right_panel, text="Network Status", bg="black", fg="white", font=("Consolas", 12))
        self.network_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Local IP display
        self.ip_label = tk.Label(
            self.network_frame,
            text=f"Your IP: {self.local_ip}",
            font=("Consolas", 12),
            fg="white",
            bg="black",
            anchor="w"
        )
        self.ip_label.pack(fill=tk.X, padx=5, pady=5)
        
        # Connection status
        self.connection_status = tk.Label(
            self.network_frame,
            text="Status: Not Connected",
            font=("Consolas", 12),
            fg="yellow",
            bg="black",
            anchor="w"
        )
        self.connection_status.pack(fill=tk.X, padx=5, pady=5)
        
        # Camera selection frame
        self.camera_frame = tk.LabelFrame(self.right_panel, text="Camera Selection", bg="black", fg="white", font=("Consolas", 12))
        self.camera_frame.pack(fill=tk.X, padx=5, pady=10)
        
        # Camera type selection
        self.camera_type_var = tk.StringVar(value="local")
        self.local_cam_radio = tk.Radiobutton(
            self.camera_frame, 
            text="Local Webcam", 
            variable=self.camera_type_var, 
            value="local",
            command=self.on_camera_type_change,
            bg="black", fg="white", selectcolor="black", font=("Consolas", 12)
        )
        self.local_cam_radio.pack(anchor="w", padx=5, pady=2)
        
        self.ip_cam_radio = tk.Radiobutton(
            self.camera_frame, 
            text="Mobile Camera (WiFi)", 
            variable=self.camera_type_var, 
            value="ip",
            command=self.on_camera_type_change,
            bg="black", fg="white", selectcolor="black", font=("Consolas", 12)
        )
        self.ip_cam_radio.pack(anchor="w", padx=5, pady=2)
        
        # IP Camera options frame (initially hidden)
        self.ip_options_frame = tk.Frame(self.camera_frame, bg="black")
        
        # Add template dropdown for different camera types
        self.template_frame = tk.Frame(self.ip_options_frame, bg="black")
        self.template_frame.pack(fill=tk.X, padx=5, pady=2)
        
        self.template_label = tk.Label(self.template_frame, text="Camera Type:", fg="white", bg="black", font=("Consolas", 10))
        self.template_label.pack(side=tk.LEFT, padx=5)
        
        self.template_var = tk.StringVar()
        self.template_options = [
            "IP Webcam: /shot.jpg",
            "DroidCam: /video",
            "DroidCam (port 4747): /video"
        ]
        self.template_dropdown = ttk.Combobox(self.template_frame, textvariable=self.template_var, 
                                           values=self.template_options, state="readonly", width=20)
        self.template_dropdown.pack(side=tk.RIGHT, padx=5, fill=tk.X, expand=True)
        self.template_dropdown.current(0)  # Default to first template
        self.template_dropdown.bind("<<ComboboxSelected>>", self.apply_template)
        
        # Manual IP entry
        self.manual_ip_frame = tk.Frame(self.ip_options_frame, bg="black")
        self.manual_ip_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.ip_entry_label = tk.Label(
            self.manual_ip_frame,
            text="Enter Camera IP:",
            font=("Consolas", 12),
            fg="white",
            bg="black",
            anchor="w"
        )
        self.ip_entry_label.pack(anchor="w")
        
        self.ip_entry_frame = tk.Frame(self.manual_ip_frame, bg="black")
        self.ip_entry_frame.pack(fill=tk.X)
        
        self.ip_entry = tk.Entry(self.ip_entry_frame, font=("Consolas", 12), width=15)
        self.ip_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.ip_entry.insert(0, "192.168.1.100")  # Default IP for IP Webcam or DroidCam
        self.ip_entry.bind("<KeyRelease>", lambda e: self.update_preview_url())
        
        self.port_entry = tk.Entry(self.ip_entry_frame, font=("Consolas", 12), width=5)
        self.port_entry.pack(side=tk.LEFT)
        self.port_entry.insert(0, "8080")
        self.port_entry.bind("<KeyRelease>", lambda e: self.update_preview_url())
        
        # Path entry
        self.path_frame = tk.Frame(self.ip_options_frame, bg="black")
        self.path_frame.pack(fill=tk.X, padx=10, pady=2)
        
        self.path_label = tk.Label(self.path_frame, text="Path:", fg="white", bg="black", font=("Consolas", 12))
        self.path_label.pack(side=tk.LEFT, padx=5)
        
        self.path_entry = tk.Entry(self.path_frame, font=("Consolas", 12), textvariable=self.path_var)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.path_var.set("/shot.jpg")  # Default path for IP Webcam
        self.path_entry.bind("<KeyRelease>", lambda e: self.update_preview_url())
        
        # Preview URL
        self.preview_frame = tk.Frame(self.ip_options_frame, bg="black")
        self.preview_frame.pack(fill=tk.X, padx=10, pady=2)
        
        self.preview_label = tk.Label(self.preview_frame, text="URL:", fg="white", bg="black", font=("Consolas", 10))
        self.preview_label.pack(side=tk.LEFT, padx=5)
        
        self.preview_url = tk.Label(self.preview_frame, textvariable=self.preview_url_var, 
                                  fg="#aaffaa", bg="black", font=("Consolas", 10))
        self.preview_url.pack(side=tk.LEFT, padx=5, fill=tk.X)
        
        # Initialize preview URL
        self.update_preview_url()
        
        self.connect_button = tk.Button(
            self.manual_ip_frame,
            text="Connect",
            font=("Consolas", 12, "bold"),
            fg="white",
            bg="#2979ff",  # Vibrant blue
            activebackground="#82b1ff",  # Lighter blue on click
            command=self.connect_to_ip_camera,
            relief=tk.RAISED,
            borderwidth=2
        )
        self.connect_button.pack(fill=tk.X, pady=5)
        # Bind hover events for connect button
        self.connect_button.bind("<Enter>", lambda e: on_enter(e, self.connect_button, "#2979ff", "#82b1ff"))
        self.connect_button.bind("<Leave>", lambda e: on_leave(e, self.connect_button, "#2979ff"))
        
        # Help button for mobile camera setup
        self.help_button = tk.Button(
            self.manual_ip_frame,
            text="How to Connect Mobile Camera",
            font=("Consolas", 12, "bold"),
            fg="white",
            bg="#aa00ff",  # Vibrant purple
            activebackground="#e040fb",  # Lighter purple on click
            command=self.show_mobile_camera_instructions,
            relief=tk.RAISED,
            borderwidth=2
        )
        self.help_button.pack(fill=tk.X, pady=5)
        # Bind hover events for help button
        self.help_button.bind("<Enter>", lambda e: on_enter(e, self.help_button, "#aa00ff", "#e040fb"))
        self.help_button.bind("<Leave>", lambda e: on_leave(e, self.help_button, "#aa00ff"))
        
        # Auto discovery
        self.auto_discovery_frame = tk.Frame(self.ip_options_frame, bg="black")
        self.auto_discovery_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.scan_button = tk.Button(
            self.auto_discovery_frame,
            text="Scan Network",
            font=("Consolas", 12, "bold"),
            fg="white",
            bg="#00c853",  # Vibrant green (matching start button)
            activebackground="#69f0ae",  # Lighter green on click
            command=self.scan_for_cameras,
            relief=tk.RAISED,
            borderwidth=2
        )
        self.scan_button.pack(fill=tk.X)
        # Bind hover events for scan button
        self.scan_button.bind("<Enter>", lambda e: on_enter(e, self.scan_button, "#00c853", "#69f0ae"))
        self.scan_button.bind("<Leave>", lambda e: on_leave(e, self.scan_button, "#00c853"))
        
        self.scan_status = tk.Label(
            self.auto_discovery_frame,
            text="",
            font=("Consolas", 10),
            fg="white",
            bg="black"
        )
        self.scan_status.pack(fill=tk.X, pady=2)
        
        # Discovered cameras dropdown
        self.camera_dropdown_frame = tk.Frame(self.auto_discovery_frame, bg="black")
        self.camera_dropdown_frame.pack(fill=tk.X, pady=5)
        
        self.camera_dropdown_label = tk.Label(
            self.camera_dropdown_frame,
            text="Discovered Cameras:",
            font=("Consolas", 10),
            fg="white",
            bg="black"
        )
        self.camera_dropdown_label.pack(anchor="w")
        
        self.camera_dropdown_var = tk.StringVar()
        self.camera_dropdown = ttk.Combobox(
            self.camera_dropdown_frame,
            textvariable=self.camera_dropdown_var,
            font=("Consolas", 10),
            state="readonly"
        )
        self.camera_dropdown.pack(fill=tk.X)
        self.camera_dropdown.bind("<<ComboboxSelected>>", self.on_camera_selected)

        # Button Frame
        btn_frame = tk.Frame(self.right_panel, bg="black")
        btn_frame.pack(pady=20, fill=tk.X)

        # Button style and animation functions
        def on_enter(e, button, original_bg, hover_bg):
            button.config(bg=hover_bg, relief=tk.RAISED)
            # Subtle grow effect
            button.config(padx=2, pady=2)
            
        def on_leave(e, button, original_bg):
            button.config(bg=original_bg, relief=tk.RAISED)
            # Return to original size
            button.config(padx=0, pady=0)
        
        # Enhanced Buttons with vibrant colors and animations
        self.start_button = tk.Button(
            btn_frame,
            text="▶ Start",
            font=("Consolas", 16, "bold"),
            fg="white",
            bg="#00c853",  # Vibrant green
            activebackground="#69f0ae",  # Lighter green on click
            width=14,
            command=self.start_camera,
            relief=tk.RAISED,
            borderwidth=3,
        )
        self.start_button.pack(fill=tk.X, pady=8)
        # Bind hover events
        self.start_button.bind("<Enter>", lambda e: on_enter(e, self.start_button, "#00c853", "#69f0ae"))
        self.start_button.bind("<Leave>", lambda e: on_leave(e, self.start_button, "#00c853"))

        # Capture button
        self.capture_button = tk.Button(
            btn_frame,
            text="📸 Capture",
            font=("Consolas", 16, "bold"),
            fg="white",
            bg="#2196F3",  # Vibrant blue
            activebackground="#64B5F6",  # Lighter blue on click
            width=14,
            command=self.capture_frame,
            state="disabled",
            relief=tk.RAISED,
            borderwidth=3,
        )
        self.capture_button.pack(fill=tk.X, pady=8)
        # Bind hover events
        self.capture_button.bind("<Enter>", lambda e: on_enter(e, self.capture_button, "#2196F3", "#64B5F6"))
        self.capture_button.bind("<Leave>", lambda e: on_leave(e, self.capture_button, "#2196F3"))

        self.stop_button = tk.Button(
            btn_frame,
            text="⏹ Stop",
            font=("Consolas", 16, "bold"),
            fg="white",
            bg="#d50000",  # Vibrant red
            activebackground="#ff5252",  # Lighter red on click
            width=14,
            command=self.stop_camera,
            state="disabled",
            relief=tk.RAISED,
            borderwidth=3,
        )
        self.stop_button.pack(fill=tk.X, pady=8)
        # Bind hover events
        self.stop_button.bind("<Enter>", lambda e: on_enter(e, self.stop_button, "#d50000", "#ff5252"))
        self.stop_button.bind("<Leave>", lambda e: on_leave(e, self.stop_button, "#d50000"))

        self.exit_button = tk.Button(
            btn_frame,
            text="❌ Exit",
            font=("Consolas", 16, "bold"),
            fg="white",
            bg="#424242",  # Dark gray
            activebackground="#757575",  # Lighter gray on click
            width=14,
            command=self.exit_app,
            relief=tk.RAISED,
            borderwidth=3,
        )
        self.exit_button.pack(fill=tk.X, pady=8)
        # Bind hover events
        self.exit_button.bind("<Enter>", lambda e: on_enter(e, self.exit_button, "#424242", "#757575"))
        self.exit_button.bind("<Leave>", lambda e: on_leave(e, self.exit_button, "#424242"))

        # Camera
        self.cap = None
        self.is_running = False
        
        # Initially hide IP camera options
        self.on_camera_type_change()

    def on_camera_type_change(self):
        """Handle camera type selection change"""
        camera_type = self.camera_type_var.get()
        
        if camera_type == "ip":
            # Show IP camera options
            self.ip_options_frame.pack(fill=tk.X, padx=5, pady=5)
        else:
            # Hide IP camera options
            self.ip_options_frame.pack_forget()
            
    def apply_template(self, event=None):
        """Apply the selected template to the IP entry field"""
        selected = self.template_var.get()
        
        # Clear current entry
        self.ip_entry.delete(0, tk.END)
        self.port_entry.delete(0, tk.END)
        
        if "IP Webcam" in selected:
            # IP Webcam format
            self.ip_entry.insert(0, "192.168.1.x")
            self.port_entry.insert(0, "8080")
            self.path_var.set("/shot.jpg")
        elif "DroidCam (port 4747)" in selected:
            # DroidCam format with specific port
            self.ip_entry.insert(0, "192.168.1.x")
            self.port_entry.insert(0, "4747")
            self.path_var.set("/video")
        elif "DroidCam" in selected:
            # DroidCam format
            self.ip_entry.insert(0, "192.168.1.x")
            self.port_entry.insert(0, "4747")
            self.path_var.set("/video")
        
        # Update the preview URL
        self.update_preview_url()
            
    def show_mobile_camera_instructions(self):
        """Show instructions for connecting a mobile camera"""
        instructions = (
            "How to connect your mobile phone as a camera:\n\n"
            "Option 1: Using IP Webcam app (Android)\n"
            "1. Install 'IP Webcam' app from Google Play Store\n"
            "2. Open the app and scroll down to 'Start server'\n"
            "3. Make sure your phone and computer are on the same WiFi network\n"
            "4. Note the IP address shown in the app (e.g., http://192.168.1.100:8080)\n"
            "5. In this application, select 'IP Camera' option\n"
            "6. Enter the IP address from step 4 followed by '/shot.jpg'\n"
            "   Example: http://192.168.1.100:8080/shot.jpg\n"
            "7. Click 'Connect' to use your phone's camera\n\n"
            
            "Option 2: Using DroidCam (Android/iOS)\n"
            "1. Install 'DroidCam' app from Google Play Store or App Store\n"
            "2. Open the app and start the server\n"
            "3. Make sure your phone and computer are on the same WiFi network\n"
            "4. Note the IP address shown in the app (DroidCam typically uses port 4747)\n"
            "5. In this application, select 'Mobile Camera (WiFi)' option\n"
            "6. Select 'DroidCam (port 4747): /video' from the dropdown\n"
            "7. Enter the IP address from your phone (e.g., 192.168.1.100)\n"
            "8. The URL should look like: http://192.168.1.100:4747/video\n"
            "9. Click 'Connect' to use your phone's camera\n\n"
            
            "The connection status will show 'Connected' when successful\n\n"
            "Note: For best results, mount your phone on a stable surface"
        )
        
        # Create a popup window with instructions
        popup = tk.Toplevel(self.root)
        popup.title("Mobile Camera Setup Instructions")
        popup.configure(bg="#1e1e1e")
        popup.geometry("600x500")
        
        # Add instructions text
        instructions_label = tk.Label(
            popup,
            text=instructions,
            font=("Arial", 12),
            fg="white",
            bg="#1e1e1e",
            justify=tk.LEFT,
            padx=20,
            pady=20
        )
        instructions_label.pack(expand=True, fill=tk.BOTH)
        
        # Add close button
        close_button = tk.Button(
            popup,
            text="Close",
            font=("Arial", 12, "bold"),
            fg="white",
            bg="#555555",
            command=popup.destroy
        )
        close_button.pack(pady=10)
            
    def scan_for_cameras(self):
        """Scan the network for IP cameras"""
        self.scan_status.config(text="Scanning network...", fg="yellow")
        self.scan_button.config(state="disabled")
        self.discovered_cameras = []
        self.camera_dropdown["values"] = []
        
        # Get network prefix from local IP
        ip_parts = self.local_ip.split('.')
        if len(ip_parts) >= 3:
            network_prefix = '.'.join(ip_parts[:3])
        else:
            network_prefix = "192.168.1"  # Default fallback
            
        def on_camera_found(url):
            # This function will be called from a worker thread
            # when a camera is found, so we need to use after() to update UI
            self.root.after(0, lambda: self._add_camera_to_dropdown(url))
            
        def scan_thread_func():
            # Run the scan in a separate thread
            scan_network_for_ip_cameras(network_prefix, on_camera_found)
            # Update UI when done
            self.root.after(0, lambda: self._scan_complete())
            
        # Start scan in a separate thread
        self.camera_scan_thread = threading.Thread(target=scan_thread_func)
        self.camera_scan_thread.daemon = True
        self.camera_scan_thread.start()
    
    def _add_camera_to_dropdown(self, url):
        """Add a discovered camera to the dropdown (called from scan thread)"""
        if url not in self.discovered_cameras:
            self.discovered_cameras.append(url)
            self.camera_dropdown["values"] = self.discovered_cameras
            self.scan_status.config(text=f"Found {len(self.discovered_cameras)} camera(s)", fg="green")
    
    def _scan_complete(self):
        """Called when scan is complete"""
        self.scan_button.config(state="normal")
        if not self.discovered_cameras:
            self.scan_status.config(text="No cameras found", fg="red")
        else:
            self.scan_status.config(text=f"Found {len(self.discovered_cameras)} camera(s)", fg="green")
    
    def on_camera_selected(self, event):
        """Handle camera selection from dropdown"""
        selected_url = self.camera_dropdown_var.get()
        if selected_url:
            self.ip_camera_url = selected_url
            self.connection_status.config(text=f"Selected: {selected_url}", fg="cyan")
    
    def update_preview_url(self):
        """Update the preview URL based on current settings"""
        ip = self.ip_entry.get().strip()
        port = self.port_entry.get().strip()
        path = self.path_var.get().strip()
        
        if ip and port and path:
            preview_url = f"http://{ip}:{port}{path}"
            self.preview_url_var.set(preview_url)
        else:
            self.preview_url_var.set("")
    
    def connect_to_ip_camera(self):
        """Connect to IP camera using manual entry"""
        ip = self.ip_entry.get().strip()
        port = self.port_entry.get().strip()
        path = self.path_var.get().strip()
        
        if not ip or not port:
            messagebox.showerror("Error", "Please enter IP and port")
            return
            
        # Construct URL based on path
        url = f"http://{ip}:{port}{path}"
        
        # Special handling for DroidCam with port 4747
        if port == "4747" and path == "/video":
            # This is likely a DroidCam connection
            try:
                # Try to open the camera with optimized settings for DroidCam
                test_cap = cv2.VideoCapture(url)
                
                # Set buffer size for better streaming performance
                test_cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)  # Smaller buffer for lower latency
                
                if test_cap.isOpened():
                    # Try multiple frames to ensure stable connection
                    for _ in range(3):
                        ret, frame = test_cap.read()
                        if ret and frame is not None:
                            self.ip_camera_url = url
                            self.connection_status.config(text=f"Connected to DroidCam: {url}", fg="green")
                            test_cap.release()
                            messagebox.showinfo("Success", f"Connected to DroidCam at {url}")
                            return
                    
                    test_cap.release()
                    messagebox.showerror("Error", "Connected to DroidCam but couldn't get video stream")
                    self.connection_status.config(text="DroidCam stream error", fg="red")
                    return
                else:
                    messagebox.showerror("Error", f"Could not connect to DroidCam at {url}")
                    self.connection_status.config(text="DroidCam connection failed", fg="red")
                    return
            except Exception as e:
                messagebox.showerror("Error", f"DroidCam connection error: {str(e)}")
                self.connection_status.config(text=f"DroidCam error: {str(e)[:30]}...", fg="red")
                return
        
        # Try different URL patterns for IP Webcam app if path is not specified
        urls_to_try = [url] if path else [
            f"http://{ip}:{port}/video",      # DroidCam format
            f"http://{ip}:{port}/videofeed", # Other camera apps
            f"http://{ip}:{port}/shot.jpg",  # IP Webcam app
        ]
        
        for url in urls_to_try:
            try:
                # Test connection
                if url.endswith('/shot.jpg'):  # IP Webcam app
                    response = requests.get(url, timeout=2)
                    if response.status_code == 200:
                        self.ip_camera_url = url
                        self.connection_status.config(text=f"Connected to IP Webcam: {url}", fg="green")
                        messagebox.showinfo("Success", f"Connected to IP Webcam at {url}")
                        return
                else:  # Other streaming URL
                    # Try to open the camera with optimized settings
                    test_cap = cv2.VideoCapture(url)
                    
                    # Set buffer size for better streaming performance
                    test_cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)  # Smaller buffer for lower latency
                    
                    if test_cap.isOpened():
                        # Try multiple frames to ensure stable connection
                        for _ in range(3):
                            ret, frame = test_cap.read()
                            if ret and frame is not None:
                                self.ip_camera_url = url
                                self.connection_status.config(text=f"Connected to camera: {url}", fg="green")
                                test_cap.release()
                                messagebox.showinfo("Success", f"Connected to camera at {url}")
                                return
                        
                        test_cap.release()
            except Exception as e:
                continue
                
        # If we get here, connection failed
        messagebox.showerror("Error", f"Could not connect to camera at {ip}:{port}")
        self.connection_status.config(text="Connection failed", fg="red")
            
    def start_camera(self):
        """Start camera stream based on selected type"""
        camera_type = self.camera_type_var.get()
        
        # Clear prediction buffer for new session
        pred_buffer.clear()
        
        if camera_type == "local":
            # Local webcam
            try:
                self.cap = cv2.VideoCapture(0)  # PC webcam
                if not self.cap.isOpened():
                    messagebox.showerror("Error", "❌ Could not access local webcam!")
                    return
                self.connection_status.config(text="Connected to local webcam", fg="green")
            except Exception as e:
                messagebox.showerror("Error", f"❌ Webcam error: {str(e)}")
                return
        else:
            # IP camera
            if not self.ip_camera_url:
                messagebox.showerror("Error", "Please select or enter an IP camera URL first")
                return
                
            # Check if URL ends with shot.jpg (IP Webcam app)
            if "/shot.jpg" in self.ip_camera_url:
                # For IP Webcam app, we'll handle this differently in update_frame
                self.cap = None  # We'll use requests instead
                
                # Test connection before starting
                try:
                    response = requests.get(self.ip_camera_url, timeout=2)
                    if response.status_code != 200:
                        messagebox.showerror("Error", f"❌ Could not connect to IP Webcam at {self.ip_camera_url}")
                        return
                    self.connection_status.config(text=f"Connected to IP Webcam app", fg="green")
                except Exception as e:
                    messagebox.showerror("Error", f"❌ IP Webcam connection error: {str(e)}")
                    return
            elif "/video" in self.ip_camera_url:
                # DroidCam video stream
                try:
                    # Close any existing capture
                    if self.cap and self.cap.isOpened():
                        self.cap.release()
                        
                    self.cap = cv2.VideoCapture(self.ip_camera_url)
                    # Optimize for streaming
                    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)  # Smaller buffer for lower latency
                    
                    if not self.cap.isOpened():
                        messagebox.showerror("Error", f"❌ Could not connect to DroidCam at {self.ip_camera_url}")
                        return
                    
                    # Test if we can get a frame
                    ret, frame = self.cap.read()
                    if not ret or frame is None:
                        messagebox.showerror("Error", "Connected to DroidCam but couldn't get video stream")
                        self.cap.release()
                        self.cap = None
                        return
                        
                    # Check if this is a DroidCam with port 4747
                    if ":4747/video" in self.ip_camera_url:
                        self.connection_status.config(text=f"Connected to DroidCam at {self.ip_camera_url}", fg="green")
                    else:
                        self.connection_status.config(text=f"Connected to video stream at {self.ip_camera_url}", fg="green")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to start video stream: {str(e)}")
                    if self.cap:
                        self.cap.release()
                    self.cap = None
                    return
            else:
                # Regular RTSP or HTTP stream
                try:
                    self.cap = cv2.VideoCapture(self.ip_camera_url)
                    if not self.cap.isOpened():
                        messagebox.showerror("Error", f"❌ Could not connect to IP camera at {self.ip_camera_url}")
                        return
                    self.connection_status.config(text=f"Connected to {self.ip_camera_url}", fg="green")
                except Exception as e:
                    messagebox.showerror("Error", f"❌ Camera connection error: {str(e)}")
                    return

        # Update UI state
        self.is_running = True
        self.start_button.config(state="disabled", bg="#757575")  # Dimmed color when disabled
        self.stop_button.config(state="normal", bg="#d50000")  # Ensure vibrant color is maintained
        self.capture_button.config(state="normal", bg="#2196F3")  # Enable capture button
        
        # Start frame updates
        self.update_frame()

    def update_frame(self):
        """Capture frame, run prediction, and update GUI."""
        frame = None
        connection_error = False
        
        # Add subtle pulsing animation to the stop button during execution
        if hasattr(self, 'pulse_count'):
            self.pulse_count = (self.pulse_count + 1) % 20
            if self.pulse_count < 10:
                # Pulse brighter
                pulse_color = "#ff5252"  # Brighter red
            else:
                # Pulse darker
                pulse_color = "#d50000"  # Original red
            self.stop_button.config(bg=pulse_color)
        else:
            self.pulse_count = 0
            
        if self.is_running:
            if self.camera_type_var.get() == "ip":
                if "/shot.jpg" in self.ip_camera_url:
                    # IP Webcam app - fetch JPEG image
                    try:
                        response = requests.get(self.ip_camera_url, timeout=1)
                        if response.status_code == 200:
                            # Convert the image from the response to a cv2 image
                            img_array = np.array(bytearray(response.content), dtype=np.uint8)
                            frame = cv2.imdecode(img_array, -1)  # -1 means load image as is
                    except Exception as e:
                        print(f"Error fetching IP Webcam frame: {e}")
                        self.connection_status.config(text=f"Connection error: {str(e)[:30]}...", fg="red")
                        connection_error = True
                elif "/video" in self.ip_camera_url:
                    # DroidCam or similar streaming URL
                    if not self.cap or not self.cap.isOpened():
                        # Initialize video capture if not already done
                        try:
                            self.cap = cv2.VideoCapture(self.ip_camera_url)
                            # Optimize for streaming
                            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)  # Smaller buffer for lower latency
                            # Set additional parameters for DroidCam to improve stability
                            if ":4747/video" in self.ip_camera_url:
                                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Lower resolution for stability
                                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                        except Exception as e:
                            print(f"Error initializing DroidCam stream: {e}")
                            self.connection_status.config(text=f"Connection error: {str(e)[:30]}...", fg="red")
                            connection_error = True
                    
                    if self.cap and self.cap.isOpened():
                        try:
                            # For DroidCam, try multiple read attempts if needed
                            max_attempts = 3 if ":4747/video" in self.ip_camera_url else 1
                            for attempt in range(max_attempts):
                                ret, frame = self.cap.read()
                                if ret and frame is not None:
                                    break
                                time.sleep(0.05)  # Short delay between attempts
                                
                            if not ret or frame is None:
                                print("Failed to get frame from DroidCam")
                                self.connection_status.config(text="Camera stream error", fg="red")
                                # Try to reconnect
                                self.cap.release()
                                self.cap = cv2.VideoCapture(self.ip_camera_url)
                                connection_error = True
                        except Exception as e:
                            print(f"Error reading DroidCam frame: {e}")
                            self.connection_status.config(text=f"Stream error: {str(e)[:30]}...", fg="red")
                            connection_error = True
            elif self.cap and self.cap.isOpened():
                # Regular webcam or video stream
                try:
                    ret, frame = self.cap.read()
                    if not ret:
                        print("Failed to get frame from camera")
                        self.connection_status.config(text="Camera disconnected", fg="red")
                        frame = None
                        connection_error = True
                except Exception as e:
                    print(f"Error reading webcam frame: {e}")
                    self.connection_status.config(text=f"Camera error: {str(e)[:30]}...", fg="red")
                    connection_error = True
            
            if frame is not None:
                # Update connection status if we successfully got a frame after an error
                if self.connection_status.cget("fg") == "red" and not connection_error:
                    if "/shot.jpg" in self.ip_camera_url:
                        self.connection_status.config(text="Connected to IP Webcam", fg="green")
                    elif "/video" in self.ip_camera_url:
                        self.connection_status.config(text="Connected to DroidCam", fg="green")
                    else:
                        self.connection_status.config(text="Connected", fg="green")
                
                # Prediction
                label = predict_frame(frame)
                self.prediction_label.config(text=label)

                # Convert for Tkinter
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)

                # ✅ Resize video to fit fullscreen nicely
                screen_w = self.root.winfo_screenwidth()
                screen_h = self.root.winfo_screenheight()
                img = img.resize((screen_w // 2, screen_h // 2))  

                imgtk = ImageTk.PhotoImage(image=img)
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)

        if self.is_running:
            # Adjust refresh rate based on camera type
            if self.camera_type_var.get() == "ip":
                if "/shot.jpg" in self.ip_camera_url:
                    refresh_rate = 200  # 5 FPS for IP Webcam app
                elif "/video" in self.ip_camera_url:
                    # For DroidCam, use a more conservative refresh rate to prevent freezing
                    refresh_rate = 100 if ":4747/video" in self.ip_camera_url else 50
                else:
                    refresh_rate = 100  # 10 FPS for other IP cameras
            else:
                refresh_rate = 30   # ~30 FPS for regular webcam
                
            self.root.after(refresh_rate, self.update_frame)

    def stop_camera(self):
        """Stop camera, capture last frame, and show its prediction."""
        # Update UI to show stopping in progress
        self.stop_button.config(state="disabled", bg="#ff5252")  # Bright red during stopping
        self.connection_status.config(text="Stopping camera...", fg="orange")
        self.root.update()  # Force UI update
        
        # Set flag to stop the update_frame loop
        self.is_running = False
        last_label = "Camera stopped."
        frame_captured = False
        
        try:
            # For regular webcam or video stream
            if self.cap:
                if self.cap.isOpened():
                    # Try to get a final frame for analysis - multiple attempts for reliability
                    for attempt in range(3):
                        try:
                            ret, frame = self.cap.read()
                            if ret and frame is not None and frame.size > 0:
                                # Save the last frame for potential further analysis
                                self.captured_frame = frame.copy()
                                frame_captured = True
                                
                                # Make final prediction
                                try:
                                    last_label = predict_frame(frame)
                                    
                                    # Display the frame
                                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                    img = Image.fromarray(frame_rgb)
                                    screen_w = self.root.winfo_screenwidth()
                                    screen_h = self.root.winfo_screenheight()
                                    img = img.resize((screen_w // 2, screen_h // 2))  
                                    imgtk = ImageTk.PhotoImage(image=img)
                                    self.video_label.imgtk = imgtk
                                    self.video_label.configure(image=imgtk)
                                except Exception as e:
                                    print(f"Error processing final frame: {e}")
                                    last_label = f"Error processing final frame: {str(e)[:30]}..."
                                break
                        except Exception as e:
                            print(f"Error reading final frame (attempt {attempt+1}): {e}")
                            time.sleep(0.1)  # Short delay between attempts
                
                # Always release the capture device, even if frame capture failed
                try:
                    self.cap.release()
                    self.cap = None
                except Exception as e:
                    print(f"Error releasing camera: {e}")
            
            # For IP Webcam app, try to get one last frame
            elif self.camera_type_var.get() == "ip" and "/shot.jpg" in self.ip_camera_url:
                try:
                    # Multiple attempts for reliability
                    for attempt in range(3):
                        try:
                            response = requests.get(self.ip_camera_url, timeout=2)
                            if response.status_code == 200:
                                img_array = np.array(bytearray(response.content), dtype=np.uint8)
                                frame = cv2.imdecode(img_array, -1)
                                if frame is not None and frame.size > 0:
                                    # Save the last frame for potential further analysis
                                    self.captured_frame = frame.copy()
                                    frame_captured = True
                                    
                                    # Make final prediction
                                    try:
                                        last_label = predict_frame(frame)
                                        
                                        # Display the frame
                                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                        img = Image.fromarray(frame_rgb)
                                        screen_w = self.root.winfo_screenwidth()
                                        screen_h = self.root.winfo_screenheight()
                                        img = img.resize((screen_w // 2, screen_h // 2))  
                                        imgtk = ImageTk.PhotoImage(image=img)
                                        self.video_label.imgtk = imgtk
                                        self.video_label.configure(image=imgtk)
                                    except Exception as e:
                                        print(f"Error processing final IP Webcam frame: {e}")
                                        last_label = f"Error processing final frame: {str(e)[:30]}..."
                                    break
                        except Exception as e:
                            print(f"Error getting final frame from IP Webcam (attempt {attempt+1}): {e}")
                            time.sleep(0.2)  # Short delay between attempts
                except Exception as e:
                    print(f"Error in IP Webcam final capture: {e}")

            # Update UI with final prediction and status
            status_text = "Camera stopped - "
            status_text += "Frame captured for analysis" if frame_captured else "No final frame captured"
            status_color = "yellow" if frame_captured else "red"
            
            self.prediction_label.config(text=f"📷 Final: {last_label}")
            self.start_button.config(state="normal", bg="#00c853")  # Restore vibrant green color
            self.stop_button.config(state="disabled", bg="#757575")  # Dimmed color when disabled
            self.capture_button.config(state="disabled", bg="#757575")  # Disable capture button
            self.connection_status.config(text=status_text, fg=status_color)
            
        except Exception as e:
            # Handle any unexpected errors during camera stopping
            error_msg = f"Error stopping camera: {str(e)}"
            print(error_msg)
            messagebox.showerror("Error", error_msg)
            
            # Ensure UI is in a consistent state
            self.is_running = False
            self.start_button.config(state="normal", bg="#00c853")
            self.stop_button.config(state="disabled", bg="#757575")
            self.capture_button.config(state="disabled", bg="#757575")
            self.connection_status.config(text="Error stopping camera", fg="red")

    def exit_app(self):
        """Exit cleanly."""
        self.stop_camera()
        self.root.destroy()
        
    def capture_frame(self):
        """Capture current frame for analysis without stopping the stream."""
        # Get current frame
        frame = None
        capture_success = False
        error_message = "Unknown error occurred during capture"
        
        # Update UI to show capture in progress
        self.capture_button.config(state="disabled", bg="#64B5F6")  # Light blue during capture
        self.connection_status.config(text="Capturing frame...", fg="blue")
        self.root.update()  # Force UI update
        
        try:
            if self.camera_type_var.get() == "ip" and "/shot.jpg" in self.ip_camera_url:
                # IP Webcam app - fetch JPEG image
                try:
                    # Multiple attempts for reliability
                    for attempt in range(3):
                        response = requests.get(self.ip_camera_url, timeout=2)
                        if response.status_code == 200:
                            img_array = np.array(bytearray(response.content), dtype=np.uint8)
                            frame = cv2.imdecode(img_array, -1)  # -1 means load image as is
                            if frame is not None and frame.size > 0:
                                capture_success = True
                                break
                        time.sleep(0.2)  # Short delay between attempts
                    
                    if not capture_success:
                        error_message = "Failed to get valid image from IP Webcam after multiple attempts"
                except Exception as e:
                    error_message = f"Failed to capture frame from IP Webcam: {str(e)}"
            elif self.cap and self.cap.isOpened():
                # Regular webcam or video stream - multiple attempts for reliability
                for attempt in range(3):
                    ret, frame = self.cap.read()
                    if ret and frame is not None and frame.size > 0:
                        capture_success = True
                        break
                    time.sleep(0.1)  # Short delay between attempts
                
                if not capture_success:
                    error_message = "Failed to get valid frame from camera after multiple attempts"
            else:
                error_message = "No active camera to capture from"
                
            # Process the captured frame if successful
            if capture_success and frame is not None:
                # Save the captured frame
                self.captured_frame = frame.copy()
                
                # Make prediction on captured frame with confidence
                try:
                    prediction, confidence = predict_frame(frame, return_confidence=True)
                    
                    # Display the captured frame
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame_rgb)
                    screen_w = self.root.winfo_screenwidth()
                    screen_h = self.root.winfo_screenheight()
                    img = img.resize((screen_w // 2, screen_h // 2))
                    imgtk = ImageTk.PhotoImage(image=img)
                    self.video_label.imgtk = imgtk
                    self.video_label.configure(image=imgtk)
                    
                    # Update prediction label
                    self.prediction_label.config(text=f"📸 Captured: {prediction}")
                    self.connection_status.config(text="Frame captured successfully", fg="green")
                    
                    # Flash the capture button to indicate successful capture
                    original_bg = "#2196F3"  # Original blue color
                    self.capture_button.config(bg="#64B5F6")  # Flash with lighter blue
                    self.root.after(200, lambda: self.capture_button.config(bg=original_bg, state="normal"))  # Return to original color
                    
                    # Continue the video stream after a brief pause
                    self.root.after(500, self.resume_after_capture)
                except Exception as e:
                    error_message = f"Error processing captured frame: {str(e)}"
                    capture_success = False
            
            # Handle capture failure
            if not capture_success:
                messagebox.showerror("Capture Error", error_message)
                self.connection_status.config(text=f"Capture failed: {error_message[:30]}...", fg="red")
                self.capture_button.config(state="normal", bg="#2196F3")  # Reset button state
        except Exception as e:
            # Catch any unexpected errors
            messagebox.showerror("Unexpected Error", f"An unexpected error occurred: {str(e)}")
            self.connection_status.config(text="Capture failed due to unexpected error", fg="red")
            self.capture_button.config(state="normal", bg="#2196F3")  # Reset button state
            
    def resume_after_capture(self):
        """Resume video stream after capturing a frame"""
        if self.is_running:
            # Clear the prediction buffer to avoid influence from the captured frame
            pred_buffer.clear()
            
            # Resume the video stream
            self.update_frame()

    def exit_fullscreen(self):
        """Disable fullscreen when pressing Esc."""
        self.root.attributes("-fullscreen", False)


# -----------------------------
# Run App
# -----------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = BOLT_INOVATOR_WasteClassifier(root)
    root.mainloop()

    if app.cap:
        app.cap.release()
    cv2.destroyAllWindows()
