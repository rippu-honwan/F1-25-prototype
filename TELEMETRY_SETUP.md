# F1 25 UDP Telemetry Setup Guide

## Overview

This guide will help you set up UDP telemetry recording from F1 25 game and compare your driving with real F1 drivers.

## Prerequisites

- **F1 25** (PC/Windows)
- **Mac** with Python 3.8+
- **Network connection** between Windows and Mac (same WiFi or Ethernet)

## Step 1: Configure F1 25 UDP Settings

### 1a. Edit the configuration file

On your **Windows machine**, locate the F1 25 settings file:

```
C:\Users\[YourUsername]\Documents\My Games\EA Sports\F1 25\
```

Find and open: `hardware_settings_config.xml`

### 1b. Update UDP settings

Find the line:
```xml
<udp enabled="true" broadcast="false" ip="YOUR_MAC_IP" port="20777" sendRate="10" format="2025" yourTelemetry="public" onlineNames="on"/>
```

**Important settings:**
- `enabled="true"` - Enable UDP output
- `yourTelemetry="public"` - **MUST be "public"** (not "restricted")
- `ip="YOUR_MAC_IP"` - Set to your Mac's IP address
- `port="20777"` - Default port (don't change unless necessary)
- `sendRate="10"` - Packets per second (20 is typical)

### 1c. Find your Mac's IP address

On your **Mac**, open Terminal and run:

```bash
ifconfig | grep "inet "
```

Look for something like `inet 192.168.x.x` (usually on your local network interface)

Example output:
```
inet 192.168.50.9
```

Use this IP in the `hardware_settings_config.xml` file.

## Step 2: Clone the Repository

On your **Mac**, clone this repository:

```bash
git clone https://github.com/rippu-honwan/F1-25-prototype.git
cd F1-25-prototype
```

## Step 3: Run the Telemetry Recorder

### 3a. Execute the recorder

```bash
python3 f1_recorder.py
```

### 3b. Enter track name

```
🎯 F1 25 UDP Telemetry Recorder
==================================================
Enter track name (e.g., monza, silverstone): monza
```

### 3c. Launch F1 25 and record

1. **Start F1 25** on Windows
2. Go to **Time Trial**
3. Select a track (e.g., Monza)
4. **Run 1-3 laps** while telemetry is recording
5. Press **Ctrl+C** on Mac terminal to stop

## Step 4: Output

Your telemetry data will be saved to:

```
telemetry_data/telemetry_monza_20251228_174500.csv
```

### CSV Contents

```csv
timestamp,frame_id,lap_number,packet_type,throttle,brake,steering,speed,gear,rpm,drs,...
2025-12-28T17:45:00.123,100,1,6,75,0,-0.15,245,6,14000,0,...
2025-12-28T17:45:00.125,101,1,0,75,0,-0.14,246,6,14000,0,...
```

## Available Data

The recorder captures:

| Field | Unit | Description |
|-------|------|-------------|
| throttle | % | Throttle input (0-100) |
| brake | % | Brake input (0-100) |
| steering | ratio | Steering angle (-1.0 to 1.0) |
| speed | kph | Current speed |
| gear | ratio | Current gear |
| rpm | rpm | Engine RPM |
| drs | bool | DRS active (0/1) |
| position_x,y,z | m | 3D position on track |

## Troubleshooting

### No data received

**Check UDP settings:**

```bash
lsof -i :20777
```

Should show:
```
Python (listening on port 20777)
```

**Check firewall:**

On Mac:
```bash
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
```

Should return: `Firewall is off` or allow UDP on port 20777

### Wrong IP address

If you get no packets, verify:
1. Mac IP in F1 25 config matches actual IP
2. Windows and Mac are on same network
3. Windows firewall allows UDP on port 20777

### File not saving

Check directory permissions:
```bash
ls -la telemetry_data/
```

## Next Steps

Once you have telemetry data:

1. **Analyze your data:**
   ```bash
   python3 analyze_telemetry.py
   ```

2. **Compare with F1 drivers (using FastF1):**
   ```bash
   python3 compare_with_f1.py
   ```

## FAQs

**Q: Why is `yourTelemetry="public"`?**
A: F1 25 restricts telemetry when set to "restricted". Public mode enables all UDP packet types.

**Q: Can I use this over internet?**
A: Possible but not recommended. UDP is designed for local networks. Use VPN if necessary.

**Q: What's the maximum recording time?**
A: Limited only by disk space. CSV grows ~5MB per 10 minutes of recording.

**Q: Can I record from multiple F1 25 instances?**
A: No, each instance needs a different port. Contact us for multi-car support.

## Support

Have issues? Check:
- F1 25 UDP Specification: https://forums.ea.com/discussions/f1-25-general-discussion-en/
- FastF1 Documentation: https://docs.fastf1.dev/

---

**Happy racing! 🏎️💨**
