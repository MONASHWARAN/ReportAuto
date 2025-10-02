# ADB GUI Tool - Complete Documentation

## Overview
A single Python Flask script that provides a web-based GUI for Android Debug Bridge (ADB) interactions. Features automatic device detection, intelligent log monitoring with trial-and-error OS detection, and file extraction capabilities.

## Features

### 🔌 Dynamic Port Selection
- Automatically finds available ports on each startup
- Prevents port conflicts
- Shows clear access URLs

### 📱 ADB Device Detection
- Real-time device detection via `adb devices`
- Device status monitoring
- Support for USB-connected devices

### 📊 Intelligent Log Monitoring
- **Trial-and-Error OS Detection**: Automatically tries different logging methods
  1. FOS/Puffin: `adb logcat`
  2. Vega OS: `adb shell journalctl -f`
- Real-time log capture with filtering
- Two-tab display: All Logs vs Filtered Logs
- Live feedback during detection process

### 🎛️ Log Controls
- **Start**: Begin log capture with automatic OS detection
- **Stop**: Terminate log capture
- **Clear**: Clear log display
- **Save**: Save logs to timestamped file
- **Filter**: Real-time grep filtering

### 📁 File Extraction (CHR.db)
Automatically tries multiple paths for each OS:

**Vega OS**:
- `/var/lib/data/alexahybrid/smartHomeSkill/customerHomeRegistry.db`
- `/var/lib/alexahybrid/smartHomeSkill/customerHomeRegistry.db`
- `/data/alexahybrid/smartHomeSkill/customerHomeRegistry.db`

**Puffin OS**:
- `/data/alexahybrid/files/smartHomeSkill/customerHomeRegistry.db`
- `/data/alexahybrid/smartHomeSkill/customerHomeRegistry.db`

**FOS (Fire OS)**:
- `/data/data/com.amazon.alexahybridremoteskill/files/customerHomeRegistry.db`
- `/data/data/com.amazon.alexahybrid/files/customerHomeRegistry.db`

### 🎨 User Interface
- Gold and Black professional theme
- Bootstrap 5 responsive design
- Single-page application
- Real-time status updates
- FontAwesome icons

## Requirements
- Python 3.6+
- Flask
- ADB (Android Debug Bridge) installed and in PATH
- USB debugging enabled on target device

## Installation & Usage

### Quick Start
```bash
# Make script executable
chmod +x adb_gui.py

# Run the tool
python adb_gui.py
```

### Expected Output
```
============================================================
🚀 Starting ADB GUI Tool...
============================================================
✅ Make sure ADB is installed and in your PATH
✅ Connect your device via USB and enable USB Debugging
============================================================
🌐 Access the GUI at: http://localhost:47217
🌐 Or from network:   http://0.0.0.0:47217
============================================================
🔌 Dynamic Port: 47217 (Auto-selected)
📱 Supported Devices: Vega OS, Puffin OS, FOS
🛠️  Press Ctrl+C to stop the server
============================================================
📋 Features Available:
   • Real-time device detection
   • Live log monitoring with grep filtering
   • CHR.db file extraction for all OS types
   • Local file storage with timestamps
============================================================
```

## Usage Workflow

1. **Connect Device**: Connect your Vega/Puffin/FOS device via USB
2. **Enable USB Debugging**: Ensure ADB debugging is enabled
3. **Run Script**: Execute `python adb_gui.py`
4. **Access GUI**: Open the displayed URL in your browser
5. **Select Device**: Choose device from dropdown
6. **Start Logging**: Click Start - tool will automatically detect OS type
7. **Monitor Logs**: View real-time logs in All Logs tab
8. **Apply Filters**: Enter keywords to filter logs
9. **Extract Files**: Use File Pull buttons to extract CHR.db files
10. **Save Data**: Use Save button to store logs locally

## Trial-and-Error Process

When you click "Start Logging", the tool:
1. Tries FOS/Puffin `logcat` command first
2. If no logs received in 3 seconds, tries Vega `journalctl -f`
3. Shows real-time feedback of each attempt
4. Automatically uses the working method
5. Displays detected OS type

Example feedback:
```
[INFO] Starting automatic log detection...
[INFO] Trying method 1/2: FOS/Puffin (logcat)...
[SUCCESS] FOS/Puffin (logcat) method works! Auto-detected: FOS
[INFO] Starting real-time log capture...
```

## File Output

### Log Files
- Format: `adb_logs_YYYYMMDD_HHMMSS.txt`
- Location: Current directory
- Contains: Timestamped log entries with metadata

### CHR Database Files
- Format: `CHR_{OS_TYPE}_YYYYMMDD_HHMMSS.db`
- Location: Current directory
- Contains: Customer Home Registry database

## Error Handling

The tool gracefully handles:
- No devices connected
- Invalid device IDs
- Network timeouts
- Permission issues
- Missing files on device
- Process termination

## Technical Architecture

### Single Script Design
- All functionality in one Python file
- No external templates or assets needed
- Embedded HTML with inline CSS/JavaScript
- Self-contained and portable

### Process Management
- Background threading for log capture
- Proper subprocess cleanup
- Graceful shutdown handling
- Resource management

### API Endpoints
- `/` - Main GUI interface
- `/api/devices` - Get connected devices
- `/api/start-logging` - Start log capture
- `/api/stop-logging` - Stop log capture
- `/api/get-logs` - Retrieve current logs
- `/api/clear-logs` - Clear log buffers
- `/api/save-logs` - Save logs to file
- `/api/pull-file` - Extract CHR.db files

## Troubleshooting

### No Devices Detected
- Check USB connection
- Verify USB debugging is enabled
- Run `adb devices` manually
- Try different USB cable/port

### Logging Not Working
- Check device permissions
- Verify ADB version compatibility
- Try manual ADB commands
- Check device OS type

### File Pull Failures
- Verify file paths exist on device
- Check device permissions
- Ensure sufficient local storage
- Try different OS type selection

### Port Conflicts
Tool automatically handles port conflicts by finding available ports.

## Supported Devices
- **Vega OS**: Smart home devices
- **Puffin OS**: Streaming devices  
- **FOS (Fire OS)**: Amazon Fire devices

## Security Notes
- Tool runs locally only
- No external network connections
- ADB permissions required
- Files saved to local system

## License
Single-purpose development tool for ADB interaction.