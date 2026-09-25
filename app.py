import cv2
import os
import urllib.request

# Model filenames
face_cascade_file = 'haarcascade_frontalface_default.xml'
eye_cascade_file = 'haarcascade_eye.xml'

# Automatically download missing XML files
if not os.path.exists(face_cascade_file):
    urllib.request.urlretrieve("https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml", face_cascade_file)

if not os.path.exists(eye_cascade_file):
    urllib.request.urlretrieve("https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_eye.xml", eye_cascade_file)

face_cascade = cv2.CascadeClassifier(face_cascade_file)
eye_cascade = cv2.CascadeClassifier(eye_cascade_file)

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open laptop webcam.")
    exit()

print("SafeDrive Edge Eye-Focused Monitor Active. Press 'q' to quit.")

drowsy_frames = 0
THRESHOLD_FRAMES = 10

while True:
    ret, frame = cap.read()
    if not ret:
        break

    height, width, _ = frame.shape
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))

    if len(faces) > 1:
        faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
        faces = [faces[0]]

    eyes_found_count = 0

    for (x, y, w, h) in faces:
        # NOTE: Face box removed for a cleaner view!

        # Region of interest for eyes (upper half of the face)
        roi_gray = gray[y + int(h * 0.15):y + int(h * 0.5), x + int(w * 0.1):x + int(w * 0.9)]
        roi_color = frame[y + int(h * 0.15):y + int(h * 0.5), x + int(w * 0.1):x + int(w * 0.9)]

        eyes = eye_cascade.detectMultiScale(roi_gray, scaleFactor=1.05, minNeighbors=4, minSize=(15, 15))
        eyes_found_count = len(eyes)

        # Draw subtle blue boxes only around detected eyes
        for (ex, ey, ew, eh) in eyes:
            cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (255, 165, 0), 2)

    # --- CLEAN HUD OVERLAY BAR ---
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (width, 75), (20, 20, 20), -1)
    alpha = 0.75
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

    # Status Logic & Text Styling
    if len(faces) > 0:
        if eyes_found_count >= 1:
            drowsy_frames = 0
            status_text = "STATUS: SAFE (Eyes Open)"
            status_color = (0, 255, 120)  # Bright Green
        else:
            drowsy_frames += 1
            status_text = f"WARNING: Eyes Closed ({drowsy_frames}/{THRESHOLD_FRAMES})"
            status_color = (0, 140, 255)  # Orange
    else:
        status_text = "STATUS: No Driver Detected"
        status_color = (0, 0, 255)  # Red

    # Render Header Text Cleanly
    cv2.putText(frame, "SAFEDRIVE EDGE HUD", (20, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1, cv2.LINE_AA)
    cv2.putText(frame, status_text, (20, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2, cv2.LINE_AA)

    # Critical Alert Banner if Drowsy
    if drowsy_frames >= THRESHOLD_FRAMES:
        cv2.rectangle(frame, (0, height - 60), (width, height), (0, 0, 200), -1)
        cv2.putText(frame, "ALERT: DROWSINESS DETECTED!", (20, height - 22), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)

    cv2.imshow("SafeDrive Edge - Drowsiness Monitor", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()