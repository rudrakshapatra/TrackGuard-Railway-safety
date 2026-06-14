import asyncio
import json
import logging
import time
from typing import List, Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Initialize FastAPI App
app = FastAPI(
    title="TrackGuard AI - Central Control & Analytics API",
    version="1.0.0",
    description="Backend engine for processing autonomous track diagnostics, station amenities, and crowdsourced AI fault tracking."
)

# Enable CORS for frontend cross-origin access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup logging Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Global In-Memory Database (Mocking Production Persistence Layer)
active_connections: List[WebSocket] = []
fault_reports: List[Dict[str, Any]] = []
robot_telemetry_history: List[Dict[str, Any]] = []

# Mock Station Static Data (Maps, Water Supply, Safety Rest Zones)
STATION_AMENITIES = {
    "NDLS_01": {
        "station_name": "New Delhi Railway Station",
        "freshwater_hubs": [{"id": "W1", "platform": 1, "status": "Optimal", "capacity": "94%"}, {"id": "W2", "platform": 3, "status": "Optimal", "capacity": "82%"}],
        "ticket_counters": [{"id": "TC1", "zone": "North Booking", "queues": "Low"}, {"id": "TC2", "zone": "South Gate", "queues": "Moderate"}],
        "safety_rest_zones": [{"id": "SR1", "platform": 2, "facilities": ["Medical Kit", "Beds", "AC"], "available_spaces": 14}]
    },
    "LJN_02": {
        "station_name": "Lucknow Junction",
        "freshwater_hubs": [{"id": "W1", "platform": 2, "status": "Maintenance Needed", "capacity": "12%"}],
        "ticket_counters": [{"id": "TC1", "zone": "Main Concourse", "queues": "High"}],
        "safety_rest_zones": [{"id": "SR1", "platform": 1, "facilities": ["Basic Medical", "Seating"], "available_spaces": 5}]
    }
}

# --- Pydantic Data Validation Schemas ---
class AIReportPayload(BaseModel):
    station_id: str
    reporter_type: str  # "Passenger" or "Staff"
    raw_text: str       # Input parsed by downstream NLP engine
    image_attached: bool
    detected_issue_category: str  # e.g., "Track Fracture", "Water Leakage"

class TelemetryPayload(BaseModel):
    device_id: str
    latitude: float
    longitude: float
    current_kilometer_marker: float
    lidar_scan_mode: str  # "LINEAR_0" or "CONICAL_30"
    point_cloud_density: int
    structural_fault_detected: bool
    vibration_g_force: float

# --- Real-Time Connection Manager ---
class ConnectionManager:
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        active_connections.append(websocket)
        logging.info(f"New client socket registered. Total connections: {len(active_connections)}")

    def disconnect(self, websocket: WebSocket):
        active_connections.remove(websocket)
        logging.info(f"Socket dropped. Total active connections: {len(active_connections)}")

    async def broadcast(self, message: dict):
        for connection in active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                pass # Stale connection cleanup handled safely on disconnect loop

manager = ConnectionManager()

# --- REST API Endpoints ---
@app.get("/")
def read_root():
    return {"status": "ONLINE", "system": "TrackGuard AI Command Core", "timestamp": time.time()}

@app.get("/api/v1/stations/{station_id}")
def get_station_map(station_id: str):
    """Fetches real-time mapped infrastructure data, freshwater utilities, and structural layers."""
    if station_id not in STATION_AMENITIES:
        raise HTTPException(status_code=404, detail="Station data parameters not found.")
    return STATION_AMENITIES[station_id]

@app.post("/api/v1/reports/submit")
async def submit_ai_report(payload: AIReportPayload, background_tasks: BackgroundTasks):
    """Processes pipeline crowdsourced passenger reports analyzed via automated AI vision parsing hacks."""
    report_id = len(fault_reports) + 1
    processed_report = {
        "report_id": report_id,
        "timestamp": time.time(),
        "status": "Verified" if payload.image_attached else "Pending Review",
        **payload.dict()
    }
    fault_reports.append(processed_report)
    
    # Trigger real-time visual alert on control dashboard if critical fault detected
    background_tasks.add_task(
        manager.broadcast, 
        {"event": "NEW_USER_REPORT", "data": processed_report}
    )
    return {"status": "SUCCESS", "report_id": report_id, "ai_routing_queue": "HIGH_PRIORITY"}

@app.post("/api/v1/telemetry/update")
async def accept_robot_telemetry(payload: TelemetryPayload):
    """Receives autonomous high-frequency operations telemetry from Jetson Nano Edge Hardware Node."""
    telemetry_data = {**payload.dict(), "received_at": time.time()}
    robot_telemetry_history.append(telemetry_data)
    
    # Broadcast telemetry stream directly to UI Client interfaces
    await manager.broadcast({"event": "ROBOT_TELEMETRY_STREAM", "data": telemetry_data})
    
    if payload.structural_fault_detected:
        await manager.broadcast({
            "event": "CRITICAL_TRACK_EMERGENCY",
            "msg": f"CRITICAL TRACK DAMAGE DETECTED AT KM: {payload.current_kilometer_marker}!! TRIGGERING EMERGENCY BRAKING SYSTEMS.",
            "coordinates": [payload.latitude, payload.longitude]
        })
    return {"status": "ACCEPTED", "broadcast_complete": True}

# --- WebSocket Infrastructure Gateway ---
@app.websocket("/ws/live-stream")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Simple heartbeat ping/pong loop to hold pipes secure
            data = await websocket.receive_text()
            await websocket.send_text(json.dumps({"heartbeat": "ACK", "server_time": time.time()}))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
