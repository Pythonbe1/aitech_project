from django.test import TestCase

# Create your tests here.
import cv2

video = cv2.VideoCapture("rtsp:/admin:Aa123456@192.168.140.228:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif")
# video = cv2.VideoCapture("rtsp:/admin:Aa123456@192.168.140.180:554/Streaming/Channels/1")

if not video.isOpened():
    print("Error: Unable to open video stream")
    exit()

while True:
    ret, frame = video.read()

    if not ret:
        print("Error: Failed to read frame from video stream")
        break

    cv2.imshow('Frame', frame)
    print(frame)

    # Check for 'q' key press to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video.release()
cv2.destroyAllWindows()
