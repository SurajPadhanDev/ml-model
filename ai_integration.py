import os
import base64
from io import BytesIO
import requests
import google.generativeai as genai
from openai import OpenAI
from dotenv import load_dotenv
from PIL import Image
import numpy as np
import cv2
import time
import json

# Load environment variables
load_dotenv()

# Initialize API clients with provided key as fallback
gemini_api_key = os.getenv("GEMINI_API_KEY", "AIzaSyBsDwFhmqIJzj3ahe9N9fhR5iy1_AKFzbQ")
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

# Real-time image upload detection with event triggers
class ImageUploadDetector:
    def __init__(self, callback=None, auto_classify=True, event_handlers=None):
        """
        Initialize the image upload detector.
        
        Args:
            callback: Function to call when an image is classified
            auto_classify: Whether to automatically classify uploaded images
            event_handlers: Dictionary of event handlers for different events
        """
        self.callback = callback
        self.auto_classify = auto_classify
        self.event_handlers = event_handlers or {}
        self.last_upload_time = 0
        self.upload_count = 0
        self.recent_uploads = []
        self.max_recent_uploads = 10
    
    def register_event_handler(self, event_type, handler):
        """
        Register an event handler for a specific event type.
        
        Args:
            event_type: Type of event (e.g., 'upload', 'classify', 'error')
            handler: Function to call when the event occurs
        """
        self.event_handlers[event_type] = handler
    
    def trigger_event(self, event_type, data=None):
        """
        Trigger an event and call the registered handler if available.
        
        Args:
            event_type: Type of event to trigger
            data: Data to pass to the event handler
        """
        if event_type in self.event_handlers and callable(self.event_handlers[event_type]):
            self.event_handlers[event_type](data)
    
    def process_image(self, image, metadata=None):
        """
        Process an uploaded image, optionally classify it, and trigger events.
        
        Args:
            image: The image to process (PIL Image, numpy array, or file path)
            metadata: Additional metadata about the image
        
        Returns:
            Classification result if auto_classify is True, otherwise None
        """
        # Update upload statistics
        current_time = time.time()
        self.last_upload_time = current_time
        self.upload_count += 1
        
        # Create upload record
        upload_record = {
            'timestamp': current_time,
            'metadata': metadata or {},
        }
        
        # Add to recent uploads, maintaining max size
        self.recent_uploads.append(upload_record)
        if len(self.recent_uploads) > self.max_recent_uploads:
            self.recent_uploads.pop(0)
        
        # Trigger upload event
        self.trigger_event('upload', {
            'image': image,
            'metadata': metadata,
            'timestamp': current_time
        })
        
        # Auto-classify if enabled
        result = None
        if self.auto_classify:
            try:
                result = classify_waste(image)
                upload_record['classification'] = result
                
                # Trigger classification event
                self.trigger_event('classify', {
                    'image': image,
                    'result': result,
                    'metadata': metadata,
                    'timestamp': current_time
                })
            except Exception as e:
                error_info = {
                    'error': str(e),
                    'image': image,
                    'metadata': metadata,
                    'timestamp': current_time
                }
                upload_record['error'] = str(e)
                
                # Trigger error event
                self.trigger_event('error', error_info)
        
        # Call the callback if provided
        if self.callback and callable(self.callback):
            self.callback(image, result, metadata)
        
        return result
    
    def get_statistics(self):
        """
        Get statistics about image uploads.
        
        Returns:
            Dictionary with upload statistics
        """
        return {
            'total_uploads': self.upload_count,
            'last_upload_time': self.last_upload_time,
            'recent_uploads': self.recent_uploads
        }

# Function to encode image for API requests
def encode_image(image):
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# Gemini Vision API for Image Classification
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

# OpenAI Vision API for Image Classification
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