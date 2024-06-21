document.addEventListener("DOMContentLoaded", function () {
    const cameraSelect = document.getElementById("id_camera");
    const canvas = document.createElement('canvas');
    const context = canvas.getContext("2d");
    const rois = []; // Array to store ROI coordinates
    let img = new Image();
    let startX, startY, isDrawing = false;

    canvas.id = 'roiCanvas';
    canvas.style.border = '1px solid #000';
    canvas.width = 640; // Set canvas width and height based on your requirements
    canvas.height = 480; // Adjust as necessary
    document.querySelector('.form-row.field-camera').appendChild(canvas);

    cameraSelect.addEventListener("change", function () {
        const cameraId = this.value;
        fetch(`/safety_detection/get_camera_frame/${cameraId}/`) // Adjust URL as per your URL configuration
            .then(response => {
                if (!response.ok) {
                    console.error(`Failed to fetch frame: ${response.statusText}`);
                    return;
                }
                return response.blob();
            })
            .then(blob => {
                const url = URL.createObjectURL(blob);
                img.onload = () => {
                    drawFrame(); // Draw existing ROIs on canvas
                };
                img.src = url;
            })
            .catch(error => {
                console.error('Error fetching camera frame:', error);
            });
    });

    canvas.addEventListener("mousedown", function (e) {
        startX = e.offsetX;
        startY = e.offsetY;
        isDrawing = true;
    });

    canvas.addEventListener("mousemove", function (e) {
        if (isDrawing) {
            const rectWidth = e.offsetX - startX;
            const rectHeight = e.offsetY - startY;
            drawFrame(); // Redraw frame with existing ROIs
            context.strokeStyle = "red";
            context.strokeRect(startX, startY, rectWidth, rectHeight);
        }
    });

    canvas.addEventListener("mouseup", function (e) {
        if (isDrawing) {
            isDrawing = false;
            const rectWidth = e.offsetX - startX;
            const rectHeight = e.offsetY - startY;
            const roi = {
                x1: startX,
                y1: startY,
                x2: startX + rectWidth,
                y2: startY + rectHeight
            };
            rois.push(roi); // Store the ROI coordinates
            updateHiddenInputs(); // Update hidden inputs for form submission
        }
    });

    function drawFrame() {
        context.clearRect(0, 0, canvas.width, canvas.height);
        context.drawImage(img, 0, 0, canvas.width, canvas.height); // Draw image on canvas
        rois.forEach(roi => {
            context.strokeStyle = "red";
            context.strokeRect(roi.x1, roi.y1, roi.x2 - roi.x1, roi.y2 - roi.y1); // Draw all ROIs
        });
    }

    function updateHiddenInputs() {
        // Update hidden input with JSON stringified ROIs
        const roiInput = document.getElementById("id_roi_coordinates");
        if (roiInput) {
            roiInput.value = JSON.stringify(rois);
        }
    }
});
