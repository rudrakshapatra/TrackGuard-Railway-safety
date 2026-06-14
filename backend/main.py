"""TrackGuard AI FastAPI Backend - FAR AWAY 2026"""
from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import random

app = FastAPI(title="TrackGuard AI API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

reports_db, faults_db, alerts_db, sensor_db = [], [], [], []

class ConnectionManager:
    def __init__(self): self.active = []
    async def connect(self, ws):
        await ws.accept(); self.active.append(ws)
    def disconnect(self, ws): self.active.remove(ws)
    async def broadcast(self, msg):
        for ws in self.active:
            try: await ws.send_json(msg)
            except: pass

manager = ConnectionManager()

class HazardReport(BaseModel):
    station_id: str
    hazard_type: str
    description: str
    latitude: float
    longitude: float
    reporter_id: str = "anonymous"

class SensorReading(BaseModel):
    node_id: str
    vibration_mv: float
    timestamp: str
    gps_lat: float = 0.0
    gps_lon: float = 0.0

class TrackFault(BaseModel):
    robot_id: str
    fault_type: str
    confidence: float
    km_marker: float
    latitude: float
    longitude: float

@app.get("/")
def root():
    return {"status": "TrackGuard AI online", "version": "1.0.0"}

@app.get("/api/stations")
def get_stations():
    return {"stations": [
        {"id": "LDH", "name": "Ludhiana Junction", "lat": 30.901, "lon": 75.857,
         "amenities": {"water": True, "washrooms": 4, "ticket_counters": 8,
                       "waiting_area": True, "food_stalls": 12}},
        {"id": "ASR", "name": "Amritsar Junction", "lat": 31.634, "lon": 74.872,
         "amenities": {"water": True, "washrooms": 6, "ticket_counters": 10,
                       "waiting_area": True, "food_stalls": 20}},
    ]}

@app.post("/api/report")
async def submit_report(report: HazardReport):
    entry = {**report.dict(), "id": len(reports_db)+1,
             "timestamp": datetime.utcnow().isoformat(), "status": "open"}
    reports_db.append(entry)
    await manager.broadcast({"type": "new_report", "data": entry})
    return {"success": True, "report_id": entry["id"]}

@app.post("/api/report/image")
async def submit_image(file: UploadFile = File(...)):
    hazard_classes = ["track_crack", "trespasser", "debris_on_track", "signal_fault", "no_hazard"]
    return {"hazard_type": random.choice(hazard_classes),
            "confidence": round(random.uniform(0.82, 0.97), 2),
            "filename": file.filename}

@app.post("/api/sensor/reading")
async def sensor_reading(reading: SensorReading):
    THRESHOLD_MV = 450.0
    entry = {**reading.dict(), "alert": reading.vibration_mv > THRESHOLD_MV}
    sensor_db.append(entry)
    if entry["alert"]:
        alert = {"type": "EMERGENCY_VIBRATION", "node_id": reading.node_id,
                 "value_mv": reading.vibration_mv, "timestamp": reading.timestamp}
        alerts_db.append(alert)
        await manager.broadcast({"type": "emergency_alert", "data": alert})
    return {"received": True, "alert_triggered": entry["alert"]}

@app.post("/api/fault")
async def robot_fault(fault: TrackFault):
    entry = {**fault.dict(), "id": len(faults_db)+1,
             "timestamp": datetime.utcnow().isoformat(), "status": "unresolved"}
    faults_db.append(entry)
    await manager.broadcast({"type": "track_fault", "data": entry})
    return {"received": True, "fault_id": entry["id"]}

@app.get("/api/faults")
def get_faults():
    return {"faults": faults_db}

@app.get("/api/alerts")
def get_alerts():
    return {"alerts": alerts_db[-20:]}

@app.get("/api/dashboard/stats")
def dashboard_stats():
    return {
        "open_reports": len([r for r in reports_db if r.get("status") == "open"]),
        "track_faults": len(faults_db),
        "active_alerts": len(alerts_db),
        "sensor_nodes_online": 4,
        "robot_status": "patrolling",
        "last_scan_km": 12.4
    }

@app.websocket("/ws/live")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)
