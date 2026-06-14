/*
 * TrackGuard AI — STM32 Sensor Node Firmware
 * FAR AWAY 2026 | Railways Theme
 * 
 * Hardware: STM32F103C8T6 (Blue Pill)
 * Sensors: Piezoelectric vibration (via ADS1115 ADC)
 * Radio:   SX1278 LoRa 433MHz
 * Purpose: Detect track vibration anomalies, trigger emergency stopper
 * 
 * Wiring:
 *   ADS1115 SDA → PB6   ADS1115 SCL → PB7
 *   SX1278 NSS  → PA4   SX1278 SCK  → PA5
 *   SX1278 MISO → PA6   SX1278 MOSI → PA7
 *   SX1278 RST  → PB0   SX1278 DIO0 → PB1
 *   Emergency Relay → PC13 (via IRF540N gate + 10kΩ pull-down)
 */

#include <Wire.h>
#include <Adafruit_ADS1X15.h>
#include <LoRa.h>
#include <ArduinoJson.h>

// ── Pin Definitions ──────────────────────────────────────────────────────────
#define LORA_NSS    PA4
#define LORA_RST    PB0
#define LORA_DIO0   PB1
#define RELAY_PIN   PC13
#define LED_PIN     PC14

// ── Configuration ────────────────────────────────────────────────────────────
#define NODE_ID         "SENSOR_NODE_01"
#define LORA_FREQUENCY  433E6
#define VIBRATION_THRESHOLD_MV  450    // mV — tune per installation
#define SAMPLE_INTERVAL_MS      100    // 10Hz sampling
#define REPORT_INTERVAL_MS      5000   // Send LoRa packet every 5s (or on alert)

Adafruit_ADS1115 ads;

float peakVibration = 0.0;
unsigned long lastReport = 0;
bool emergencyActive = false;

// ── Setup ─────────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  pinMode(RELAY_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);   // Relay OFF (safe default)
  
  // ADS1115 init (16-bit ADC, ±4.096V range)
  Wire.begin(PB6, PB7);
  ads.begin();
  ads.setGain(GAIN_ONE);          // ±4.096V range, 0.125mV/bit
  
  // LoRa init
  LoRa.setPins(LORA_NSS, LORA_RST, LORA_DIO0);
  if (!LoRa.begin(LORA_FREQUENCY)) {
    Serial.println("LoRa init FAILED");
    while (true);
  }
  LoRa.setSpreadingFactor(10);    // SF10 for ~5km range
  LoRa.setSignalBandwidth(125E3);
  LoRa.setCodingRate4(5);
  Serial.println("TrackGuard Sensor Node ready");
}

// ── Loop ──────────────────────────────────────────────────────────────────────
void loop() {
  // 1. Read piezo vibration from ADS1115 channel 0
  int16_t raw = ads.readADC_SingleEnded(0);
  float voltage_mv = raw * 0.125;   // 0.125mV/bit at GAIN_ONE
  
  // Track peak in this window
  if (voltage_mv > peakVibration) peakVibration = voltage_mv;
  
  // 2. Check threshold — emergency if exceeded
  if (voltage_mv > VIBRATION_THRESHOLD_MV && !emergencyActive) {
    emergencyActive = true;
    digitalWrite(RELAY_PIN, HIGH);  // Engage emergency stopper
    digitalWrite(LED_PIN, HIGH);
    Serial.println("EMERGENCY: Vibration threshold exceeded!");
    sendLoRaAlert(voltage_mv);      // Immediate alert
  }
  
  // 3. Reset emergency after 30s of normal readings
  if (emergencyActive && voltage_mv < VIBRATION_THRESHOLD_MV * 0.7) {
    static unsigned long clearStart = 0;
    if (clearStart == 0) clearStart = millis();
    if (millis() - clearStart > 30000) {
      emergencyActive = false;
      digitalWrite(RELAY_PIN, LOW);
      digitalWrite(LED_PIN, LOW);
      clearStart = 0;
      Serial.println("Emergency cleared");
    }
  }
  
  // 4. Periodic telemetry packet
  if (millis() - lastReport > REPORT_INTERVAL_MS) {
    sendLoRaReport(peakVibration);
    peakVibration = 0.0;
    lastReport = millis();
  }
  
  delay(SAMPLE_INTERVAL_MS);
}

// ── LoRa Functions ────────────────────────────────────────────────────────────
void sendLoRaReport(float peak_mv) {
  StaticJsonDocument<128> doc;
  doc["id"]    = NODE_ID;
  doc["type"]  = "report";
  doc["mv"]    = round(peak_mv);
  doc["alert"] = emergencyActive;
  doc["ts"]    = millis() / 1000;

  String payload;
  serializeJson(doc, payload);
  
  LoRa.beginPacket();
  LoRa.print(payload);
  LoRa.endPacket();
  Serial.println("LoRa TX: " + payload);
}

void sendLoRaAlert(float voltage_mv) {
  StaticJsonDocument<128> doc;
  doc["id"]    = NODE_ID;
  doc["type"]  = "EMERGENCY";
  doc["mv"]    = round(voltage_mv);
  doc["alert"] = true;

  String payload;
  serializeJson(doc, payload);
  
  // Send 3 times for reliability
  for (int i = 0; i < 3; i++) {
    LoRa.beginPacket();
    LoRa.print(payload);
    LoRa.endPacket();
    delay(200);
  }
}
