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
import platform
import psutil  # For robust process management
from datetime import datetime
from flask import Flask, render_template_string, jsonify, request, send_file
import queue
import signal
import sys
import re
import logging
from logging.handlers import RotatingFileHandler

# Windows-specific subprocess constants
if platform.system().lower() == 'windows':
    try:
        # These constants are available in subprocess module on Windows
        STARTF_USESHOWWINDOW = subprocess.STARTF_USESHOWWINDOW
        SW_HIDE = subprocess.SW_HIDE  
        CREATE_NO_WINDOW = subprocess.CREATE_NO_WINDOW
    except AttributeError:
        # Fallback values if not available
        STARTF_USESHOWWINDOW = 0x00000001
        SW_HIDE = 0
        CREATE_NO_WINDOW = 0x08000000

app = Flask(__name__)

# Setup debug logging to file
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s')
log_handler = RotatingFileHandler('logfetcher_debug.log', maxBytes=10*1024*1024, backupCount=3)
log_handler.setFormatter(log_formatter)
log_handler.setLevel(logging.DEBUG)

debug_logger = logging.getLogger('ADBLogFetcher')
debug_logger.setLevel(logging.DEBUG)
debug_logger.addHandler(log_handler)

# Also log to console
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO)
debug_logger.addHandler(console_handler)

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
                            <div class="col-md-12">
                                <label class="form-label text-warning"><i class="fas fa-filter"></i> Grep Filters (Any match will be shown)</label>
                                <div class="row">
                                    <div class="col-md-4">
                                        <div class="input-group mb-2">
                                            <input type="text" id="grep-filter1" class="form-control" placeholder="Filter 1...">
                                        </div>
                                    </div>
                                    <div class="col-md-4">
                                        <div class="input-group mb-2">
                                            <input type="text" id="grep-filter2" class="form-control" placeholder="Filter 2...">
                                        </div>
                                    </div>
                                    <div class="col-md-4">
                                        <div class="input-group mb-2">
                                            <input type="text" id="grep-filter3" class="form-control" placeholder="Filter 3...">
                                            <button class="btn btn-warning" onclick="applyFilters()">
                                                <i class="fas fa-filter"></i> Apply
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="row mb-3">
                            <div class="col-md-12">
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
                                    <button class="btn btn-primary" onclick="showSaveDialog()">
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
                                    <div class="text-muted text-center p-4">
                                        <i class="fas fa-filter fa-2x mb-2"></i><br>
                                        No filtered logs available.<br>
                                        Enter filter keywords and start logging to see matches.
                                    </div>
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

    <!-- Save Dialog Modal -->
    <div class="modal fade" id="saveModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content" style="background: var(--light-gray); border: 1px solid var(--gold);">
                <div class="modal-header" style="background: var(--gold); color: var(--black);">
                    <h5 class="modal-title"><i class="fas fa-save"></i> Save Logs</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="mb-3">
                        <label for="filename-input" class="form-label text-light">Filename (will be saved as .txt)</label>
                        <input type="text" class="form-control" id="filename-input" placeholder="Enter filename without extension">
                        <div class="form-text text-muted">File will be saved in current directory</div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-primary" onclick="saveLogsWithFilename()">
                        <i class="fas fa-save"></i> Save
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- File Pull Success Modal -->
    <div class="modal fade" id="filePullModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content" style="background: var(--light-gray); border: 1px solid var(--gold);">
                <div class="modal-header" id="pullModalHeader">
                    <h5 class="modal-title" id="pullModalTitle"></h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <p id="pullModalMessage"></p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-primary" data-bs-dismiss="modal">OK</button>
                </div>
            </div>
        </div>
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

        async function pullFile(osType) {
            try {
                const response = await fetch('/api/pull-file', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({os_type: osType})
                });
                const data = await response.json();
                
                // Show modal popup with result
                const modal = new bootstrap.Modal(document.getElementById('filePullModal'));
                const modalTitle = document.getElementById('pullModalTitle');
                const modalMessage = document.getElementById('pullModalMessage');
                const modalHeader = document.getElementById('pullModalHeader');
                
                if (data.success) {
                    modalTitle.innerHTML = '<i class="fas fa-check-circle"></i> File Pull Successful';
                    modalHeader.style.background = 'var(--gold)';
                    modalHeader.style.color = 'var(--black)';
                    modalMessage.textContent = data.message;
                } else {
                    modalTitle.innerHTML = '<i class="fas fa-exclamation-triangle"></i> File Pull Failed';
                    modalHeader.style.background = '#dc3545';
                    modalHeader.style.color = 'white';
                    modalMessage.textContent = data.message;
                }
                
                modal.show();
            } catch (error) {
                const modal = new bootstrap.Modal(document.getElementById('filePullModal'));
                const modalTitle = document.getElementById('pullModalTitle');
                const modalMessage = document.getElementById('pullModalMessage');
                const modalHeader = document.getElementById('pullModalHeader');
                
                modalTitle.innerHTML = '<i class="fas fa-exclamation-triangle"></i> File Pull Error';
                modalHeader.style.background = '#dc3545';
                modalHeader.style.color = 'white';
                modalMessage.textContent = 'Error pulling file: ' + error.message;
                modal.show();
            }
        }

        function showSaveDialog() {
            // Set default filename with timestamp
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
            document.getElementById('filename-input').value = `adb_logs_${timestamp}`;
            
            const modal = new bootstrap.Modal(document.getElementById('saveModal'));
            modal.show();
        }

        async function saveLogsWithFilename() {
            const filename = document.getElementById('filename-input').value.trim();
            if (!filename) {
                showAlert('Please enter a filename', 'warning');
                return;
            }
            
            try {
                const response = await fetch('/api/save-logs', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({filename: filename})
                });
                const data = await response.json();
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('saveModal'));
                modal.hide();
                
                showAlert(data.message, data.success ? 'success' : 'danger');
            } catch (error) {
                showAlert('Error saving logs: ' + error.message, 'danger');
            }
        }

        function applyFilters() {
            const filter1 = document.getElementById('grep-filter1').value.trim();
            const filter2 = document.getElementById('grep-filter2').value.trim();
            const filter3 = document.getElementById('grep-filter3').value.trim();
            
            if (!filter1 && !filter2 && !filter3) {
                showAlert('Please enter at least one filter keyword', 'warning');
                return;
            }
            
            const filters = [filter1, filter2, filter3].filter(f => f !== '');
            
            // Send filters to backend to apply them
            fetch('/api/apply-filters', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({filters: filters})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert(`Filters applied: ${filters.join(', ')}`, 'success');
                } else {
                    showAlert('Failed to apply filters: ' + data.message, 'danger');
                }
            })
            .catch(error => {
                showAlert('Error applying filters: ' + error.message, 'danger');
            });
        }

        async function clearLogs() {
            document.getElementById('all-log-output').textContent = 'Logs cleared.';
            document.getElementById('filtered-log-output').innerHTML = `
                <div class="text-muted text-center p-4">
                    <i class="fas fa-filter fa-2x mb-2"></i><br>
                    No filtered logs available.<br>
                    Enter filter keywords and start logging to see matches.
                </div>
            `;
            
            try {
                await fetch('/api/clear-logs', {method: 'POST'});
                showAlert('Logs cleared successfully', 'success');
            } catch (error) {
                showAlert('Error clearing logs: ' + error.message, 'danger');
            }
        }

        async function updateLogs() {
            if (!isLogging) return;

            try {
                const response = await fetch('/api/get-logs');
                const data = await response.json();
                
                if (data.all_logs) {
                    document.getElementById('all-log-output').textContent = data.all_logs;
                }
                if (data.filtered_logs !== undefined) {
                    const filteredOutput = document.getElementById('filtered-log-output');
                    if (data.filtered_logs === "" || data.filtered_logs.includes('<div class="text-muted')) {
                        // HTML message for no matches or empty
                        filteredOutput.innerHTML = data.filtered_logs || `
                            <div class="text-muted text-center p-4">
                                <i class="fas fa-filter fa-2x mb-2"></i><br>
                                No filtered logs available.<br>
                                Enter filter keywords and start logging to see matches.
                            </div>
                        `;
                    } else {
                        // Regular log text - preserve existing content and append new
                        filteredOutput.textContent = data.filtered_logs;
                    }
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
        self.current_filters = []  # User filters
        self.platform_system = platform.system().lower()
        self.current_log_method = None
        self.is_logging_active = False
        self.log_thread = None
        self.log_process = None
        
        # Target patterns for Python-side filtering (base patterns)
        self.base_patterns = [
            r"CosineSimilarityCache::LookupImpl",
            r"eventType=Speech", 
            r"RESULT_GENERATOR",
            r"Calling onCacheUpdate"
        ]
        
        # ADB command setup
        self.adb_cmd = 'adb.exe' if self.platform_system == 'windows' else 'adb'
        
    def get_connected_devices(self):
        """Get list of connected ADB devices - Windows compatible"""
        try:
            # Determine ADB executable name based on platform
            adb_cmd = 'adb.exe' if self.platform_system == 'windows' else 'adb'
            
            result = subprocess.run([adb_cmd, 'devices'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                print(f"ADB devices command failed: {result.stderr}")
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
            
            print(f"Found {len(devices)} ADB devices ({self.platform_system})")
            return devices
            
        except FileNotFoundError:
            print(f"ADB executable not found. Make sure ADB is installed and in PATH ({self.platform_system})")
            return []
        except Exception as e:
            print(f"Error getting devices ({self.platform_system}): {e}")
            return []
    
    def aggressive_cleanup(self, device_id=None):
        """Aggressive cleanup for robust restart capability"""
        global log_process, is_logging
        
        self.add_log_entry("[INFO] Starting aggressive cleanup for robust restart")
        
        # Step 1: Stop Python logging
        is_logging = False
        self.is_logging_active = False
        
        # Step 2: Kill Python log process
        if self.log_process:
            try:
                self.add_log_entry(f"[INFO] Terminating Python log process (PID: {self.log_process.pid})")
                
                # Kill process tree (important for Windows)
                if self.platform_system == 'windows':
                    try:
                        parent = psutil.Process(self.log_process.pid)
                        children = parent.children(recursive=True)
                        for child in children:
                            child.terminate()
                        parent.terminate()
                        
                        # Wait and force kill if needed
                        psutil.wait_procs([parent] + children, timeout=3)
                    except psutil.NoSuchProcess:
                        pass
                else:
                    # Unix: Standard termination
                    self.log_process.terminate()
                    try:
                        self.log_process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        self.log_process.kill()
                        self.log_process.wait(timeout=2)
                        
            except Exception as e:
                self.add_log_entry(f"[WARN] Python process cleanup error: {str(e)}")
            
            self.log_process = None
            log_process = None
        
        # Step 3: Kill device-side processes
        if device_id:
            try:
                self.add_log_entry("[INFO] Cleaning up device-side processes")
                
                # Kill logcat processes
                subprocess.run([self.adb_cmd, '-s', device_id, 'shell', 'pkill', '-f', 'logcat'], 
                             capture_output=True, timeout=5)
                
                # Kill journalctl processes  
                subprocess.run([self.adb_cmd, '-s', device_id, 'shell', 'pkill', '-f', 'journalctl'], 
                             capture_output=True, timeout=5)
                
                time.sleep(1)  # Let device settle
                
            except Exception as e:
                self.add_log_entry(f"[WARN] Device cleanup warning: {str(e)}")
        
        # Step 4: ADB server reset (critical for Windows reliability)
        try:
            self.add_log_entry("[INFO] Resetting ADB server for clean state")
            subprocess.run([self.adb_cmd, 'kill-server'], capture_output=True, timeout=5)
            time.sleep(2)
            subprocess.run([self.adb_cmd, 'start-server'], capture_output=True, timeout=10)
            time.sleep(3)  # Let ADB stabilize
        except Exception as e:
            self.add_log_entry(f"[WARN] ADB server reset warning: {str(e)}")
        
        # Step 5: Clean up thread references
        if self.log_thread and self.log_thread.is_alive():
            try:
                self.log_thread.join(timeout=2)
            except:
                pass
        self.log_thread = None
        
        # Step 6: Reset all state variables
        self.current_device = None
        self.current_log_method = None
        
        # Step 7: Clear buffers for fresh start
        self.log_buffer.clear()
        self.filtered_log_buffer.clear()
        
        self.add_log_entry("[SUCCESS] Aggressive cleanup completed")
        
        # Final stabilization delay
        time.sleep(2)

    def test_device_connectivity(self, device_id, max_attempts=3):
        """Robust device connectivity testing"""
        for attempt in range(max_attempts):
            try:
                self.add_log_entry(f"[INFO] Testing connectivity to {device_id} (attempt {attempt + 1}/{max_attempts})")
                
                result = subprocess.run(
                    [self.adb_cmd, '-s', device_id, 'shell', 'getprop', 'ro.build.type'], 
                    capture_output=True, text=True, timeout=10
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    self.add_log_entry(f"[SUCCESS] Device connectivity confirmed: {result.stdout.strip()}")
                    return True
                else:
                    if attempt < max_attempts - 1:
                        self.add_log_entry(f"[WARN] Connectivity attempt {attempt + 1} failed, retrying...")
                        time.sleep(3)
                    
            except Exception as e:
                if attempt < max_attempts - 1:
                    self.add_log_entry(f"[WARN] Connectivity error: {str(e)}, retrying...")
                    time.sleep(3)
                else:
                    self.add_log_entry(f"[ERROR] Final connectivity test failed: {str(e)}")
        
        return False
    
    def add_log_entry(self, message, apply_filters=True):
        """Add a log entry and apply filters if needed"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # Add to main log buffer
        self.log_buffer.append(log_entry)
        if len(self.log_buffer) > 1000:
            self.log_buffer.pop(0)
        
        # Apply filters if requested
        if apply_filters and self.current_filters:
            for filter_keyword in self.current_filters:
                if filter_keyword and filter_keyword.lower() in message.lower():
                    self.filtered_log_buffer.append(log_entry)
                    if len(self.filtered_log_buffer) > 1000:
                        self.filtered_log_buffer.pop(0)
                    print(f"FILTERED LOG MATCH: '{filter_keyword}' found in: {message.strip()}")
                    break
    
    def start_logging(self, device_id):
        """Main entry point for starting logging - delegates to robust implementation"""
        return self.start_logging_robust(device_id)
    
    def start_logging_robust(self, device_id):
        """Robust logging with Python-side filtering (no shell pipes)"""
        global log_process, is_logging
        
        try:
            # Validate input
            if not device_id or not device_id.strip():
                return False, "❌ Device ID is required"
            
            device_id = device_id.strip()
            
            # Step 1: Aggressive cleanup first
            self.aggressive_cleanup(device_id)
            
            # Step 2: Test connectivity 
            if not self.test_device_connectivity(device_id):
                return False, f"❌ Cannot establish reliable connection to device {device_id}. Check USB debugging and ADB setup."
            
            self.current_device = device_id
            self.add_log_entry(f"[INFO] Starting robust logging for device: {device_id}")
            self.add_log_entry(f"[INFO] Platform: {self.platform_system.title()}, ADB: {self.adb_cmd}")
            
            # Step 3: Try log methods with Python-side filtering
            log_methods = [
                {
                    'name': 'FOS/Puffin (logcat - Python filtered)',
                    'command': [self.adb_cmd, '-s', device_id, 'shell', 'logcat', '-c'],  # Clear first
                    'stream_command': [self.adb_cmd, '-s', device_id, 'shell', 'logcat'],  # Then stream
                    'os_type': 'fos'
                },
                {
                    'name': 'Vega (journalctl - Python filtered)', 
                    'command': None,  # No clear command
                    'stream_command': [self.adb_cmd, '-s', device_id, 'shell', 'journalctl', '-f'],
                    'os_type': 'vega'
                }
            ]
            
            for i, method in enumerate(log_methods, 1):
                self.add_log_entry(f"[INFO] Trying method {i}/2: {method['name']}")
                
                try:
                    # Clear buffer for FOS
                    if method['command']:
                        self.add_log_entry("[INFO] Clearing logcat buffer...")
                        subprocess.run(method['command'], capture_output=True, timeout=5)
                        time.sleep(1)
                    
                    # Start streaming process (no shell pipes!)
                    self.add_log_entry(f"[INFO] Starting raw log stream: {' '.join(method['stream_command'])}")
                    
                    test_process = subprocess.Popen(
                        method['stream_command'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        bufsize=0,  # Unbuffered for real-time
                        universal_newlines=True
                    )
                    
                    # Test for 30 seconds (extended detection time)
                    self.add_log_entry("[INFO] Testing log stream for 30 seconds...")
                    lines_received = 0
                    start_time = time.time()
                    
                    while time.time() - start_time < 30:
                        if test_process.poll() is not None:
                            # Process died
                            try:
                                _, stderr = test_process.communicate(timeout=2)
                                self.add_log_entry(f"[ERROR] {method['name']} process died: {stderr.strip()}")
                                break
                            except:
                                self.add_log_entry(f"[ERROR] {method['name']} process died unexpectedly")
                                break
                        
                        try:
                            # Non-blocking read attempt
                            line = test_process.stdout.readline()
                            if line:
                                lines_received += 1
                                if lines_received <= 3:  # Show first few lines
                                    self.add_log_entry(f"[SAMPLE] {line.strip()}")
                                
                                if lines_received >= 5:  # Success criteria: 5+ lines
                                    self.add_log_entry(f"[SUCCESS] {method['name']} working! Got {lines_received} lines")
                                    
                                    # This method works, start actual logging
                                    self.log_process = test_process
                                    log_process = test_process
                                    is_logging = True
                                    self.is_logging_active = True
                                    
                                    self.current_log_method = method
                                    
                                    # Start background thread for continuous reading with Python filtering
                                    self.log_thread = threading.Thread(
                                        target=self._read_logs_with_python_filtering, 
                                        daemon=True
                                    )
                                    self.log_thread.start()
                                    
                                    return True, f"✅ Started robust logging for {device_id} using {method['name']} (Detected: {method['os_type'].upper()})"
                        
                        except Exception as e:
                            # Non-critical read error, continue testing
                            pass
                        
                        time.sleep(0.1)  # Brief pause between read attempts
                    
                    # Method failed - didn't get enough output
                    self.add_log_entry(f"[WARN] {method['name']} insufficient output ({lines_received} lines in 30s)")
                    
                    try:
                        test_process.terminate()
                        test_process.wait(timeout=2)
                    except:
                        try:
                            test_process.kill()
                        except:
                            pass
                    
                except Exception as e:
                    self.add_log_entry(f"[ERROR] {method['name']} exception: {str(e)}")
                    continue
            
            # All methods failed
            return False, "❌ All logging methods failed. Ensure device is generating logs and applications are active."
            
        except Exception as e:
            self.aggressive_cleanup()
            return False, f"❌ Logging startup error: {str(e)}"
    
    def _read_logs_with_python_filtering(self):
        """Read logs continuously with Python-side filtering"""
        global is_logging
        
        self.add_log_entry("[INFO] Starting Python-side log filtering thread")
        
        try:
            while is_logging and self.is_logging_active and self.log_process:
                try:
                    # Check if process is still alive
                    if self.log_process.poll() is not None:
                        self.add_log_entry("[WARN] Log process terminated unexpectedly")
                        break
                    
                    # Read line with timeout
                    line = self.log_process.stdout.readline()
                    
                    if line:
                        line = line.strip()
                        if line:  # Non-empty line
                            timestamp = datetime.now().strftime("%H:%M:%S")
                            log_entry = f"[{timestamp}] {line}\n"
                            
                            # Check if line matches base patterns (Python-side filtering)
                            matches_base_pattern = any(
                                re.search(pattern, line, re.IGNORECASE) 
                                for pattern in self.base_patterns
                            )
                            
                            if matches_base_pattern:
                                # Add to main log buffer (all base pattern matches)
                                self.log_buffer.append(log_entry)
                                if len(self.log_buffer) > 2000:  # Increased buffer size
                                    self.log_buffer.pop(0)
                                
                                # Apply user filters on top of base filtering
                                if self.current_filters:
                                    for user_filter in self.current_filters:
                                        if user_filter and user_filter.lower() in line.lower():
                                            self.filtered_log_buffer.append(log_entry)
                                            if len(self.filtered_log_buffer) > 2000:
                                                self.filtered_log_buffer.pop(0)
                                            print(f"PYTHON FILTER MATCH: '{user_filter}' in: {line[:60]}...")
                                            break
                                else:
                                    # No user filters, show all base pattern matches
                                    self.filtered_log_buffer.append(log_entry)
                                    if len(self.filtered_log_buffer) > 2000:
                                        self.filtered_log_buffer.pop(0)
                    
                    else:
                        # No line read, brief pause to avoid busy waiting
                        time.sleep(0.05)
                        
                except Exception as e:
                    print(f"Python filtering thread error: {e}")
                    self.add_log_entry(f"[ERROR] Log reading error: {str(e)}")
                    break
        
        except Exception as e:
            print(f"Python filtering thread fatal error: {e}")
            self.add_log_entry(f"[ERROR] Log filtering thread failed: {str(e)}")
        
        finally:
            self.add_log_entry("[INFO] Python-side log filtering thread terminated")
            print("Python-side log filtering thread terminated")

    def stop_logging(self):
        """Stop logging with aggressive cleanup"""
        was_logging = self.is_logging_active
        
        self.aggressive_cleanup(self.current_device)
        
        if was_logging:
            self.add_log_entry("[SUCCESS] Logging stopped with complete cleanup")
            return True, "✅ Logging stopped successfully with aggressive cleanup"
        else:
            return True, "ℹ️ No active logging to stop"
    
    # OLD METHODS REMOVED - Using unified Python-side filtering approach
    # Removed: _start_logging_unix (old shell-pipe approach)
    # Removed: duplicate stop_logging method (old approach)
    
    # OLD METHOD REMOVED: _read_logs_windows_direct
    # Now using unified _read_logs_with_python_filtering for all platforms

    def clear_logs(self):
        """Clear log buffers with validation"""
        log_count = len(self.log_buffer)
        filtered_count = len(self.filtered_log_buffer)
        
        if log_count == 0 and filtered_count == 0:
            return "ℹ️ No logs to clear"
        
        self.log_buffer.clear()
        self.filtered_log_buffer.clear()
        
        print(f"Cleared {log_count} main logs and {filtered_count} filtered logs")
        return f"✅ Cleared {log_count} main logs and {filtered_count} filtered logs"
    
    # OLD METHODS REMOVED: _read_logs_windows and _read_logs_unix
    # Now using unified _read_logs_with_python_filtering for all platforms
    
    def get_logs(self):
        """Get current logs"""
        all_logs = ''.join(self.log_buffer[-500:])  # Last 500 lines
        filtered_logs = ''.join(self.filtered_log_buffer[-500:])
        
        # If no filtered logs but filters are applied, show helpful message
        if self.current_filters and not filtered_logs.strip():
            filtered_logs = f"""<div class="text-muted text-center p-4">
<i class="fas fa-search fa-2x mb-2"></i><br>
<strong>Active Filters:</strong> {', '.join(self.current_filters)}<br>
<small>No logs match your filters yet. Waiting for matching log entries...</small>
</div>"""
        elif not self.current_filters:
            filtered_logs = """<div class="text-muted text-center p-4">
<i class="fas fa-filter fa-2x mb-2"></i><br>
No filtered logs available.<br>
Enter filter keywords and start logging to see matches.
</div>"""
        
        return all_logs, filtered_logs
    
    def clear_logs(self):
        """Clear log buffers with validation"""
        log_count = len(self.log_buffer)
        filtered_count = len(self.filtered_log_buffer)
        
        if log_count == 0 and filtered_count == 0:
            print("No logs to clear")
            return "ℹ️ No logs to clear"
        
        self.log_buffer.clear()
        self.filtered_log_buffer.clear()
        
        print(f"Cleared {log_count} main logs and {filtered_count} filtered logs")
        return f"✅ Cleared {log_count} main logs and {filtered_count} filtered logs"
    
    def set_filters(self, filter_keywords):
        """Set multiple log filters"""
        self.current_filters = [f.strip() for f in filter_keywords if f.strip()]
        # Clear existing filtered logs when filters change
        self.filtered_log_buffer.clear()
    
    def save_logs(self, custom_filename=None):
        """Save current logs to file with custom filename and validation"""
        try:
            # Check if there are any logs to save
            if not self.log_buffer:
                return False, "❌ No logs to save. Start logging first to capture logs."
            
            if custom_filename:
                # Use custom filename, ensure .txt extension
                if not custom_filename.endswith('.txt'):
                    filename = f"{custom_filename}.txt"
                else:
                    filename = custom_filename
            else:
                # Use default timestamp filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"adb_logs_{timestamp}.txt"
            
            with open(filename, 'w') as f:
                f.write(f"ADB Logs - Generated: {datetime.now()}\n")
                f.write(f"Platform: {self.platform_system.title()}\n")
                f.write(f"Total log entries: {len(self.log_buffer)}\n")
                f.write("="*50 + "\n\n")
                f.writelines(self.log_buffer)
            
            file_size = os.path.getsize(filename)
            return True, f"✅ {len(self.log_buffer)} log entries saved to {filename} ({file_size} bytes)"
        except Exception as e:
            return False, f"❌ Failed to save logs: {str(e)}"
    
    def pull_chr_file(self, os_type):
        """Pull CHR.db file based on OS type with trial and error method - Windows compatible"""
        try:
            devices = self.get_connected_devices()
            if not devices:
                return False, "No devices connected"
            
            # Find first available device
            device_id = None
            for device in devices:
                if device['status'] == 'device':
                    device_id = device['id']
                    break
            
            if not device_id:
                return False, "No active devices found"
            
            # Determine ADB executable name based on platform
            adb_cmd = 'adb.exe' if self.platform_system == 'windows' else 'adb'
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            local_filename = f"CHR_{os_type}_{timestamp}.db"
            
            # Define all possible paths for each OS type
            path_mapping = {
                'vega': [
                    "/var/lib/data/alexahybrid/smartHomeSkill/customerHomeRegistry.db",
                    "/var/lib/alexahybrid/smartHomeSkill/customerHomeRegistry.db",
                    "/data/alexahybrid/smartHomeSkill/customerHomeRegistry.db"
                ],
                'puffin': [
                    "/data/alexahybrid/files/smartHomeSkill/customerHomeRegistry.db",
                    "/data/alexahybrid/smartHomeSkill/customerHomeRegistry.db"
                ],
                'fos': [
                    "/data/data/com.amazon.alexahybridremoteskill/files/customerHomeRegistry.db",
                    "/data/data/com.amazon.alexahybrid/files/customerHomeRegistry.db"
                ]
            }
            
            remote_paths = path_mapping.get(os_type.lower(), [])
            if not remote_paths:
                return False, f"Unsupported OS type: {os_type}"
            
            # Try each path until one works
            for i, remote_path in enumerate(remote_paths, 1):
                try:
                    print(f"Trying path {i}/{len(remote_paths)}: {remote_path} ({self.platform_system})")
                    
                    # Execute ADB pull command
                    result = subprocess.run([adb_cmd, '-s', device_id, 'pull', remote_path, local_filename], 
                                          capture_output=True, text=True, timeout=30)
                    
                    if result.returncode == 0 and os.path.exists(local_filename):
                        # Check if file has actual content (not empty)
                        file_size = os.path.getsize(local_filename)
                        if file_size > 0:
                            return True, f"✅ Successfully pulled {os_type.upper()} CHR.db to {local_filename} ({file_size} bytes) on {self.platform_system.title()}"
                        else:
                            # File exists but is empty, try next path
                            os.remove(local_filename)
                            continue
                    else:
                        # Command failed, try next path
                        if os.path.exists(local_filename):
                            os.remove(local_filename)
                        continue
                        
                except subprocess.TimeoutExpired:
                    return False, f"Pull operation timed out for {os_type} on {self.platform_system.title()}"
                except Exception as e:
                    print(f"Error trying path {remote_path} on {self.platform_system}: {str(e)}")
                    continue
            
            return False, f"❌ Failed to pull {os_type.upper()} CHR.db - file not found in any expected location ({self.platform_system.title()})"
                
        except Exception as e:
            return False, f"Error pulling CHR file on {self.platform_system.title()}: {str(e)}"

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
    """API endpoint to start logging with validation"""
    try:
        data = request.get_json()
        device_id = data.get('device_id', '').strip() if data else ''
        
        if not device_id:
            return jsonify({'success': False, 'message': '❌ Device ID is required to start logging'})
        
        success, message = adb_manager.start_logging(device_id)
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'message': f'❌ Error starting logging: {str(e)}'})

@app.route('/api/stop-logging', methods=['POST'])
def stop_logging():
    """API endpoint to stop logging with validation"""
    try:
        success, message = adb_manager.stop_logging()
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'message': f'❌ Error stopping logging: {str(e)}'})

@app.route('/api/clear-logs', methods=['POST'])
def clear_logs():
    """API endpoint to clear logs with validation"""
    try:
        message = adb_manager.clear_logs()
        return jsonify({'success': True, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'message': f'❌ Error clearing logs: {str(e)}'})

@app.route('/api/save-logs', methods=['POST'])
def save_logs():
    """API endpoint to save logs with validation"""
    try:
        data = request.get_json() or {}
        custom_filename = data.get('filename', '').strip()
        
        success, message = adb_manager.save_logs(custom_filename if custom_filename else None)
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'message': f'❌ Error saving logs: {str(e)}'})

@app.route('/api/apply-filters', methods=['POST'])
def apply_filters():
    """API endpoint to apply multiple filters with validation"""
    try:
        data = request.get_json()
        filters = data.get('filters', []) if data else []
        
        # Validate and clean filters
        valid_filters = [f.strip() for f in filters if f and f.strip()]
        
        if not valid_filters:
            return jsonify({'success': False, 'message': '❌ At least one valid filter keyword is required'})
        
        adb_manager.set_filters(valid_filters)
        return jsonify({
            'success': True, 
            'message': f'✅ Filters applied: {", ".join(valid_filters)}',
            'active_filters': valid_filters
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'❌ Error applying filters: {str(e)}'})

@app.route('/api/pull-file', methods=['POST'])
def pull_file():
    """API endpoint to pull CHR.db file with validation"""
    try:
        data = request.get_json()
        os_type = data.get('os_type', '').strip().lower() if data else ''
        
        if os_type not in ['vega', 'puffin', 'fos']:
            return jsonify({'success': False, 'message': '❌ Invalid OS type. Must be vega, puffin, or fos'})
        
        success, message = adb_manager.pull_chr_file(os_type)
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'message': f'❌ Error pulling file: {str(e)}'})

@app.route('/api/get-logs')
def get_logs():
    """API endpoint to get current logs with status info"""
    try:
        all_logs, filtered_logs = adb_manager.get_logs()
        
        return jsonify({
            'all_logs': all_logs,
            'filtered_logs': filtered_logs,
            'active_filters': adb_manager.current_filters,
            'is_logging': adb_manager.is_logging_active,
            'current_device': adb_manager.current_device,
            'log_count': len(adb_manager.log_buffer),
            'filtered_count': len(adb_manager.filtered_log_buffer)
        })
    except Exception as e:
        return jsonify({
            'error': f'Error retrieving logs: {str(e)}',
            'all_logs': '',
            'filtered_logs': '',
            'active_filters': [],
            'is_logging': False
        })

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
    
    print("="*70)
    print("🚀 Starting ADB GUI Tool with Specific Log Pattern Filtering...")
    print("="*70)
    print("✅ Make sure ADB is installed and in your PATH")
    print("✅ Connect your device via USB and enable USB Debugging")
    print("="*70)
    print(f"🌐 Access the GUI at: http://localhost:{port}")
    print(f"🌐 Or from network:   http://0.0.0.0:{port}")
    print("="*70)
    print(f"🔌 Dynamic Port: {port} (Auto-selected)")
    print(f"💻 Platform: {platform.system()} ({platform.platform()})")
    print(f"🔧 ADB Command: {'adb.exe' if platform.system().lower() == 'windows' else 'adb'}")
    print(f"🔍 Filter Command: {'findstr' if platform.system().lower() == 'windows' else 'grep'}")
    print("📱 Supported Devices: Vega OS, Puffin OS, FOS")
    print("🛠️  Press Ctrl+C to stop the server")
    print("="*70)
    print("📋 Enhanced Features Available:")
    print("   • Real-time device detection")
    print("   • Specific log pattern filtering (CosineSimilarityCache, eventType=Speech, etc.)")
    print("   • Cross-platform log monitoring (Windows/Mac/Linux)")
    print("   • Multi-filter user grep support (3 additional filter inputs)")
    print("   • CHR.db file extraction for all OS types")
    print("   • Local file storage with timestamps")
    print("="*70)
    print("🎯 Target Log Patterns:")
    print("   • CosineSimilarityCache::LookupImpl")
    print("   • eventType=Speech")
    print("   • RESULT_GENERATOR")
    print("   • Calling onCacheUpdate")
    print("="*70)
    if platform.system().lower() == 'windows':
        print("🪟 Windows Optimizations:")
        print("   • File-based log capture with findstr filtering")
        print("   • adb.exe executable detection")
        print("   • Hidden console windows")
    else:
        print("🐧 Unix/Linux/Mac Optimizations:")
        print("   • Pipe-based log capture with grep filtering")  
        print("   • Standard ADB executable")
        print("   • Select-based I/O for performance")
    print("="*70)
    
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