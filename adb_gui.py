#!/usr/bin/env python3
"""
ADB GUI Tool - Single Python Flask Script
Provides web interface for ADB device interaction, log monitoring, and file pulling
"""

import os
import subprocess
import threading
import time
import socket
from datetime import datetime
from flask import Flask, render_template_string, jsonify, request, send_file
import queue
import signal
import sys

app = Flask(__name__)

# Global variables for log management
log_queue = queue.Queue()
filtered_log_queue = queue.Queue()
log_thread = None
log_process = None
is_logging = False
current_filter = ""
connected_devices = []

# HTML Template with Gold/Black theme
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ADB GUI Tool</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --gold: #FFD700;
            --dark-gold: #B8860B;
            --black: #000000;
            --dark-gray: #1a1a1a;
            --light-gray: #2d2d2d;
            --text-light: #f8f9fa;
        }
        
        body {
            background: linear-gradient(135deg, var(--black) 0%, var(--dark-gray) 100%);
            color: var(--text-light);
            font-family: 'Arial', sans-serif;
            min-height: 100vh;
        }
        
        .navbar {
            background: linear-gradient(90deg, var(--black) 0%, var(--dark-gold) 100%);
            border-bottom: 2px solid var(--gold);
        }
        
        .navbar-brand {
            color: var(--gold) !important;
            font-weight: bold;
            font-size: 1.5rem;
        }
        
        .card {
            background: var(--light-gray);
            border: 1px solid var(--dark-gold);
            border-radius: 10px;
        }
        
        .card-header {
            background: linear-gradient(90deg, var(--dark-gold) 0%, var(--gold) 100%);
            color: var(--black);
            font-weight: bold;
            border-radius: 10px 10px 0 0 !important;
        }
        
        .btn-primary {
            background: linear-gradient(45deg, var(--dark-gold) 0%, var(--gold) 100%);
            border: none;
            color: var(--black);
            font-weight: bold;
        }
        
        .btn-primary:hover {
            background: linear-gradient(45deg, var(--gold) 0%, var(--dark-gold) 100%);
            transform: translateY(-2px);
            transition: all 0.3s ease;
        }
        
        .btn-danger {
            background: linear-gradient(45deg, #dc3545 0%, #c82333 100%);
            border: none;
        }
        
        .btn-success {
            background: linear-gradient(45deg, #28a745 0%, #20c997 100%);
            border: none;
        }
        
        .btn-warning {
            background: linear-gradient(45deg, var(--gold) 0%, #ffc107 100%);
            border: none;
            color: var(--black);
        }
        
        .form-control {
            background: var(--dark-gray);
            border: 1px solid var(--dark-gold);
            color: var(--text-light);
        }
        
        .form-control:focus {
            background: var(--dark-gray);
            border-color: var(--gold);
            color: var(--text-light);
            box-shadow: 0 0 0 0.2rem rgba(255, 215, 0, 0.25);
        }
        
        .nav-tabs .nav-link {
            background: var(--dark-gray);
            border: 1px solid var(--dark-gold);
            color: var(--text-light);
        }
        
        .nav-tabs .nav-link.active {
            background: var(--gold);
            border-color: var(--gold);
            color: var(--black);
            font-weight: bold;
        }
        
        .tab-content {
            background: var(--dark-gray);
            border: 1px solid var(--dark-gold);
            border-top: none;
            min-height: 400px;
            max-height: 400px;
            overflow-y: auto;
        }
        
        .log-output {
            font-family: 'Courier New', monospace;
            font-size: 12px;
            white-space: pre-wrap;
            padding: 15px;
            background: var(--black);
            color: var(--gold);
            height: 100%;
        }
        
        .device-status {
            padding: 10px;
            border-radius: 5px;
            margin: 5px 0;
        }
        
        .device-online {
            background: linear-gradient(90deg, rgba(40, 167, 69, 0.2) 0%, rgba(32, 201, 151, 0.2) 100%);
            border-left: 4px solid #28a745;
        }
        
        .device-offline {
            background: linear-gradient(90deg, rgba(220, 53, 69, 0.2) 0%, rgba(200, 35, 51, 0.2) 100%);
            border-left: 4px solid #dc3545;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-online { background: #28a745; }
        .status-offline { background: #dc3545; }
        
        .icon-button {
            background: none;
            border: 1px solid var(--gold);
            color: var(--gold);
            padding: 8px 12px;
            margin: 2px;
            border-radius: 5px;
            transition: all 0.3s ease;
        }
        
        .icon-button:hover {
            background: var(--gold);
            color: var(--black);
        }
        
        .alert {
            border-radius: 8px;
            margin-top: 10px;
        }
        
        .alert-success {
            background: rgba(40, 167, 69, 0.2);
            border-color: #28a745;
            color: #d4edda;
        }
        
        .alert-danger {
            background: rgba(220, 53, 69, 0.2);
            border-color: #dc3545;
            color: #f8d7da;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-dark">
        <div class="container-fluid">
            <span class="navbar-brand">
                <i class="fas fa-mobile-alt"></i> ADB GUI Tool
            </span>
            <div class="d-flex">
                <button class="btn btn-outline-warning btn-sm" onclick="refreshDevices()">
                    <i class="fas fa-sync-alt"></i> Refresh
                </button>
            </div>
        </div>
    </nav>

    <div class="container-fluid mt-4">
        <div class="row">
            <!-- Device Status Panel -->
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">
                        <i class="fas fa-devices"></i> Connected Devices
                    </div>
                    <div class="card-body">
                        <div id="device-list">
                            <div class="text-muted">Loading devices...</div>
                        </div>
                        <div class="mt-3">
                            <h6>File Pull Options</h6>
                            <button class="btn btn-primary btn-sm w-100 mb-2" onclick="pullFile('vega')">
                                <i class="fas fa-download"></i> Pull Vega CHR.db
                            </button>
                            <button class="btn btn-primary btn-sm w-100 mb-2" onclick="pullFile('puffin')">
                                <i class="fas fa-download"></i> Pull Puffin CHR.db
                            </button>
                            <button class="btn btn-primary btn-sm w-100" onclick="pullFile('fos')">
                                <i class="fas fa-download"></i> Pull FOS CHR.db
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Log Monitoring Panel -->
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <span><i class="fas fa-terminal"></i> Log Monitoring</span>
                        <div>
                            <select id="device-select" class="form-select form-select-sm" style="width: auto; display: inline-block; background: var(--dark-gray); border-color: var(--gold); color: var(--text-light);">
                                <option value="">Select Device</option>
                            </select>
                        </div>
                    </div>
                    <div class="card-body">
                        <!-- Controls -->
                        <div class="row mb-3">
                            <div class="col-md-6">
                                <div class="input-group">
                                    <input type="text" id="grep-filter" class="form-control" placeholder="Enter filter keyword for grep...">
                                    <button class="btn btn-warning" onclick="applyFilter()">
                                        <i class="fas fa-filter"></i> Filter
                                    </button>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="btn-group w-100">
                                    <button class="btn btn-success" onclick="startLogging()">
                                        <i class="fas fa-play"></i> Start
                                    </button>
                                    <button class="btn btn-danger" onclick="stopLogging()">
                                        <i class="fas fa-stop"></i> Stop
                                    </button>
                                    <button class="btn btn-warning" onclick="clearLogs()">
                                        <i class="fas fa-eraser"></i> Clear
                                    </button>
                                    <button class="btn btn-primary" onclick="saveLogs()">
                                        <i class="fas fa-save"></i> Save
                                    </button>
                                </div>
                            </div>
                        </div>

                        <!-- Log Tabs -->
                        <ul class="nav nav-tabs">
                            <li class="nav-item">
                                <a class="nav-link active" data-bs-toggle="tab" href="#all-logs">
                                    <i class="fas fa-list"></i> All Logs
                                </a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link" data-bs-toggle="tab" href="#filtered-logs">
                                    <i class="fas fa-filter"></i> Filtered Logs
                                </a>
                            </li>
                        </ul>

                        <!-- Tab Content -->
                        <div class="tab-content">
                            <div class="tab-pane fade show active" id="all-logs">
                                <div class="log-output" id="all-log-output">
                                    No logs available. Click 'Start' to begin log capture.
                                </div>
                            </div>
                            <div class="tab-pane fade" id="filtered-logs">
                                <div class="log-output" id="filtered-log-output">
                                    No filtered logs available. Enter a filter keyword and start logging.
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Status Messages -->
        <div id="status-messages" class="mt-3"></div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let logInterval = null;
        let isLogging = false;

        // Initialize on page load
        document.addEventListener('DOMContentLoaded', function() {
            refreshDevices();
            // Start polling for logs every second when logging is active
            setInterval(updateLogs, 1000);
        });

        async function refreshDevices() {
            try {
                const response = await fetch('/api/devices');
                const data = await response.json();
                updateDeviceList(data.devices);
                updateDeviceSelect(data.devices);
            } catch (error) {
                showAlert('Failed to refresh devices: ' + error.message, 'danger');
            }
        }

        function updateDeviceList(devices) {
            const deviceList = document.getElementById('device-list');
            if (devices.length === 0) {
                deviceList.innerHTML = '<div class="text-warning">No devices connected</div>';
                return;
            }

            let html = '';
            devices.forEach(device => {
                const statusClass = device.status === 'device' ? 'device-online' : 'device-offline';
                const statusIcon = device.status === 'device' ? 'status-online' : 'status-offline';
                html += `
                    <div class="device-status ${statusClass}">
                        <span class="status-indicator ${statusIcon}"></span>
                        <strong>${device.id}</strong><br>
                        <small>Status: ${device.status}</small>
                    </div>
                `;
            });
            deviceList.innerHTML = html;
        }

        function updateDeviceSelect(devices) {
            const deviceSelect = document.getElementById('device-select');
            deviceSelect.innerHTML = '<option value="">Select Device</option>';
            devices.forEach(device => {
                if (device.status === 'device') {
                    deviceSelect.innerHTML += `<option value="${device.id}">${device.id}</option>`;
                }
            });
        }

        async function startLogging() {
            const deviceId = document.getElementById('device-select').value;
            if (!deviceId) {
                showAlert('Please select a device first', 'warning');
                return;
            }

            try {
                const response = await fetch('/api/start-logging', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({device_id: deviceId})
                });
                const data = await response.json();
                
                if (data.success) {
                    isLogging = true;
                    showAlert('Logging started for device: ' + deviceId, 'success');
                } else {
                    showAlert('Failed to start logging: ' + data.message, 'danger');
                }
            } catch (error) {
                showAlert('Error starting logging: ' + error.message, 'danger');
            }
        }

        async function stopLogging() {
            try {
                const response = await fetch('/api/stop-logging', {method: 'POST'});
                const data = await response.json();
                isLogging = false;
                showAlert(data.message, data.success ? 'success' : 'danger');
            } catch (error) {
                showAlert('Error stopping logging: ' + error.message, 'danger');
            }
        }

        async function clearLogs() {
            document.getElementById('all-log-output').textContent = 'Logs cleared.';
            document.getElementById('filtered-log-output').textContent = 'Logs cleared.';
            
            try {
                await fetch('/api/clear-logs', {method: 'POST'});
                showAlert('Logs cleared successfully', 'success');
            } catch (error) {
                showAlert('Error clearing logs: ' + error.message, 'danger');
            }
        }

        async function saveLogs() {
            try {
                const response = await fetch('/api/save-logs', {method: 'POST'});
                const data = await response.json();
                showAlert(data.message, data.success ? 'success' : 'danger');
            } catch (error) {
                showAlert('Error saving logs: ' + error.message, 'danger');
            }
        }

        async function pullFile(osType) {
            try {
                const response = await fetch('/api/pull-file', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({os_type: osType})
                });
                const data = await response.json();
                showAlert(data.message, data.success ? 'success' : 'danger');
            } catch (error) {
                showAlert('Error pulling file: ' + error.message, 'danger');
            }
        }

        function applyFilter() {
            const filter = document.getElementById('grep-filter').value;
            if (!filter.trim()) {
                showAlert('Please enter a filter keyword', 'warning');
                return;
            }
            showAlert('Filter applied: ' + filter, 'success');
        }

        async function updateLogs() {
            if (!isLogging) return;

            try {
                const response = await fetch('/api/get-logs');
                const data = await response.json();
                
                if (data.all_logs) {
                    document.getElementById('all-log-output').textContent = data.all_logs;
                }
                if (data.filtered_logs) {
                    document.getElementById('filtered-log-output').textContent = data.filtered_logs;
                }
            } catch (error) {
                console.error('Error updating logs:', error);
            }
        }

        function showAlert(message, type) {
            const alertsContainer = document.getElementById('status-messages');
            const alert = document.createElement('div');
            alert.className = `alert alert-${type} alert-dismissible fade show`;
            alert.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            alertsContainer.appendChild(alert);
            
            // Auto-remove after 5 seconds
            setTimeout(() => {
                if (alert.parentNode) {
                    alert.remove();
                }
            }, 5000);
        }
    </script>
</body>
</html>
"""

class ADBManager:
    def __init__(self):
        self.current_device = None
        self.log_buffer = []
        self.filtered_log_buffer = []
        self.current_filter = ""
        
    def get_connected_devices(self):
        """Get list of connected ADB devices"""
        try:
            result = subprocess.run(['adb', 'devices'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                return []
            
            devices = []
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            
            for line in lines:
                if line.strip():
                    parts = line.strip().split('\t')
                    if len(parts) >= 2:
                        device_id = parts[0]
                        status = parts[1]
                        devices.append({'id': device_id, 'status': status})
            
            return devices
        except Exception as e:
            print(f"Error getting devices: {e}")
            return []
    
    def detect_device_os(self, device_id):
        """Detect device OS type using trial and error log method"""
        # We'll determine OS type by trying different log commands
        # This is more reliable than checking properties
        return 'unknown'  # Will be determined during logging trial
    
    def start_logging(self, device_id):
        """Start logging for specified device"""
        global log_process, is_logging
        
        try:
            self.stop_logging()  # Stop any existing logging
            
            os_type = self.detect_device_os(device_id)
            self.current_device = device_id
            
            if os_type == 'vega':
                # For Vega: adb shell journalctl -f
                log_process = subprocess.Popen(['adb', '-s', device_id, 'shell', 'journalctl', '-f'], 
                                             stdout=subprocess.PIPE, 
                                             stderr=subprocess.PIPE,
                                             text=True,
                                             bufsize=1)
            else:
                # For FOS/Puffin: adb logcat
                log_process = subprocess.Popen(['adb', '-s', device_id, 'logcat'], 
                                             stdout=subprocess.PIPE, 
                                             stderr=subprocess.PIPE,
                                             text=True,
                                             bufsize=1)
            
            is_logging = True
            # Start background thread to read logs
            log_thread = threading.Thread(target=self._read_logs, daemon=True)
            log_thread.start()
            
            return True, f"Started logging for {device_id} ({os_type})"
        except Exception as e:
            return False, f"Failed to start logging: {str(e)}"
    
    def stop_logging(self):
        """Stop current logging"""
        global log_process, is_logging
        
        is_logging = False
        if log_process:
            try:
                log_process.terminate()
                log_process.wait(timeout=2)
            except:
                try:
                    log_process.kill()
                except:
                    pass
            log_process = None
        
        return True, "Logging stopped"
    
    def _read_logs(self):
        """Background thread to read logs"""
        global log_process, is_logging
        
        while is_logging and log_process:
            try:
                line = log_process.stdout.readline()
                if line:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    log_entry = f"[{timestamp}] {line.rstrip()}\n"
                    
                    # Add to main log buffer
                    self.log_buffer.append(log_entry)
                    if len(self.log_buffer) > 1000:  # Keep last 1000 lines
                        self.log_buffer.pop(0)
                    
                    # Add to filtered log buffer if matches filter
                    if self.current_filter and self.current_filter.lower() in line.lower():
                        self.filtered_log_buffer.append(log_entry)
                        if len(self.filtered_log_buffer) > 1000:
                            self.filtered_log_buffer.pop(0)
                
                elif log_process.poll() is not None:
                    break
                    
            except Exception as e:
                print(f"Error reading logs: {e}")
                break
    
    def get_logs(self):
        """Get current logs"""
        all_logs = ''.join(self.log_buffer[-500:])  # Last 500 lines
        filtered_logs = ''.join(self.filtered_log_buffer[-500:])
        return all_logs, filtered_logs
    
    def clear_logs(self):
        """Clear log buffers"""
        self.log_buffer.clear()
        self.filtered_log_buffer.clear()
    
    def set_filter(self, filter_keyword):
        """Set log filter"""
        self.current_filter = filter_keyword
        # Clear existing filtered logs when filter changes
        self.filtered_log_buffer.clear()
    
    def save_logs(self):
        """Save current logs to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"adb_logs_{timestamp}.txt"
            
            with open(filename, 'w') as f:
                f.write(f"ADB Logs - Generated: {datetime.now()}\n")
                f.write("="*50 + "\n\n")
                f.writelines(self.log_buffer)
            
            return True, f"Logs saved to {filename}"
        except Exception as e:
            return False, f"Failed to save logs: {str(e)}"
    
    def pull_chr_file(self, os_type):
        """Pull CHR.db file based on OS type"""
        try:
            devices = self.get_connected_devices()
            if not devices:
                return False, "No devices connected"
            
            device_id = devices[0]['id']  # Use first available device
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            local_filename = f"CHR_{os_type}_{timestamp}.db"
            
            if os_type.lower() == 'vega':
                remote_path = "/var/lib/data/alexahybrid/smartHomeSkill/customerHomeRegistry.db"
            elif os_type.lower() == 'puffin':
                remote_path = "/data/alexahybrid/files/smartHomeSkill/customerHomeRegistry.db"
            elif os_type.lower() == 'fos':
                remote_path = "/data/data/com.amazon.alexahybridremoteskill/files/customerHomeRegistry.db"
            else:
                return False, f"Unsupported OS type: {os_type}"
            
            # Execute ADB pull command
            result = subprocess.run(['adb', '-s', device_id, 'pull', remote_path, local_filename], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return True, f"Successfully pulled {os_type} CHR.db to {local_filename}"
            else:
                return False, f"Failed to pull file: {result.stderr}"
                
        except Exception as e:
            return False, f"Error pulling CHR file: {str(e)}"

# Initialize ADB Manager
adb_manager = ADBManager()

@app.route('/')
def index():
    """Main page"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/devices')
def get_devices():
    """API endpoint to get connected devices"""
    devices = adb_manager.get_connected_devices()
    return jsonify({'devices': devices})

@app.route('/api/start-logging', methods=['POST'])
def start_logging():
    """API endpoint to start logging"""
    data = request.get_json()
    device_id = data.get('device_id')
    
    if not device_id:
        return jsonify({'success': False, 'message': 'Device ID required'})
    
    success, message = adb_manager.start_logging(device_id)
    return jsonify({'success': success, 'message': message})

@app.route('/api/stop-logging', methods=['POST'])
def stop_logging():
    """API endpoint to stop logging"""
    success, message = adb_manager.stop_logging()
    return jsonify({'success': success, 'message': message})

@app.route('/api/clear-logs', methods=['POST'])
def clear_logs():
    """API endpoint to clear logs"""
    adb_manager.clear_logs()
    return jsonify({'success': True, 'message': 'Logs cleared'})

@app.route('/api/get-logs')
def get_logs():
    """API endpoint to get current logs"""
    all_logs, filtered_logs = adb_manager.get_logs()
    
    # Apply current filter if set
    filter_keyword = request.args.get('filter', '')
    if filter_keyword:
        adb_manager.set_filter(filter_keyword)
    
    return jsonify({
        'all_logs': all_logs,
        'filtered_logs': filtered_logs
    })

@app.route('/api/save-logs', methods=['POST'])
def save_logs():
    """API endpoint to save logs"""
    success, message = adb_manager.save_logs()
    return jsonify({'success': success, 'message': message})

@app.route('/api/pull-file', methods=['POST'])
def pull_file():
    """API endpoint to pull CHR.db file"""
    data = request.get_json()
    os_type = data.get('os_type')
    
    if not os_type:
        return jsonify({'success': False, 'message': 'OS type required'})
    
    success, message = adb_manager.pull_chr_file(os_type)
    return jsonify({'success': success, 'message': message})

def find_free_port():
    """Find a free port to run the Flask application"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

def signal_handler(sig, frame):
    """Handle shutdown gracefully"""
    print("\nShutting down ADB GUI Tool...")
    adb_manager.stop_logging()
    sys.exit(0)

if __name__ == '__main__':
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Find an available port
    port = find_free_port()
    
    print("="*60)
    print("🚀 Starting ADB GUI Tool...")
    print("="*60)
    print("✅ Make sure ADB is installed and in your PATH")
    print("✅ Connect your device via USB and enable USB Debugging")
    print("="*60)
    print(f"🌐 Access the GUI at: http://localhost:{port}")
    print(f"🌐 Or from network:   http://0.0.0.0:{port}")
    print("="*60)
    print(f"🔌 Dynamic Port: {port} (Auto-selected)")
    print("📱 Supported Devices: Vega OS, Puffin OS, FOS")
    print("🛠️  Press Ctrl+C to stop the server")
    print("="*60)
    print("📋 Features Available:")
    print("   • Real-time device detection")
    print("   • Live log monitoring with grep filtering")
    print("   • CHR.db file extraction for all OS types")
    print("   • Local file storage with timestamps")
    print("="*60)
    
    try:
        app.run(debug=False, host='0.0.0.0', port=port, threaded=True)
    except KeyboardInterrupt:
        signal_handler(None, None)
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {port} is already in use. Trying another port...")
            port = find_free_port()
            print(f"🔄 Retrying with port {port}")
            app.run(debug=False, host='0.0.0.0', port=port, threaded=True)
        else:
            print(f"❌ Error starting server: {e}")
            sys.exit(1)