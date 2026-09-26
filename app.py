"""
SafeDrive Edge - Python Bridge (motor only, buzzer skipped for now)
Same detection logic as your original script. Calls /alert/on and
/alert/off on the ESP32 to pulse the vibration motor when drowsy.
"""

import cv2
import os
import urllib.request
import requests

# --- ESP32 CONFIGURATION ---
ESP32_IP = "10.110.1.184"  # <-- update this to match the IP printed in Serial Monitor
REQUEST_TIMEOUT_S = 0.3

face_cascade_file = 'haarcascade_frontalface_default.xml'
eye_cascade_file = 'haarcascade_eye.xml'

if not os.path.exists(face_cascade_file):
    urllib.request.urlretrieve(
        "https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml",
        face_cascade_file)

if not os.path.exists(eye_cascade_file):
    urllib.request.urlretrieve(
        "https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_eye.xml",
        eye_cascade_file)

face_cascade = cv2.CascadeClassifier(face_cascade_file)
eye_cascade = cv2.CascadeClassifier(eye_cascade_file)

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open laptop webcam.")
    exit()

print("SafeDrive Edge (motor-only) Active. Press 'q' to quit.")

drowsy_frames = 0
THRESHOLD_FRAMES = 10
alert_is_on = False  # track last sent state so we don't spam requests every frame

def set_alert(on: bool):
    global alert_is_on
    if on == alert_is_on:
        return  # already in this state, don't resend every frame
    endpoint = "on" if on else "off"
    try:
        requests.get(f"http://{ESP32_IP}/alert/{endpoint}", timeout=REQUEST_TIMEOUT_S)
        alert_is_on = on
    except requests.RequestException as e:
        print(f"Could not reach ESP32: {e}")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Camera read failed, exiting.")
        break

    height, width, _ = frame.shape
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))

    if len(faces) > 1:
        faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
        faces = [faces[0]]

    eyes_found_count = 0
    for (x, y, w, h) in faces:
        roi_gray = gray[y + int(h * 0.15):y + int(h * 0.5), x + int(w * 0.1):x + int(w * 0.9)]
        roi_color = frame[y + int(h * 0.15):y + int(h * 0.5), x + int(w * 0.1):x + int(w * 0.9)]
        eyes = eye_cascade.detectMultiScale(roi_gray, scaleFactor=1.05, minNeighbors=4, minSize=(15, 15))
        eyes_found_count = len(eyes)
        for (ex, ey, ew, eh) in eyes:
            cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (255, 165, 0), 2)

    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (width, 75), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

    if len(faces) > 0:
        if eyes_found_count >= 1:
            drowsy_frames = 0
            status_text = "STATUS: SAFE (Eyes Open)"
            status_color = (0, 255, 120)
        else:
            drowsy_frames += 1
            status_text = f"WARNING: Eyes Closed ({drowsy_frames}/{THRESHOLD_FRAMES})"
            status_color = (0, 140, 255)
    else:
        status_text = "STATUS: No Driver Detected"
        status_color = (0, 0, 255)

    cv2.putText(frame, "SAFEDRIVE EDGE HUD", (20, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1, cv2.LINE_AA)
    cv2.putText(frame, status_text, (20, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2, cv2.LINE_AA)

    if drowsy_frames >= THRESHOLD_FRAMES:
        cv2.rectangle(frame, (0, height - 60), (width, height), (0, 0, 200), -1)
        cv2.putText(frame, "ALERT: DROWSINESS DETECTED!", (20, height - 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
        set_alert(True)
    else:
        set_alert(False)

    cv2.imshow("SafeDrive Edge - Drowsiness Monitor", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        set_alert(False)
        break

cap.release()
cv2.destroyAllWindows()