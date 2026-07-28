document.addEventListener("DOMContentLoaded", () => {
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const previewImage = document.getElementById('preview-image');
    const captureBtn = document.getElementById('capture-btn');
    const retakeBtn = document.getElementById('retake-btn');
    const filterBtn = document.getElementById('filter-btn');
    const sendControls = document.getElementById('send-controls');
    const sendSnapBtns = document.querySelectorAll('.send-snap-btn');
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    let currentStream = null;
    let capturedBlob = null;
    
    const filters = [
        "none",
        "grayscale(100%)",
        "sepia(100%)",
        "invert(100%)",
        "saturate(300%) hue-rotate(45deg)", // Neon-ish
        "contrast(150%) brightness(110%)"
    ];
    let currentFilterIndex = 0;

    async function startCamera() {
        try {
            currentStream = await navigator.mediaDevices.getUserMedia({ 
                video: { facingMode: "user" } // Front camera default
            });
            video.srcObject = currentStream;
        } catch (err) {
            console.error("Camera access denied or unavailable", err);
            alert("Could not access camera. Please allow camera permissions.");
        }
    }

    // Stop Camera
    function stopCamera() {
        if (currentStream) {
            currentStream.getTracks().forEach(track => track.stop());
        }
    }

    // Cycle Filters
    filterBtn.addEventListener('click', () => {
        currentFilterIndex = (currentFilterIndex + 1) % filters.length;
        video.style.filter = filters[currentFilterIndex];
        previewImage.style.filter = filters[currentFilterIndex]; // Apply same to preview
    });

    // Capture Snap
    captureBtn.addEventListener('click', () => {
        // Set canvas size to video size
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        
        const ctx = canvas.getContext('2d');
        
        // Very important: We must apply the CSS filter to the canvas context BEFORE drawing
        // so the filter is actually saved into the JPEG file!
        ctx.filter = filters[currentFilterIndex];
        
        // Draw video frame to canvas
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        // Show preview image
        previewImage.src = canvas.toDataURL('image/jpeg', 0.8);
        
        // Convert to blob for uploading later
        canvas.toBlob((blob) => {
            capturedBlob = blob;
        }, 'image/jpeg', 0.8);

        // Switch UI Mode
        video.classList.add('hidden');
        previewImage.classList.remove('hidden');
        captureBtn.classList.add('hidden');
        sendControls.classList.remove('hidden');
        
        stopCamera();
    });

    // Retake Snap
    retakeBtn.addEventListener('click', () => {
        capturedBlob = null;
        previewImage.src = "";
        
        video.classList.remove('hidden');
        previewImage.classList.add('hidden');
        captureBtn.classList.remove('hidden');
        sendControls.classList.add('hidden');
        
        startCamera();
    });

    // Upload and Send Snap via AJAX
    sendSnapBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            if (!capturedBlob) return;
            
            const friendId = this.getAttribute('data-friend-id');
            const formData = new FormData();
            
            // Generate a random filename
            const fileName = `snap_${Date.now()}.jpg`;
            formData.append('image', capturedBlob, fileName);
            
            // Add a tiny loading spinner to the button
            const originalIcon = this.innerHTML;
            this.innerHTML = '<span class="loading loading-spinner loading-xs"></span>';
            this.disabled = true;

            // Post to send_message endpoint
            fetch(`/send-message/${friendId}`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken
                },
                body: formData
            })
            .then(response => {
                if(response.ok) {
                    // Redirect to chat room
                    window.location.href = `/chat-details/${friendId}`;
                } else {
                    alert("Failed to send snap.");
                    this.innerHTML = originalIcon;
                    this.disabled = false;
                }
            })
            .catch(err => {
                console.error(err);
                alert("Network error.");
                this.innerHTML = originalIcon;
                this.disabled = false;
            });
        });
    });

    // Init
    startCamera();
})