// ============================================================
// TrackGuard AI — ESP32 Co-processor Firmware
// Role: Low-level I/O controller for the caterpillar robot
//   - CAN Bus communication (MCP2515 / TJA1050 via SPI)
//   - BNO055 9-axis IMU (I2C) for vibration/tilt detection
//   - NEMA17 LiDAR pivot stepper (DRV8825 STEP/DIR)
//   - Dual BTS7960 H-bridge drivers for caterpillar tracks
// The Jetson Nano connects to this ESP32 via serial (USB)
// and issues drive/scan commands; this MCU replies with IMU
// telemetry and CAN status frames.
// ============================================================

#include <Arduino.h>
#include <SPI.h>
#include <mcp2515.h>          // autowp/arduino-mcp2515
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <AccelStepper.h>

// ──────────────────────────────────────────────
// Pin Definitions
// ──────────────────────────────────────────────
#define MCP_CS_PIN    13
#define MCP_INT_PIN   4

#define STEP_PIN      26
#define DIR_PIN       27

// Left track (BTS7960)
#define LEFT_RPWM     32
#define LEFT_LPWM     33
#define LEFT_R_EN     25
#define LEFT_L_EN     16

// Right track (BTS7960)
#define RIGHT_RPWM    14
#define RIGHT_LPWM    5
#define RIGHT_R_EN    17
#define RIGHT_L_EN    15

// PWM channels (ESP32 LEDC)
#define PWM_FREQ      20000   // 20 kHz — above audible range
#define PWM_RES       8       // 8-bit: 0-255

#define CH_LEFT_FWD   0
#define CH_LEFT_REV   1
#define CH_RIGHT_FWD  2
#define CH_RIGHT_REV  3

// ──────────────────────────────────────────────
// Peripheral Objects
// ──────────────────────────────────────────────

// Forward declarations
void IRAM_ATTR onCANInterrupt();
void setupPWM();
void setLeftTrack(int speed);
void setRightTrack(int speed);
void stopAllMotors();
void sendCANAlert(uint32_t alertCode);
void sendCANTelemetry(float accelMag, float rollDeg, float pitchDeg);
void parseCommand(String cmd);

MCP2515 mcp2515(MCP_CS_PIN);

Adafruit_BNO055 bno = Adafruit_BNO055(55, 0x28);

// AccelStepper in DRIVER mode (STEP + DIR)
AccelStepper stepper(AccelStepper::DRIVER, STEP_PIN, DIR_PIN);

// ──────────────────────────────────────────────
// Thresholds
// ──────────────────────────────────────────────
#define VIBRATION_G_THRESHOLD  2.5f   // m/s² above which alert is triggered
#define TILT_DEG_THRESHOLD     20.0f  // degrees; stop motors if tilted too far
#define CAN_SPEED              CAN_500KBPS
#define CAN_CLOCK_FREQ         MCP_8MHZ

// Stepper parameters
#define LIDAR_MAX_SPEED        800.0f  // steps/sec
#define LIDAR_ACCELERATION     400.0f  // steps/sec²
#define LIDAR_CONICAL_STEPS    1667    // ~30° at 200 steps/rev with 1/8 microstepping

// ──────────────────────────────────────────────
// Global State
// ──────────────────────────────────────────────
bool motorEnabled = true;
bool alertActive  = false;

volatile bool canInterrupt = false;

void IRAM_ATTR onCANInterrupt() {
  canInterrupt = true;
}

// ──────────────────────────────────────────────
// Motor helpers
// ──────────────────────────────────────────────
void setupPWM() {
  ledcSetup(CH_LEFT_FWD,  PWM_FREQ, PWM_RES);
  ledcSetup(CH_LEFT_REV,  PWM_FREQ, PWM_RES);
  ledcSetup(CH_RIGHT_FWD, PWM_FREQ, PWM_RES);
  ledcSetup(CH_RIGHT_REV, PWM_FREQ, PWM_RES);

  ledcAttachPin(LEFT_RPWM,  CH_LEFT_FWD);
  ledcAttachPin(LEFT_LPWM,  CH_LEFT_REV);
  ledcAttachPin(RIGHT_RPWM, CH_RIGHT_FWD);
  ledcAttachPin(RIGHT_LPWM, CH_RIGHT_REV);

  // Enable both bridges
  pinMode(LEFT_R_EN,  OUTPUT); digitalWrite(LEFT_R_EN,  HIGH);
  pinMode(LEFT_L_EN,  OUTPUT); digitalWrite(LEFT_L_EN,  HIGH);
  pinMode(RIGHT_R_EN, OUTPUT); digitalWrite(RIGHT_R_EN, HIGH);
  pinMode(RIGHT_L_EN, OUTPUT); digitalWrite(RIGHT_L_EN, HIGH);
}

// speed: -255 (full reverse) to +255 (full forward)
void setLeftTrack(int speed) {
  if (!motorEnabled) { ledcWrite(CH_LEFT_FWD, 0); ledcWrite(CH_LEFT_REV, 0); return; }
  speed = constrain(speed, -255, 255);
  if (speed >= 0) { ledcWrite(CH_LEFT_FWD, speed); ledcWrite(CH_LEFT_REV, 0);     }
  else            { ledcWrite(CH_LEFT_FWD, 0);     ledcWrite(CH_LEFT_REV, -speed); }
}

void setRightTrack(int speed) {
  if (!motorEnabled) { ledcWrite(CH_RIGHT_FWD, 0); ledcWrite(CH_RIGHT_REV, 0); return; }
  speed = constrain(speed, -255, 255);
  if (speed >= 0) { ledcWrite(CH_RIGHT_FWD, speed); ledcWrite(CH_RIGHT_REV, 0);     }
  else            { ledcWrite(CH_RIGHT_FWD, 0);     ledcWrite(CH_RIGHT_REV, -speed); }
}

void stopAllMotors() {
  ledcWrite(CH_LEFT_FWD,  0); ledcWrite(CH_LEFT_REV,  0);
  ledcWrite(CH_RIGHT_FWD, 0); ledcWrite(CH_RIGHT_REV, 0);
}

// ──────────────────────────────────────────────
// CAN helpers
// ──────────────────────────────────────────────
void sendCANAlert(uint32_t alertCode) {
  struct can_frame frame;
  frame.can_id  = 0x7FF;  // Broadcast emergency frame ID
  frame.can_dlc = 4;
  frame.data[0] = (alertCode >> 24) & 0xFF;
  frame.data[1] = (alertCode >> 16) & 0xFF;
  frame.data[2] = (alertCode >>  8) & 0xFF;
  frame.data[3] = (alertCode)       & 0xFF;
  mcp2515.sendMessage(&frame);
}

void sendCANTelemetry(float accelMag, float rollDeg, float pitchDeg) {
  struct can_frame frame;
  frame.can_id  = 0x100;  // Telemetry frame
  frame.can_dlc = 6;
  // Pack as fixed-point: scale by 100, clamp to int16
  int16_t accel16 = (int16_t)(accelMag * 100.0f);
  int16_t roll16  = (int16_t)(rollDeg  * 100.0f);
  int16_t pitch16 = (int16_t)(pitchDeg * 100.0f);
  frame.data[0] = (accel16 >> 8) & 0xFF;
  frame.data[1] = accel16 & 0xFF;
  frame.data[2] = (roll16 >> 8) & 0xFF;
  frame.data[3] = roll16 & 0xFF;
  frame.data[4] = (pitch16 >> 8) & 0xFF;
  frame.data[5] = pitch16 & 0xFF;
  mcp2515.sendMessage(&frame);
}

// ──────────────────────────────────────────────
// Serial command parser (from Jetson Nano)
// Protocol: "CMD <arg>\n"
//   DRIVE <leftSpeed> <rightSpeed>  e.g. "DRIVE 200 200"
//   STOP
//   LIDAR_SWEEP                     move to conical position
//   LIDAR_HOME                      return to 0° (home)
//   STATUS
// ──────────────────────────────────────────────
void parseCommand(String cmd) {
  cmd.trim();
  if (cmd.startsWith("DRIVE")) {
    int s1 = 0, s2 = 0;
    sscanf(cmd.c_str(), "DRIVE %d %d", &s1, &s2);
    setLeftTrack(s1);
    setRightTrack(s2);
    Serial.println("OK DRIVE");
  } else if (cmd == "STOP") {
    stopAllMotors();
    Serial.println("OK STOP");
  } else if (cmd == "LIDAR_SWEEP") {
    stepper.moveTo(LIDAR_CONICAL_STEPS);
    Serial.println("OK LIDAR_SWEEP");
  } else if (cmd == "LIDAR_HOME") {
    stepper.moveTo(0);
    Serial.println("OK LIDAR_HOME");
  } else if (cmd == "STATUS") {
    Serial.printf("ALERT:%d MOTORS:%d LIDAR_POS:%ld\n",
                  (int)alertActive, (int)motorEnabled, stepper.currentPosition());
  }
}

// ──────────────────────────────────────────────
// setup()
// ──────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  Serial.println("[TrackGuard AI] ESP32 co-processor boot");

  // I2C — BNO055
  Wire.begin(21, 22);  // SDA=21, SCL=22
  if (!bno.begin()) {
    Serial.println("[ERROR] BNO055 not found — check wiring!");
  } else {
    bno.setExtCrystalUse(true);
    Serial.println("[OK] BNO055 online");
  }

  // SPI — MCP2515
  SPI.begin(18, 19, 23, MCP_CS_PIN);  // SCK=18, MISO=19, MOSI=23, CS=13
  mcp2515.reset();
  if (mcp2515.setBitrate(CAN_SPEED, CAN_CLOCK_FREQ) == MCP2515::ERROR_OK) {
    mcp2515.setNormalMode();
    Serial.println("[OK] MCP2515 CAN bus online at 500 kbps");
  } else {
    Serial.println("[ERROR] MCP2515 init failed");
  }

  pinMode(MCP_INT_PIN, INPUT);
  attachInterrupt(digitalPinToInterrupt(MCP_INT_PIN), onCANInterrupt, FALLING);

  // PWM / Motor drivers
  setupPWM();
  Serial.println("[OK] Motor drivers armed");

  // Stepper (LiDAR pivot)
  stepper.setMaxSpeed(LIDAR_MAX_SPEED);
  stepper.setAcceleration(LIDAR_ACCELERATION);
  stepper.setCurrentPosition(0);
  Serial.println("[OK] LiDAR pivot stepper ready");

  Serial.println("[TrackGuard AI] Ready — awaiting Jetson Nano commands");
}

// ──────────────────────────────────────────────
// loop()
// ──────────────────────────────────────────────
static uint32_t lastImuMs = 0;
static String   serialBuf = "";

void loop() {
  // ── 1. Run stepper (non-blocking)
  stepper.run();

  // ── 2. Serial command intake (Jetson Nano → ESP32)
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      if (serialBuf.length() > 0) parseCommand(serialBuf);
      serialBuf = "";
    } else {
      serialBuf += c;
    }
  }

  // ── 3. IMU telemetry (every 100 ms)
  if (millis() - lastImuMs >= 100) {
    lastImuMs = millis();

    sensors_event_t accelEvent;
    bno.getEvent(&accelEvent, Adafruit_BNO055::VECTOR_ACCELEROMETER);

    imu::Quaternion quat = bno.getQuat();
    imu::Vector<3> euler = quat.toEuler();  // radians

    float ax = accelEvent.acceleration.x;
    float ay = accelEvent.acceleration.y;
    float az = accelEvent.acceleration.z;
    float accelMag = sqrt(ax*ax + ay*ay + az*az) - 9.81f;  // subtract gravity baseline
    if (accelMag < 0.0f) accelMag = 0.0f;

    float rollDeg  = euler.z() * 180.0f / PI;
    float pitchDeg = euler.y() * 180.0f / PI;

    // Send telemetry frame over CAN
    sendCANTelemetry(accelMag, rollDeg, pitchDeg);

    // Forward IMU data to Jetson Nano via Serial
    Serial.printf("IMU ax=%.2f ay=%.2f az=%.2f mag=%.2f roll=%.1f pitch=%.1f\n",
                  ax, ay, az, accelMag, rollDeg, pitchDeg);

    // ── 4. Emergency stop logic
    bool vibrationAlert = (accelMag > VIBRATION_G_THRESHOLD);
    bool tiltAlert      = (fabs(rollDeg) > TILT_DEG_THRESHOLD ||
                           fabs(pitchDeg) > TILT_DEG_THRESHOLD);

    if ((vibrationAlert || tiltAlert) && !alertActive) {
      alertActive    = true;
      motorEnabled   = false;
      stopAllMotors();
      uint32_t code = vibrationAlert ? 0xDEAD0001 : 0xDEAD0002;
      sendCANAlert(code);
      Serial.printf("[ALERT] Emergency stop triggered! vib=%d tilt=%d\n",
                    (int)vibrationAlert, (int)tiltAlert);
    }

    // Auto-clear alert if conditions resolve
    if (alertActive && !vibrationAlert && !tiltAlert) {
      alertActive  = false;
      motorEnabled = true;
      Serial.println("[ALERT] Conditions cleared — motors re-enabled");
    }
  }

  // ── 5. Handle incoming CAN frames (if interrupt fired)
  if (canInterrupt) {
    canInterrupt = false;
    struct can_frame frame;
    while (mcp2515.readMessage(&frame) == MCP2515::ERROR_OK) {
      // Forward raw CAN frame to Jetson Nano for logging/decoding
      Serial.printf("CAN id=0x%03X dlc=%d data=", frame.can_id, frame.can_dlc);
      for (int i = 0; i < frame.can_dlc; i++) {
        Serial.printf("%02X ", frame.data[i]);
      }
      Serial.println();
    }
  }
}