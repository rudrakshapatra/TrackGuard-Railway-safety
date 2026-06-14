# PCB Design Notes — TrackGuard AI

## Tool: KiCad 6 (Free & Open Source)
Download: https://www.kicad.org/

## PCB 1 — Sensor Node Board (STM32)

### Schematic Summary
- **U1**: STM32F103C8T6 (Blue Pill footprint)
- **U2**: ADS1115 I²C 16-bit ADC (SSOP-10)
- **U3**: AMS1117-3.3 LDO regulator (SOT-223)
- **U4**: SX1278 LoRa module (castellated holes)
- **Q1**: IRF540N N-MOSFET for relay drive (TO-220)
- **J1**: Piezo sensor input (2-pin screw terminal)
- **J2**: Power input 5V (2-pin XT30)
- **J3**: Emergency relay output (2-pin screw terminal)
- **C1-C4**: 100nF decoupling caps (0402)
- **R1**: 10kΩ MOSFET gate pull-down (0402)
- **R2**: 10kΩ I²C pull-up SDA (0402)
- **R3**: 10kΩ I²C pull-up SCL (0402)

### PCB Specs (order from JLCPCB)
- Layers: 2
- Size: 80mm × 60mm
- Thickness: 1.6mm
- Copper weight: 1oz
- Surface finish: HASL
- Color: Green

### KiCad → Gerber Export Steps
1. Open KiCad PCB Editor
2. File → Fabrication Outputs → Gerbers
3. Select all layers (F.Cu, B.Cu, F.SilkS, B.SilkS, F.Mask, B.Mask, Edge.Cuts)
4. Generate Drill Files → Excellon format
5. Zip all files → Upload to JLCPCB

## PCB 2 — Robot Controller Hat (Raspberry Pi)
- **U1**: Raspberry Pi 40-pin header passthrough
- **U2**: Arduino Mega UART interface (TX/RX level shifter)
- **U3**: SX1278 LoRa module
- **U4**: Level shifter 5V↔3.3V (TXS0108E)
- **J1-J4**: Motor driver outputs
- **J5**: LiDAR UART (5V via logic shifter)
- Size: 65mm × 56mm (Pi HAT standard)

## Accepted Tools (per FAR AWAY rules)
✅ KiCad 6 — primary tool
✅ EasyEDA — for verification
✅ Altium, Fusion 360, SolidWorks — if available
