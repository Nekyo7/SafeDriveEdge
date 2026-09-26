"""
SafeDrive Edge - Python Bridge (drop-in replacement)
-----------------------------------------------------
Same detection logic as your original script, plus:
  - Sends ?level=0..3 instead of on/off, matching the new firmware
  - Real error handling + logging instead of bare except: pass
  - Camera-disconnect detection with one reconnect attempt
  - ESP32 comms-timeout detection (3 consecutive failures) shown on the HUD
  - CSV logging of every alert level change with timestamps
"""

import cv2
import os
import csv
import time
import logging
import urllib.request
import requests
from datetime import datetime

# --- ESP32 CONFIGURATION ---
ESP32_IP = "10.110.1.184"
REQUEST_TIMEOUT_S = 0.3           # a little more headroom than the original 0.05s
MAX_CONSECUTIVE_FAILURES = 3

# --- LOGGING SETUP ---
logging.basicConfig(
    filename="safedrive_edge.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
ALERT_LOG_FILE = "alert_log.csv"
if not os.path.exists(ALERT_LOG_FILE):
    with open(ALERT_LOG_FILE, "w", newline="") as f:
        csv.writer(f).writerow(["timestamp", "level", "eyes_closed_frames"])

def log_alert_event(level, drowsy_frames):
    with open(ALERT_LOG_FILE, "a", newline="") as f:
        csv.writer(f).writerow([datetime.now().isoformat(), level, drowsy_frames])

# --- MODEL FILES ---
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

# --- ESP32 COMMS ---
consecutive_failures = 0
esp32_online = True
last_sent_level = -1  # force first send

def send_alert_level(level, drowsy_frames):
    """Send the alert level to the ESP32. Only sends on change to avoid spamming."""
    global consecutive_failures, esp32_online, last_sent_level
    if level == last_sent_level:
        return
    try:
        resp = requests.get(f"http://{ESP32_IP}/alert", params={"level": level}, timeout=REQUEST_TIMEOUT_S)
        if resp.status_code == 200:
            consecutive_failures = 0
            esp32_online = True
            last_sent_level = level
            log_alert_event(level, drowsy_frames)
            logging.info(f"Alert level -> {level} (drowsy_frames={drowsy_frames})")
        else:
            raise requests.RequestException(f"HTTP {resp.status_code}")
    except requests.RequestException as e:
        consecutive_failures += 1
        logging.warning(f"ESP32 request failed ({consecutive_failures}/{MAX_CONSECUTIVE_FAILURES}): {e}")
        if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
            esp32_online = False

# --- CAMERA SETUP ---
def open_camera():
    c = cv2.VideoCapture(0)
    if not c.isOpened():
        logging.error("Could not open laptop webcam.")
        return None
    return c

cap = open_camera()
if cap is None:
    print("Error: Could not open laptop webcam.")
    exit()

print("SafeDrive Edge Full System Active. Press 'q' to quit.")

drowsy_frames = 0
THRESHOLD_FRAMES = 10
CRITICAL_FRAMES = 20   # escalate to level 2 past this
EMERGENCY_FRAMES = 35  # escalate to level 3 past this
camera_retry_deadline = 0

while True:
    ret, frame = cap.read()

    if not ret:
        logging.warning("Camera read failed — attempting one reconnect.")
        cap.release()
        time.sleep(0.5)
        cap = open_camera()
        if cap is None:
            print("Camera reconnect failed. Exiting.")
            logging.error("Camera reconnect failed. Exiting.")
            break
        continue

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

    # --- HUD OVERLAY BAR ---
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (width, 75), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

    # --- STATUS LOGIC ---
    if len(faces) > 0:
        if eyes_found_count >= 1:
            drowsy_frames = 0
            status_text = "STATUS: SAFE (Eyes Open)"
            status_color = (0, 255, 120)
        else:
            drowsy_frames += 1
            status_text = f"WARNING: Eyes Closed ({drowsy_frames})"
            status_color = (0, 140, 255)
    else:
        status_text = "STATUS: No Driver Detected"
        status_color = (0, 0, 255)

    cv2.putText(frame, "SAFEDRIVE EDGE HUD", (20, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1, cv2.LINE_AA)
    cv2.putText(frame, status_text, (20, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2, cv2.LINE_AA)

    if not esp32_online:
        cv2.putText(frame, "ESP32 OFFLINE - hardware alerts disabled", (20, height - 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2, cv2.LINE_AA)

    # --- MAP DROWSINESS TO ALERT LEVEL ---
    if drowsy_frames >= EMERGENCY_FRAMES:
        target_level = 3
        cv2.rectangle(frame, (0, height - 60), (width, height), (0, 0, 200), -1)
        cv2.putText(frame, "EMERGENCY: WAKE UP!", (20, height - 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
    elif drowsy_frames >= CRITICAL_FRAMES:
        target_level = 2
        cv2.rectangle(frame, (0, height - 60), (width, height), (0, 60, 220), -1)
        cv2.putText(frame, "CRITICAL: DROWSINESS DETECTED", (20, height - 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
    elif drowsy_frames >= THRESHOLD_FRAMES:
        target_level = 1
        cv2.rectangle(frame, (0, height - 60), (width, height), (0, 140, 255), -1)
        cv2.putText(frame, "WARNING: Eyes closing", (20, height - 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
    else:
        target_level = 0

    if esp32_online or target_level == 0:
        send_alert_level(target_level, drowsy_frames)

    cv2.imshow("SafeDrive Edge - Drowsiness Monitor", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        send_alert_level(0, drowsy_frames)
        break

cap.release()
cv2.destroyAllWindows()
