# ML Model Architecture Specification

## Overview

This document outlines the architecture, specifications, and integration requirements for the waste classification ML model used in our system. The model is designed to classify waste items into different categories based on image input.

## Input Specifications

### Data Formats

- **Image Input**: 
  - Format: JPEG, PNG
  - Resolution: Minimum 224x224 pixels (will be resized internally)
  - Color Space: RGB
  - Bit Depth: 8-bit per channel
  - Maximum File Size: 5MB

### Processing Requirements

- **Preprocessing Pipeline**:
  1. Image Validation (format, size, content)
  2. Resizing to 224x224 pixels with aspect ratio preservation
  3. Normalization (pixel values scaled to [-1, 1] range)
  4. Data Augmentation (during training only):
     - Random horizontal flips
     - Random brightness/contrast adjustments
     - Random cropping

## Output Specifications

### Response Structure

```json
{
  "classification": "recyclable",  // Primary waste category
  "class_code": "R",            // Category code (R, O, H)
  "confidence": 0.95,            // Confidence score (0.0-1.0)
  "alternatives": [              // Alternative classifications
    {
      "classification": "hazardous",
      "class_code": "H",
      "confidence": 0.03
    },
    {
      "classification": "organic",
      "class_code": "O",
      "confidence": 0.02
    }
  ],
  "processing_time": 0.45,       // Processing time in seconds
  "source": "gemini_api"         // Source of classification (local_model, gemini_api, openai_api)
}
```

## Model Architecture

### Base Model

- **Architecture**: MobileNetV2
- **Input Shape**: 224x224x3
- **Output Classes**: 3 (Recyclable, Organic, Hazardous)
- **Parameters**: ~3.5 million
- **Model Size**: ~14MB

### Key Components

1. **Feature Extraction**: MobileNetV2 backbone with depthwise separable convolutions
2. **Classification Head**: Global average pooling followed by fully connected layers
3. **Activation**: Softmax for final classification probabilities

## Performance Metrics

### Accuracy Thresholds

- **Overall Accuracy**: ≥ 90% on validation set
- **Per-Class Precision**: ≥ 85%
- **Per-Class Recall**: ≥ 85%
- **F1 Score**: ≥ 0.87

### Processing Time Benchmarks

- **Local Model**:
  - Inference Time: < 200ms on CPU
  - End-to-End Processing: < 500ms

- **External API (Gemini/OpenAI)**:
  - Total Response Time: < 2000ms (including network latency)

### Resource Utilization Limits

- **Memory Usage**: < 200MB during inference
- **CPU Usage**: < 30% of a single core during inference
- **GPU Usage** (if available): < 10% of GPU memory

## Integration Requirements

### Hardware Specifications

#### Minimum Requirements

- **CPU**: Dual-core processor, 2.0 GHz or higher
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 100MB for model files
- **Camera**: Any standard webcam or smartphone camera

#### Recommended Requirements

- **CPU**: Quad-core processor, 2.5 GHz or higher
- **RAM**: 8GB or higher
- **GPU**: Any dedicated GPU with at least 2GB VRAM (optional, for faster inference)
- **Camera**: HD webcam (720p or higher)

### Software Dependencies

- **Python**: 3.8 or higher
- **TensorFlow**: 2.8.0 or higher
- **OpenCV**: 4.5.0 or higher
- **NumPy**: 1.20.0 or higher
- **Flask**: 2.0.0 or higher (for API server)
- **Requests**: 2.25.0 or higher (for API client)

### Compatibility Constraints

- **Operating Systems**: Windows 10+, macOS 10.15+, Ubuntu 20.04+
- **Browsers** (for web integration): Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Mobile Platforms**: iOS 14+, Android 10+

## Fallback Mechanisms

The system implements a tiered approach to classification:

1. **Primary**: External AI API (Gemini or OpenAI) if available and configured
2. **Secondary**: Local MobileNetV2 model if external API fails or is unavailable
3. **Tertiary**: Rule-based classification based on image features if both primary and secondary methods fail

## Model Versioning and Updates

- **Current Version**: 2.1.0
- **Update Mechanism**: Automatic updates via API endpoint `/api/model/update`
- **Backward Compatibility**: All updates maintain the same input/output interface

## Security Considerations

- All image data is processed locally unless external API is used
- No user data is stored permanently
- API keys are stored securely in environment variables
- All API communications use HTTPS encryption

## Monitoring and Logging

The model includes built-in monitoring capabilities:

- Performance metrics logging
- Error rate tracking
- Processing time monitoring
- Classification distribution analysis

Logs are available via the `/api/logs` endpoint (requires authentication).