# TrackGuard-Railway-safety
TrackGuard AI is an advanced, end-to-end autonomous hardware and software ecosystem designed to modernize railway track inspection, safety monitoring, and station management. By replacing manual, high-risk track auditing with high-frequency edge computing and multi-angle 3D spatial scanning, the system minimizes human error, 
# 🚂 TrackGuard AI — Autonomous Railway Safety System
### FAR AWAY 2026 | Railways Theme

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev)
[![Arduino](https://img.shields.io/badge/Arduino-ESP32%2FSTM32-teal.svg)](https://arduino.cc)

> **A 3-layer autonomous railway safety ecosystem combining a citizen reporting app, an AI-powered inspection robot with LiDAR, and a smart pressure-sensor network — all monitored through a real-time cloud dashboard.**

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         TrackGuard AI                               │
│                                                                     │
│  LAYER 1: Citizen App          LAYER 2: Inspection Robot            │
│  ┌──────────────────┐         ┌──────────────────────────────────┐  │
│  │ React PWA        │         │ Raspberry Pi 4 + Arduino Mega    │  │
│  │ Hazard Reporting │─────────│ RPLiDAR A2M8 + OV5647 Cameras   │  │
│  │ Station Map      │         │ Caterpillar Track Drive          │  │
│  │ Amenity Status   │         │ YOLOv8 Fault Detection AI        │  │
│  └──────────────────┘         └──────────────────────────────────┘  │
│            │                                    │                   │
│            ▼                                    ▼                   │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │               FastAPI Edge AI Server                         │   │
│  │               PostgreSQL + PostGIS Database                  │   │
│  │               AWS Cloud Dashboard                            │   │
│  └──────────────────────────────────────────────────────────────┘   │
│            │                                                        │
│  LAYER 3: Sensor Network                                           │
│  ┌──────────────────┐                                             │
│  │ STM32 + Piezo    │ ← Pressure/vibration every 500m            │
│  │ LoRa SX1278      │ ← Emergency stopper trigger                │
│  │ PTZ Cameras      │ ← YOLOv8 trespasser detection             │
│  └──────────────────┘                                             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Repository Structure

```
trackguard-ai/
├── app/                    # React PWA (Citizen App)
│   ├── src/
│   │   ├── components/    # UI components
│   │   ├── pages/         # App pages (Map, Report, Dashboard)
│   │   ├── api/           # API client
│   │   └── App.jsx
│   ├── package.json
│   └── vite.config.js
├── backend/                # FastAPI server
│   ├── main.py
│   ├── models.py
│   ├── routes/
│   ├── ai/                 # YOLOv8 inference
│   ├── requirements.txt
│   └── Dockerfile
├── robot/                  # Raspberry Pi robot firmware
│   ├── main.py
│   ├── lidar_scan.py
│   ├── motor_control.py
│   ├── fault_detector.py
│   └── telemetry.py
├── arduino/                # STM32 sensor node firmware
│   ├── sensor_node/
│   │   └── sensor_node.ino
│   └── emergency_stopper/
│       └── emergency_stopper.ino
├── pcb/                    # KiCad PCB design files
│   ├── sensor_node.kicad_sch
│   ├── sensor_node.kicad_pcb
│   ├── robot_hat.kicad_sch
│   ├── robot_hat.kicad_pcb
│   └── gerbers/
├── cad/                    # Robot chassis 3D files
│   ├── chassis_body.stl
│   ├── lidar_mount.stl
│   └── assembly.step
├── docs/
│   ├── circuit_diagram.png
│   ├── BOM.csv
│   ├── ARCHITECTURE.md
│   └── SETUP.md
└── demo/
    ├── screenshots/
    └── VIDEO_LINK.txt
```

---

## ⚡ Quick Start

### Prerequisites
- Python 3.10+, Node.js 18+
- Arduino IDE with STM32 & RPLiDAR libraries
- PostgreSQL 14+, Redis

### 1. Clone & Setup Backend
```bash
git clone https://github.com/[yourname]/trackguard-ai.git
cd trackguard-ai/backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # Edit with your DB credentials
uvicorn main:app --reload --port 8000
```

### 2. Setup Citizen App
```bash
cd ../app
npm install
npm run dev   # Opens at http://localhost:5173
```

### 3. Flash Robot Firmware
```bash
cd ../robot
# Copy to Raspberry Pi via SSH
scp -r . pi@<robot-ip>:/home/pi/trackguard/
ssh pi@<robot-ip> "cd /home/pi/trackguard && python main.py"
```

### 4. Flash Arduino Sensor Node
- Open `arduino/sensor_node/sensor_node.ino` in Arduino IDE
- Select board: **STM32F103C8T6 (Blue Pill)**
- Upload via USB-TTL adapter

---

## 🤖 Robot Hardware Setup

| Component            | Model              | Connection         |
|----------------------|--------------------|--------------------|
| Main computer        | Raspberry Pi 4B    | —                  |
| Motor controller     | Arduino Mega 2560  | USB Serial         |
| LiDAR scanner        | RPLiDAR A2M8       | USB /dev/ttyUSB0   |
| Camera (front)       | Pi Camera V2       | CSI ribbon         |
| LoRa radio           | SX1278 module      | SPI (GPIO 10-11-9) |
| Motor driver         | L298N ×2           | GPIO PWM           |
| Battery              | 4S 5000mAh LiPo    | XT60 connector     |

**Pin Map (Arduino Mega → L298N):**
```
Pin 2 → IN1   Pin 3 → IN2   (Left motor)
Pin 4 → IN3   Pin 5 → IN4   (Right motor)
Pin 6 → ENA   Pin 7 → ENB   (PWM speed)
```

---

## 🔌 Sensor Node Wiring (STM32)

```
STM32F103C8T6 (Blue Pill)
├── PA0  → Piezo sensor signal (via ADS1115 A0)
├── PA1  → Secondary piezo (ADS1115 A1)
├── PB6  → SDA (ADS1115 I²C)
├── PB7  → SCL (ADS1115 I²C)
├── PA4  → SX1278 NSS (SPI CS)
├── PA5  → SX1278 SCK
├── PA6  → SX1278 MISO
├── PA7  → SX1278 MOSI
├── PB0  → Emergency relay control (via IRF540N gate)
└── 3.3V/GND → AMS1117 regulator output
```

---

## 📡 API Endpoints (FastAPI)

| Method | Endpoint                  | Description                     |
|--------|---------------------------|---------------------------------|
| GET    | `/api/stations`           | List all stations with amenities|
| POST   | `/api/report`             | Submit hazard report + image    |
| GET    | `/api/faults`             | Get LiDAR-detected track faults |
| GET    | `/api/alerts`             | Active emergency alerts         |
| POST   | `/api/sensor/reading`     | Sensor node data ingestion      |
| GET    | `/api/dashboard/stats`    | Maintenance dashboard stats     |
| WS     | `/ws/live`                | WebSocket for real-time alerts  |

---

## 🏆 FAR AWAY 2026 Submission Checklist

- [x] GitHub repository with source code
- [x] Setup instructions (this README)
- [x] 15-slide presentation (see `/demo/`)
- [x] PCB design files — KiCad schematics + Gerbers
- [x] CAD files — Robot chassis STL
- [x] Bill of Materials (BOM.csv)
- [x] Circuit diagram
- [x] Demo video link
- [x] Working prototype

---

## 👥 Team

| Name | Role | Contact |
|------|------|---------|
| rudraksha| Hardware + Firmware | pp6489845@gmial.com |
| bhavika | AI + Backend |  |

---

## 📜 License
MIT License — see [LICENSE](LICENSE)
