# Loveable Platform UI Components Design

## Overview

This document outlines the design specifications for responsive UI components that adapt to all Loveable platform interfaces. The components are designed to ensure full compatibility with Loveable's technical specifications while providing a seamless user experience.

## Design Principles

- **Responsive Design**: All components adapt to various screen sizes and orientations
- **Accessibility**: WCAG 2.1 AA compliance for all components
- **Consistency**: Uniform design language across all platform interfaces
- **Performance**: Optimized for minimal load times and smooth interactions
- **Modularity**: Components can be used independently or combined as needed

## Core Components

### 1. Camera Interface

#### Features

- Responsive video container that maintains aspect ratio
- Camera selection dropdown for devices with multiple cameras
- Capture button with visual feedback states
- Stop button with confirmation on long-running sessions
- Status indicators for camera state and processing

#### Responsive Behavior

- **Desktop**: Full-width video with controls below
- **Tablet**: Scaled video with controls below or side-by-side
- **Mobile**: Full-width video with floating controls overlay

#### Implementation

```html
<div class="camera-container">
  <div class="video-wrapper">
    <video id="camera-feed" autoplay playsinline></video>
    <div class="camera-overlay">
      <div class="status-indicator" id="camera-status">Camera Ready</div>
    </div>
  </div>
  
  <div class="camera-controls">
    <select id="camera-select" class="camera-select">
      <option value="">Select Camera</option>
    </select>
    
    <div class="button-group">
      <button id="capture-btn" class="primary-btn">
        <i class="fa fa-camera"></i> Capture
      </button>
      <button id="stop-btn" class="secondary-btn">
        <i class="fa fa-stop"></i> Stop
      </button>
    </div>
  </div>
</div>
```

### 2. Classification Results Display

#### Features

- Clear visual distinction between waste categories
- Confidence level indicator
- Source information (local model vs. external AI)
- Processing time display
- Historical results comparison (optional)

#### Responsive Behavior

- **Desktop**: Side-by-side with camera feed
- **Tablet**: Below camera feed or side-by-side depending on orientation
- **Mobile**: Full-width below camera feed

#### Implementation

```html
<div class="results-container">
  <div class="result-card">
    <h3 class="result-title">Classification Result</h3>
    
    <div class="result-content">
      <div class="result-icon recyclable">
        <i class="fa fa-recycle"></i>
      </div>
      
      <div class="result-details">
        <p class="result-type">Recyclable</p>
        <div class="confidence-bar">
          <div class="confidence-level" style="width: 95%;"></div>
          <span class="confidence-text">95% Confidence</span>
        </div>
        <p class="result-meta">Source: Gemini API</p>
        <p class="result-meta">Processing Time: 0.45s</p>
      </div>
    </div>
    
    <div class="result-actions">
      <button class="action-btn">Save Result</button>
      <button class="action-btn">Share</button>
    </div>
  </div>
</div>
```

### 3. Upload Interface

#### Features

- Drag-and-drop file upload area
- File browser button
- Upload progress indicator
- File type validation with error messages
- Auto-classification on upload

#### Responsive Behavior

- **Desktop**: Large drop area with prominent instructions
- **Tablet**: Medium-sized drop area with condensed instructions
- **Mobile**: Simplified interface prioritizing the file selection button

#### Implementation

```html
<div class="upload-container" id="file-upload-area">
  <div class="upload-inner">
    <i class="fa fa-cloud-upload-alt upload-icon"></i>
    <h3 class="upload-title">Upload Image for Classification</h3>
    <p class="upload-instructions">Drag and drop an image here, or click to select</p>
    
    <div class="upload-actions">
      <label for="file-input" class="upload-btn">Select Image</label>
      <input type="file" id="file-input" accept="image/*" hidden>
    </div>
    
    <p class="upload-formats">Supported formats: JPG, PNG (Max 5MB)</p>
  </div>
  
  <div class="upload-progress" hidden>
    <div class="progress-bar">
      <div class="progress-fill"></div>
    </div>
    <p class="progress-text">Uploading... <span id="progress-percent">0%</span></p>
  </div>
</div>
```

### 4. Navigation Component

#### Features

- Responsive navigation bar/menu
- Active state indicators
- Collapsible on mobile devices
- Smooth transitions between states

#### Responsive Behavior

- **Desktop**: Horizontal navigation bar
- **Tablet**: Horizontal bar with optional dropdown for secondary items
- **Mobile**: Hamburger menu with slide-in navigation panel

#### Implementation

```html
<nav class="main-nav">
  <div class="nav-logo">
    <img src="/static/images/logo.svg" alt="Loveable Logo">
  </div>
  
  <button class="nav-toggle" aria-label="Toggle Navigation">
    <span class="toggle-bar"></span>
    <span class="toggle-bar"></span>
    <span class="toggle-bar"></span>
  </button>
  
  <ul class="nav-menu">
    <li class="nav-item active"><a href="#">Classifier</a></li>
    <li class="nav-item"><a href="#">History</a></li>
    <li class="nav-item"><a href="#">Statistics</a></li>
    <li class="nav-item"><a href="#">Settings</a></li>
    <li class="nav-item"><a href="#">Help</a></li>
  </ul>
</nav>
```

## User Experience Flows

### 1. Camera Classification Flow

1. User arrives at the application
2. Camera permission is requested (with clear explanation)
3. Once granted, camera feed is displayed with ready state
4. User clicks capture button
5. Visual feedback indicates processing state
6. Classification result is displayed with animation
7. User can capture another image or stop the camera

### 2. Upload Classification Flow

1. User navigates to upload section
2. User drags an image or clicks to select
3. Upload progress is displayed
4. Automatic classification begins after upload
5. Result is displayed with the same format as camera classification
6. User can upload another image or switch to camera mode

## Feedback Mechanisms

### Visual Feedback

- **Loading States**: Spinners and progress bars for all asynchronous operations
- **Success States**: Green checkmarks and success messages
- **Error States**: Red indicators with clear error messages
- **Hover/Focus States**: Subtle highlights for interactive elements

### Status Messages

- Clear, concise messages for all system states
- Temporary toast notifications for non-critical information
- Modal dialogs for critical errors or confirmations
- Inline validation messages for form inputs

## Styling Guidelines

### Color Palette

- **Primary**: #3498db (Blue)
- **Secondary**: #2ecc71 (Green)
- **Accent**: #f39c12 (Orange)
- **Error**: #e74c3c (Red)
- **Background**: #f5f7fa (Light Gray)
- **Text**: #2c3e50 (Dark Blue)

### Typography

- **Primary Font**: 'Roboto', sans-serif
- **Headings**: 'Roboto Condensed', sans-serif
- **Base Size**: 16px
- **Scale Ratio**: 1.25 (Major Third)

### Spacing System

- Base unit: 8px
- Spacing scale: 8px, 16px, 24px, 32px, 48px, 64px

### Breakpoints

- **Mobile**: < 768px
- **Tablet**: 768px - 1023px
- **Desktop**: ≥ 1024px

## Accessibility Features

- High contrast mode support
- Keyboard navigation for all interactive elements
- Screen reader compatible markup
- Focus management for modal dialogs
- Alternative text for all images
- Minimum touch target size of 44x44px

## Performance Optimizations

- Lazy loading for off-screen components
- Image optimization and responsive images
- Minimal DOM updates during classification
- Debounced event handlers for resize events
- CSS animations optimized for GPU acceleration

## Implementation Notes

- All components use CSS Grid and Flexbox for layout
- JavaScript interactions use event delegation where appropriate
- Components are built with progressive enhancement in mind
- All interactive elements have appropriate ARIA attributes
- CSS custom properties used for theming and consistency