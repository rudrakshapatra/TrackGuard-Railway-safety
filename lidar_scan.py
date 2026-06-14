"""RPLiDAR A2M8 interface — 2D scan + 3D point cloud fusion"""
import math, threading
try:
    from rplidar import RPLidar
except ImportError:
    RPLidar = None  # Simulation mode

class LidarScanner:
    def __init__(self, port="/dev/ttyUSB0"):
        self.port = port
        self._scan = []
        self._lock = threading.Lock()
        self._running = False
        if RPLidar:
            self.lidar = RPLidar(port, baudrate=115200)
        else:
            import random; self._sim = True; self.random = random

    def start(self):
        self._running = True
        t = threading.Thread(target=self._scan_loop, daemon=True)
        t.start()

    def _scan_loop(self):
        if not RPLidar:
            # Simulation mode — generate synthetic track profile
            import time, random
            while self._running:
                scan = [(a, 1500 + random.gauss(0, 20)) for a in range(0, 360, 1)]
                # Inject synthetic fault every 30 seconds
                if int(time.time()) % 30 == 0:
                    scan[90] = (90, 800)  # Simulated crack gap
                with self._lock: self._scan = scan
                time.sleep(0.1)
        else:
            for scan in self.lidar.iter_scans():
                if not self._running: break
                pts = [(round(m[1], 1), round(m[2], 1)) for m in scan]
                with self._lock: self._scan = pts

    def get_scan(self):
        with self._lock: return list(self._scan)

    def to_3d(self, scan_2d, z_offset=0.0):
        points = []
        for angle_deg, dist_mm in scan_2d:
            rad = math.radians(angle_deg)
            x = dist_mm * math.cos(rad)
            y = dist_mm * math.sin(rad)
            points.append({"x": round(x, 2), "y": round(y, 2), "z": round(z_offset, 2),
                           "dist": dist_mm, "angle": angle_deg})
        return points

    def stop(self):
        self._running = False
        if RPLidar and hasattr(self, "lidar"):
            self.lidar.stop(); self.lidar.disconnect()
