#!/usr/bin/env python3
"""
Windows Compatibility Test for ADB GUI Tool
Tests Windows-specific functionality
"""

import platform
import subprocess
import sys
import os

def test_windows_compatibility():
    """Test Windows-specific features"""
    print("="*60)
    print("🪟 ADB GUI Tool - Windows Compatibility Test")
    print("="*60)
    
    # Test 1: Platform Detection
    system = platform.system().lower()
    print(f"✅ Platform detected: {platform.system()} ({platform.platform()})")
    print(f"✅ System type: {system}")
    
    # Test 2: ADB Executable Detection
    adb_cmd = 'adb.exe' if system == 'windows' else 'adb'
    print(f"✅ ADB command will be: {adb_cmd}")
    
    # Test 3: Test ADB availability
    try:
        result = subprocess.run([adb_cmd, '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"✅ ADB executable found and working")
            print(f"   Version: {result.stdout.strip().split()[4] if len(result.stdout.split()) > 4 else 'Unknown'}")
        else:
            print(f"❌ ADB executable not working properly")
            print(f"   Error: {result.stderr}")
    except FileNotFoundError:
        print(f"❌ ADB executable '{adb_cmd}' not found in PATH")
        print(f"   Please install ADB and add it to your PATH")
    except Exception as e:
        print(f"❌ Error testing ADB: {e}")
    
    # Test 4: Test device detection
    print("\n--- Testing Device Detection ---")
    try:
        result = subprocess.run([adb_cmd, 'devices'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ ADB devices command works")
            lines = result.stdout.strip().split('\n')
            print(f"   Output lines: {len(lines)}")
            if len(lines) > 1:
                devices = [line for line in lines[1:] if line.strip()]
                print(f"   Connected devices: {len(devices)}")
                for device in devices:
                    print(f"   - {device}")
            else:
                print("   No devices connected (expected in test environment)")
        else:
            print(f"❌ ADB devices command failed: {result.stderr}")
    except Exception as e:
        print(f"❌ Error testing device detection: {e}")
    
    # Test 5: Threading capability test
    print("\n--- Testing Threading (Windows log reading method) ---")
    try:
        import threading
        import queue
        import time
        
        # Test basic threading functionality
        test_queue = queue.Queue()
        
        def test_thread():
            test_queue.put("Thread working!")
        
        thread = threading.Thread(target=test_thread, daemon=True)
        thread.start()
        thread.join(timeout=1)
        
        try:
            result = test_queue.get_nowait()
            print(f"✅ Threading functionality working: {result}")
        except queue.Empty:
            print(f"❌ Threading test failed - queue empty")
            
    except Exception as e:
        print(f"❌ Threading test error: {e}")
    
    # Test 6: File operations
    print("\n--- Testing File Operations ---")
    try:
        test_file = "test_windows_compatibility.txt"
        with open(test_file, 'w') as f:
            f.write("Windows compatibility test file")
        
        if os.path.exists(test_file):
            file_size = os.path.getsize(test_file)
            print(f"✅ File operations working - created {test_file} ({file_size} bytes)")
            os.remove(test_file)
            print(f"✅ File cleanup successful")
        else:
            print(f"❌ File creation failed")
    except Exception as e:
        print(f"❌ File operations error: {e}")
    
    print("\n" + "="*60)
    print("Windows Compatibility Test Complete")
    print("="*60)
    
    if system == 'windows':
        print("🪟 Running on Windows - using Windows-optimized methods")
        print("   • Threading-based log capture")
        print("   • adb.exe executable detection")
        print("   • Windows-compatible subprocess handling")
    else:
        print("🐧 Running on Unix-like system - using standard methods")
        print("   • select-based log capture")
        print("   • standard adb executable")
    
    print("\n💡 Recommendations:")
    print("   • Ensure ADB is installed from Android SDK")
    print("   • Add ADB to system PATH environment variable")
    print("   • Enable USB debugging on target devices")
    print("   • Use USB 2.0 ports for better device compatibility")

if __name__ == "__main__":
    test_windows_compatibility()