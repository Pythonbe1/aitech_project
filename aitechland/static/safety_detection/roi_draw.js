document.addEventListener("DOMContentLoaded", function () {
    const cameraSelect = document.getElementById("id_camera");
    const canvas = document.createElement('canvas');
    const context = canvas.getContext("2d");
    const rois = [];
    let img = new Image();
    let startX, startY, isDrawing = false;

    // Set up the canvas
    canvas.id = 'roiCanvas';
    canvas.style.border = '1px solid #000';
    canvas.width = 640;  // Adjust based on your needs
    canvas.height = 480; // Adjust based on your needs
    document.querySelector('.form-row.field-camera').appendChild(canvas);

    // Fetch and display the frame when a camera is selected
    cameraSelect.addEventListener("change", function () {
        const cameraId = this.value;
        fetch(`/safety_detection/get_camera_frame/${cameraId}/`)
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
                    drawFrame();
                };
                img.src = url;
            })
            .catch(error => {
                console.error('Error fetching camera frame:', error);
            });
    });

    // Start drawing a rectangle
    canvas.addEventListener("mousedown", function (e) {
        startX = e.offsetX;
        startY = e.offsetY;
        isDrawing = true;
    });

    // Draw the rectangle as the mouse moves
    canvas.addEventListener("mousemove", function (e) {
        if (isDrawing) {
            const rectWidth = e.offsetX - startX;
            const rectHeight = e.offsetY - startY;
            drawFrame();
            context.strokeStyle = "red";
            context.strokeRect(startX, startY, rectWidth, rectHeight);
        }
    });

    // Finish drawing the rectangle and save the coordinates
    canvas.addEventListener("mouseup", function (e) {
        if (isDrawing) {
            isDrawing = false;
            const rectWidth = e.offsetX - startX;
            const rectHeight = e.offsetY - startY;
            const roi = {
                x: startX,
                y: startY,
                width: rectWidth,
                height: rectHeight
            };
            rois.push(roi);
            updateHiddenInputs();
        }
    });

    // Draw the current frame and any existing ROIs
    function drawFrame() {
        context.clearRect(0, 0, canvas.width, canvas.height);
        context.drawImage(img, 0, 0, canvas.width, canvas.height);
        rois.forEach(roi => {
            context.strokeStyle = "red";
            context.strokeRect(roi.x, roi.y, roi.width, roi.height);
        });
    }

    // Convert ROIs to YOLO format and update the hidden input
    function updateHiddenInputs() {
        const roiInput = document.getElementById("id_roi_data");
        if (roiInput) {
            const yoloData = rois.map(roi => {
                // Convert to YOLO format
                const x_center = (roi.x + roi.width / 2) / canvas.width;
                const y_center = (roi.y + roi.height / 2) / canvas.height;
                const width = roi.width / canvas.width;
                const height = roi.height / canvas.height;

                // Format as YOLO
                return `${x_center.toFixed(6)} ${y_center.toFixed(6)} ${width.toFixed(6)} ${height.toFixed(6)}`;
            });
            roiInput.value = yoloData.join("\n");
        }
    }
});
