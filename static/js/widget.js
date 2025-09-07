/**
 * BOLT INNOVATORS - Smart Waste Classification Widget
 * This file provides an easy way to integrate the waste classification system into any website
 */

class WasteClassifierWidget {
    constructor(options = {}) {
        // Default configuration
        this.config = {
            apiUrl: options.apiUrl || window.location.origin,
            containerId: options.containerId || 'waste-classifier-widget',
            width: options.width || '100%',
            height: options.height || '600px',
            theme: options.theme || 'dark', // 'dark' or 'light'
            showUpload: options.showUpload !== undefined ? options.showUpload : true,
            showWebcam: options.showWebcam !== undefined ? options.showWebcam : true,
            autoStart: options.autoStart !== undefined ? options.autoStart : false,
            onResult: options.onResult || null, // Callback function for classification results
            customStyles: options.customStyles || null
        };

        // Create container if it doesn't exist
        this.container = document.getElementById(this.config.containerId);
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = this.config.containerId;
            document.body.appendChild(this.container);
        }

        // Set container styles
        this.container.style.width = this.config.width;
        this.container.style.height = this.config.height;
        this.container.style.overflow = 'hidden';
        this.container.style.borderRadius = '8px';
        this.container.style.boxShadow = '0 4px 10px rgba(0, 0, 0, 0.1)';

        // Initialize the widget
        this.init();
    }

    init() {
        // Create iframe for the widget
        this.iframe = document.createElement('iframe');
        this.iframe.style.width = '100%';
        this.iframe.style.height = '100%';
        this.iframe.style.border = 'none';
        this.iframe.style.borderRadius = '8px';
        
        // Set the source URL with query parameters for configuration
        const params = new URLSearchParams();
        params.append('theme', this.config.theme);
        params.append('showUpload', this.config.showUpload);
        params.append('showWebcam', this.config.showWebcam);
        params.append('autoStart', this.config.autoStart);
        params.append('widget', 'true');
        
        this.iframe.src = `${this.config.apiUrl}/?${params.toString()}`;
        
        // Add iframe to container
        this.container.appendChild(this.iframe);
        
        // Setup message listener for communication with the iframe
        window.addEventListener('message', this.handleMessage.bind(this));
    }

    handleMessage(event) {
        // Verify the origin of the message
        if (event.origin !== this.config.apiUrl.replace(/\/$/, '')) {
            return;
        }
        
        const data = event.data;
        
        // Handle classification results
        if (data.type === 'classification-result' && this.config.onResult) {
            this.config.onResult(data.result);
        }
    }

    // Public methods
    startCamera() {
        this.sendMessage({ action: 'startCamera' });
    }

    stopCamera() {
        this.sendMessage({ action: 'stopCamera' });
    }

    captureImage() {
        this.sendMessage({ action: 'captureImage' });
    }

    // Send message to iframe
    sendMessage(message) {
        if (this.iframe.contentWindow) {
            this.iframe.contentWindow.postMessage(message, this.config.apiUrl);
        }
    }
}

// Example usage:
/*
const classifier = new WasteClassifierWidget({
    containerId: 'my-waste-classifier',
    width: '800px',
    height: '600px',
    theme: 'dark',
    showUpload: true,
    showWebcam: true,
    autoStart: false,
    onResult: function(result) {
        console.log('Classification result:', result);
        // Do something with the result
    }
});
*/

// Make it available globally
window.WasteClassifierWidget = WasteClassifierWidget;