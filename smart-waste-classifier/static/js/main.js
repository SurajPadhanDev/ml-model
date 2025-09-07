document.addEventListener('DOMContentLoaded', () => {
    // --- COMMON ELEMENTS ---
    const socket = io();

    // --- STATIC IMAGE UPLOAD LOGIC ---
    const imageUploadInput = document.getElementById('imageUpload');
    const imagePreview = document.getElementById('imagePreview');
    const uploadResultCard = document.getElementById('uploadResultCard');
    const cardInner = uploadResultCard.querySelector('.card-inner');
    const cardFront = uploadResultCard.querySelector('.card-front p');
    const uploadPrediction = document.getElementById('uploadPrediction');
    const uploadConfidence = document.getElementById('uploadConfidence');
    const cardBack = uploadResultCard.querySelector('.card-back');

    imageUploadInput.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (!file) return;

        // 1. Display image preview
        const reader = new FileReader();
        reader.onload = (e) => {
            imagePreview.src = e.target.result;
            imagePreview.style.display = 'block';
        };
        reader.readAsDataURL(file);

        // 2. Prepare for prediction
        uploadResultCard.classList.remove('is-flipped');
        cardFront.textContent = 'Processing...';

        // 3. Send image to backend
        const formData = new FormData();
        formData.append('file', file);

        fetch('/predict/upload', {
            method: 'POST',
            body: formData
        })
       .then(response => response.json())
       .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            // 4. Display result on the card's back
            displayPrediction(data);
        })
       .catch(error => {
            console.error('Error:', error);
            cardFront.textContent = 'Error processing image.';
        });
    });

    function displayPrediction(data) {
        uploadPrediction.textContent = data.prediction;
        uploadConfidence.textContent = `Confidence: ${data.confidence}`;

        // Style the card back based on the prediction
        if (data.prediction.toLowerCase() === 'recyclable') {
            cardBack.className = 'card-back recyclable';
        } else {
            cardBack.className = 'card-back not-recyclable';
        }

        // 5. Flip the card to show the result
        uploadResultCard.classList.add('is-flipped');
    }

    // --- LIVE CAMERA FEED LOGIC ---
    const startCameraBtn = document.getElementById('startCameraBtn');
    const videoFeed = document.getElementById('videoFeed');
    const canvasOverlay = document.getElementById('canvasOverlay');
    const ctx = canvasOverlay.getContext('2d');
    let frameInterval;

    startCameraBtn.addEventListener('click', async () => {
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
                videoFeed.srcObject = stream;
                videoFeed.hidden = false;
                startCameraBtn.textContent = 'Stop Camera';

                videoFeed.onloadedmetadata = () => {
                    // Match canvas dimensions to video dimensions
                    canvasOverlay.width = videoFeed.videoWidth;
                    canvasOverlay.height = videoFeed.videoHeight;

                    // Start sending frames to the server at a controlled rate (e.g., 2.5 FPS)
                    frameInterval = setInterval(() => {
                        sendFrameForPrediction();
                    }, 400); // 1000ms / 400ms = 2.5 FPS
                };

            } catch (error) {
                console.error("Error accessing camera:", error);
                alert("Could not access the camera. Please ensure you have given permission.");
            }
        } else {
            alert("Your browser does not support camera access.");
        }
    });

    function sendFrameForPrediction() {
        if (videoFeed.paused || videoFeed.ended) {
            clearInterval(frameInterval);
            return;
        }
        // Draw the current video frame onto the hidden canvas
        ctx.drawImage(videoFeed, 0, 0, canvasOverlay.width, canvasOverlay.height);
        // Get the frame as a JPEG data URL (reduces data size)
        const imageDataUrl = canvasOverlay.toDataURL('image/jpeg', 0.7);
        // Send the frame over WebSocket
        socket.emit('video_frame', imageDataUrl);
    }

    // Listen for prediction results from the server
    socket.on('prediction_result', (data) => {
        drawPredictionOnCanvas(data);
    });

    function drawPredictionOnCanvas(data) {
        // Clear previous drawings
        ctx.clearRect(0, 0, canvasOverlay.width, canvasOverlay.height);

        const predictionText = `${data.prediction} (${data.confidence})`;
        const isRecyclable = data.prediction.toLowerCase() === 'recyclable';

        // Style the text
        ctx.font = 'bold 24px Roboto';
        ctx.fillStyle = isRecyclable? '#28a745' : '#dc3545';
        ctx.textAlign = 'center';
        ctx.strokeStyle = 'white';
        ctx.lineWidth = 4;

        // Position the text at the bottom center of the canvas
        const x = canvasOverlay.width / 2;
        const y = canvasOverlay.height - 20;

        // Draw stroke and then fill for a clear outline effect
        ctx.strokeText(predictionText, x, y);
        ctx.fillText(predictionText, x, y);
    }
});
