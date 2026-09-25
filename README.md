# 🚗 SafeDrive Edge

> **An offline driver-safety system designed to detect drowsiness and unsafe vehicle movement using edge-based intelligence.**

**Deep Tech & Edge AI · Smart Mobility**

---

## 🧠 What is SafeDrive Edge?

SafeDrive Edge is an **offline driver-monitoring system** that aims to detect driver drowsiness and abnormal vehicle movement in real time.

The system uses an onboard camera to monitor the driver's eyes and motion sensing to identify potential safety risks. When a risk is detected, the system can trigger **audio and haptic alerts**.

> **Driver:** "I'm not sleepy bro."
> **SafeDrive Edge:** 👁️👁️

---

## 🚨 The Problem

Driver fatigue and microsleeps can lead to delayed reactions and loss of vehicle control.

Many existing solutions can depend on internet connectivity or remote processing, while basic camera systems may struggle in low-light conditions or produce false alarms from normal blinking.

SafeDrive Edge focuses on **local, offline processing** for fast and privacy-conscious driver monitoring.

---

## 💡 Key Features

* 📷 Camera-based driver monitoring
* 👁️ Eye-state / drowsiness detection
* 🚗 Motion-based swerving detection
* 🧠 Edge processing
* 🌙 Low-light monitoring using IR
* 🔊 Audio alerts
* 📳 Haptic alerts
* 🔒 Offline-first design

---

## 🏗️ System Overview

```text
       Camera
         ↓
   ESP32-CAM
         ↓
 Local Processing
         ↓
Drowsiness + Motion Analysis
         ↓
   Safety Decision
         ↓
 🔊 Alarm + 📳 Vibration
```

---

## 📷 Current Prototype

Our current prototype uses an **AI-Thinker ESP32-CAM** as the main camera and processing platform.

### Hardware

| Component            | Purpose                  |
| -------------------- | ------------------------ |
| AI-Thinker ESP32-CAM | Main controller + camera |
| HW-417C FTDI         | Programming/flashing     |
| Jumper Wires         | Connections              |
| USB / External Power | Power & testing          |

**No MicroSD card is used.**

---

## 💻 Tech Stack

* **C++** — ESP32 firmware
* **Arduino IDE 2.3.10**
* **ESP32 Arduino Core**
* **CameraWebServer**
* **UART / Serial communication**

---

## 👁️ Drowsiness Detection

The planned eye-monitoring pipeline uses facial landmarks and **Eye Aspect Ratio (EAR)** to distinguish normal blinking from prolonged eye closure.

```text
Camera
  ↓
Face Detection
  ↓
Eye Landmarks
  ↓
EAR
  ↓
Temporal Analysis
  ↓
Drowsiness Alert
```

---

## 🔗 Sensor Fusion

Camera-based eye monitoring can be combined with motion data to improve detection reliability.

```text
Eye State ──────┐
                ↓
          Sensor Fusion
                ↑
Motion Data ────┘
                ↓
        🚨 Safety Alert
```

---

## 🛣️ Future Scope

* Real-time eye tracking
* EAR/PERCLOS-based drowsiness detection
* IMU-based swerving detection
* Sensor fusion
* Buzzer + vibration integration
* Distracted-driver detection
* OBD-II / CAN integration
* Compact PCB and enclosure

---

## 🔒 Offline by Design

SafeDrive Edge is designed to process safety-related data **locally**, reducing dependence on cloud services and internet connectivity while keeping camera data on-device.

---

## ⚠️ Disclaimer

SafeDrive Edge is currently a **hackathon/research prototype** and is not a certified automotive safety system.

---

### 🚗 SafeDrive Edge

**Eyes on the road. Sleep mode off.**

> *Because "I'm fine bro" is not a safety system.* 💀
