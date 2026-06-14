"""LoRa + HTTP telemetry client for TrackGuard robot"""
import requests, json, time

class TelemetryClient:
    def __init__(self, server_url="http://dashboard.trackguard.ai"):
        self.url = server_url
        self.robot_id = "ROBOT_001"

    def report_fault(self, fault_type, confidence, km_marker, lat=0.0, lon=0.0):
        payload = {"robot_id": self.robot_id, "fault_type": fault_type,
                   "confidence": confidence, "km_marker": km_marker,
                   "latitude": lat, "longitude": lon}
        try:
            r = requests.post(f"{self.url}/api/fault", json=payload, timeout=5)
            return r.json()
        except Exception as e:
            print(f"[Telemetry] Failed to report: {e}")
            return None

    def heartbeat(self, km_marker, faults_found):
        payload = {"robot_id": self.robot_id, "km_marker": km_marker,
                   "faults_found": faults_found, "ts": time.time()}
        try:
            requests.post(f"{self.url}/api/robot/heartbeat", json=payload, timeout=3)
        except: pass
