#!/usr/bin/env python3
"""
Test harness for ADB GUI Tool
Tests basic functionality without requiring actual ADB devices
"""

import requests
import time
import sys

BASE_URL = "http://localhost:5000"  # Update this if your Flask app runs on a different port

def test_device_detection():
    """Test 1: Device detection endpoint"""
    print("\n" + "="*60)
    print("TEST 1: Device Detection")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/devices", timeout=5)
        data = response.json()
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"📱 Devices found: {len(data.get('devices', []))}")
        
        for device in data.get('devices', []):
            print(f"   - {device['id']}: {device['status']}")
        
        return True
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def test_logging_without_device():
    """Test 2: Logging without device (should fail gracefully)"""
    print("\n" + "="*60)
    print("TEST 2: Logging Without Device")
    print("="*60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/start-logging",
            json={'device_id': 'test_device_12345'},
            timeout=10
        )
        data = response.json()
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"📝 Response: {data.get('message', 'No message')}")
        print(f"🔍 Success: {data.get('success', False)}")
        
        # Should fail gracefully
        if not data.get('success'):
            print("✅ Correctly rejected invalid device")
            return True
        else:
            print("❌ Should have rejected invalid device")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def test_get_logs():
    """Test 3: Get logs endpoint"""
    print("\n" + "="*60)
    print("TEST 3: Get Logs Endpoint")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/get-logs", timeout=5)
        data = response.json()
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"📊 Log count: {data.get('log_count', 0)}")
        print(f"🔍 Filtered count: {data.get('filtered_count', 0)}")
        print(f"🏃 Is logging: {data.get('is_logging', False)}")
        print(f"🎯 Detection verdict: {data.get('detection_verdict', 'None')}")
        print(f"⚠️  Fallback mode: {data.get('fallback_mode', False)}")
        
        return True
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def test_apply_filters():
    """Test 4: Apply filters endpoint"""
    print("\n" + "="*60)
    print("TEST 4: Apply Filters")
    print("="*60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/apply-filters",
            json={'filters': ['test', 'error', 'warning']},
            timeout=5
        )
        data = response.json()
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"📝 Message: {data.get('message', 'No message')}")
        print(f"🔍 Active filters: {data.get('active_filters', [])}")
        
        return data.get('success', False)
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def test_clear_logs():
    """Test 5: Clear logs endpoint"""
    print("\n" + "="*60)
    print("TEST 5: Clear Logs")
    print("="*60)
    
    try:
        response = requests.post(f"{BASE_URL}/api/clear-logs", timeout=5)
        data = response.json()
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"📝 Message: {data.get('message', 'No message')}")
        
        return True
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def test_file_pull_invalid():
    """Test 6: File pull with invalid OS type"""
    print("\n" + "="*60)
    print("TEST 6: File Pull (Invalid OS Type)")
    print("="*60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/pull-file",
            json={'os_type': 'invalid_os'},
            timeout=5
        )
        data = response.json()
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"📝 Message: {data.get('message', 'No message')}")
        
        # Should fail gracefully
        if not data.get('success'):
            print("✅ Correctly rejected invalid OS type")
            return True
        else:
            print("❌ Should have rejected invalid OS type")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def test_repeated_start_stop():
    """Test 7: Repeated start/stop cycles (stress test)"""
    print("\n" + "="*60)
    print("TEST 7: Repeated Start/Stop (Stress Test)")
    print("="*60)
    
    try:
        cycles = 5
        print(f"Running {cycles} start/stop cycles...")
        
        for i in range(cycles):
            print(f"\n  Cycle {i+1}/{cycles}:")
            
            # Try to start (will fail without device, but should not crash)
            start_response = requests.post(
                f"{BASE_URL}/api/start-logging",
                json={'device_id': f'test_device_{i}'},
                timeout=10
            )
            print(f"    Start: {start_response.status_code}")
            
            time.sleep(0.5)
            
            # Stop
            stop_response = requests.post(f"{BASE_URL}/api/stop-logging", timeout=5)
            print(f"    Stop: {stop_response.status_code}")
            
            time.sleep(0.5)
        
        print(f"\n✅ Completed {cycles} cycles without crashing")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("🧪 ADB GUI TOOL - TEST SUITE")
    print("="*70)
    print(f"Target: {BASE_URL}")
    print("="*70)
    
    # Check if server is running
    try:
        requests.get(BASE_URL, timeout=2)
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERROR: Cannot connect to {BASE_URL}")
        print("Please start the ADB GUI tool first:")
        print("  python3 adb_gui.py")
        sys.exit(1)
    
    tests = [
        ("Device Detection", test_device_detection),
        ("Logging Without Device", test_logging_without_device),
        ("Get Logs", test_get_logs),
        ("Apply Filters", test_apply_filters),
        ("Clear Logs", test_clear_logs),
        ("File Pull (Invalid)", test_file_pull_invalid),
        ("Repeated Start/Stop", test_repeated_start_stop),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Unexpected error in {name}: {str(e)}")
            results.append((name, False))
    
    # Print summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print("="*70)
    print(f"Results: {passed}/{total} tests passed")
    print("="*70)
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
