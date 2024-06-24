document.addEventListener("DOMContentLoaded", function () {
    const cameraSelect = document.getElementById("id_camera");
    const canvas = document.createElement('canvas');
    const context = canvas.getContext("2d");
    const rois = [];
    let img = new Image();
    let startX, startY, isDrawing = false;

    canvas.id = 'roiCanvas';
    canvas.style.border = '1px solid #000';
    canvas.width = 640;
    canvas.height = 480;
    document.querySelector('.form-row.field-camera').appendChild(canvas);

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

    canvas.addEventListener("mousedown", function (e) {
        startX = e.offsetX;
        startY = e.offsetY;
        isDrawing = true;
    });

    canvas.addEventListener("mousemove", function (e) {
        if (isDrawing) {
            const rectWidth = e.offsetX - startX;
            const rectHeight = e.offsetY - startY;
            drawFrame();
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
                x: startX,
                y: startY,
                width: rectWidth,
                height: rectHeight
            };
            rois.push(roi);
            updateHiddenInputs();
        }
    });

    function drawFrame() {
        context.clearRect(0, 0, canvas.width, canvas.height);
        context.drawImage(img, 0, 0, canvas.width, canvas.height);
        rois.forEach(roi => {
            context.strokeStyle = "red";
            context.strokeRect(roi.x, roi.y, roi.width, roi.height);
        });
    }

    function updateHiddenInputs() {
        const roiInput = document.getElementById("id_roi_data");
        if (roiInput) {
            roiInput.value = JSON.stringify(rois);
        }
    }
});
