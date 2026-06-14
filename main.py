"""
TrackGuard AI — Raspberry Pi Robot Main Controller
FAR AWAY 2026 | Railways Theme
Autonomous track inspection with LiDAR + Camera + LoRa telemetry
"""
import time, threading, logging
from lidar_scan import LidarScanner
from motor_control import MotorController
from fault_detector import FaultDetector
from telemetry import TelemetryClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("TrackGuardRobot")

SCAN_INTERVAL_SEC  = 0.1    # 10Hz scan rate
PATROL_SPEED       = 60     # PWM 0-255
FAULT_STOP_METERS  = 0.5    # Stop robot if fault within 0.5m

def main():
    log.info("TrackGuard AI Robot starting...")
    
    lidar  = LidarScanner(port="/dev/ttyUSB0")
    motors = MotorController(left_pins=(2,3,6), right_pins=(4,5,7))
    ai     = FaultDetector(model_path="models/trackguard_yolo.pt")
    telem  = TelemetryClient(server_url="http://dashboard.trackguard.ai")
    
    lidar.start()
    motors.set_speed(PATROL_SPEED)
    motors.forward()
    
    km_marker = 0.0
    scan_count = 0
    
    try:
        while True:
            # 1. Grab LiDAR scan
            scan_2d = lidar.get_scan()          # [(angle, distance_mm), ...]
            point_cloud_3d = lidar.to_3d(scan_2d, z_offset=km_marker * 1000)
            
            # 2. Run AI fault detection
            faults = ai.detect(point_cloud_3d)
            
            for fault in faults:
                log.warning(f"FAULT DETECTED: {fault['type']} @ km {km_marker:.3f} confidence={fault['confidence']:.2f}")
                telem.report_fault(fault_type=fault["type"], confidence=fault["confidence"],
                                   km_marker=km_marker, lat=0.0, lon=0.0)
                if fault["distance_m"] < FAULT_STOP_METERS:
                    motors.stop()
                    log.critical("Robot stopped — fault too close!")
                    time.sleep(5)
                    motors.forward()
            
            # 3. Update odometry
            km_marker += (PATROL_SPEED / 255.0) * (SCAN_INTERVAL_SEC / 1000.0)
            scan_count += 1
            
            # 4. Heartbeat telemetry every 50 scans
            if scan_count % 50 == 0:
                telem.heartbeat(km_marker=km_marker, faults_found=len(faults_db_local := []))
            
            time.sleep(SCAN_INTERVAL_SEC)
    
    except KeyboardInterrupt:
        log.info("Shutting down...")
    finally:
        motors.stop()
        lidar.stop()

if __name__ == "__main__":
    main()
