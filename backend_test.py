#!/usr/bin/env python3
"""
Backend API Testing for ADB GUI Tool
Tests all API endpoints and functionality
"""

import requests
import sys
import time
import json
from datetime import datetime

class ADBGUITester:
    def __init__(self, base_url="http://localhost:47217"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.session = requests.Session()
        self.session.timeout = 10

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=10):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = self.session.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = self.session.post(url, json=data, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)}")
                    return True, response_data
                except:
                    print(f"   Response: {response.text[:200]}...")
                    return True, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                return False, {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timed out after {timeout} seconds")
            return False, {}
        except requests.exceptions.ConnectionError:
            print(f"❌ Failed - Connection error (server may not be running)")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_main_page(self):
        """Test main page loads"""
        success, response = self.run_test(
            "Main Page Load",
            "GET",
            "",
            200
        )
        if success and "ADB GUI Tool" in str(response):
            print("   ✅ Main page contains expected title")
            return True
        elif success:
            print("   ⚠️  Main page loaded but title not found")
            return True
        return False

    def test_device_detection(self):
        """Test device detection API"""
        success, response = self.run_test(
            "Device Detection API",
            "GET",
            "api/devices",
            200
        )
        
        if success and isinstance(response, dict) and 'devices' in response:
            devices = response['devices']
            print(f"   📱 Found {len(devices)} devices")
            for device in devices:
                if isinstance(device, dict) and 'id' in device and 'status' in device:
                    print(f"      - {device['id']}: {device['status']}")
                else:
                    print(f"      - Invalid device format: {device}")
            return True
        return False

    def test_start_logging_no_device(self):
        """Test start logging without device ID"""
        success, response = self.run_test(
            "Start Logging (No Device)",
            "POST",
            "api/start-logging",
            200,
            data={}
        )
        
        if success and isinstance(response, dict):
            if not response.get('success', True):
                print("   ✅ Correctly rejected request without device ID")
                return True
        return False

    def test_start_logging_invalid_device(self):
        """Test start logging with invalid device ID"""
        success, response = self.run_test(
            "Start Logging (Invalid Device)",
            "POST",
            "api/start-logging",
            200,
            data={"device_id": "invalid_device_123"}
        )
        
        if success and isinstance(response, dict):
            # Should either fail or show trial-and-error feedback
            print(f"   Response success: {response.get('success')}")
            print(f"   Message: {response.get('message', 'No message')}")
            return True
        return False

    def test_stop_logging(self):
        """Test stop logging"""
        success, response = self.run_test(
            "Stop Logging",
            "POST",
            "api/stop-logging",
            200
        )
        
        if success and isinstance(response, dict):
            print(f"   Success: {response.get('success')}")
            print(f"   Message: {response.get('message', 'No message')}")
            return True
        return False

    def test_clear_logs(self):
        """Test clear logs"""
        success, response = self.run_test(
            "Clear Logs",
            "POST",
            "api/clear-logs",
            200
        )
        
        if success and isinstance(response, dict):
            if response.get('success'):
                print("   ✅ Logs cleared successfully")
                return True
        return False

    def test_get_logs(self):
        """Test get logs API"""
        success, response = self.run_test(
            "Get Logs",
            "GET",
            "api/get-logs",
            200
        )
        
        if success and isinstance(response, dict):
            if 'all_logs' in response and 'filtered_logs' in response:
                print("   ✅ Log structure is correct")
                print(f"   All logs length: {len(response.get('all_logs', ''))}")
                print(f"   Filtered logs length: {len(response.get('filtered_logs', ''))}")
                return True
        return False

    def test_get_logs_with_filter(self):
        """Test get logs with filter parameter"""
        success, response = self.run_test(
            "Get Logs (With Filter)",
            "GET",
            "api/get-logs?filter=test",
            200
        )
        
        if success and isinstance(response, dict):
            if 'all_logs' in response and 'filtered_logs' in response:
                print("   ✅ Filtered log request handled")
                return True
        return False

    def test_save_logs(self):
        """Test save logs"""
        success, response = self.run_test(
            "Save Logs",
            "POST",
            "api/save-logs",
            200
        )
        
        if success and isinstance(response, dict):
            print(f"   Success: {response.get('success')}")
            print(f"   Message: {response.get('message', 'No message')}")
            return True
        return False

    def test_pull_file_vega(self):
        """Test pull file for Vega OS"""
        success, response = self.run_test(
            "Pull File (Vega)",
            "POST",
            "api/pull-file",
            200,
            data={"os_type": "vega"}
        )
        
        if success and isinstance(response, dict):
            print(f"   Success: {response.get('success')}")
            print(f"   Message: {response.get('message', 'No message')}")
            return True
        return False

    def test_pull_file_puffin(self):
        """Test pull file for Puffin OS"""
        success, response = self.run_test(
            "Pull File (Puffin)",
            "POST",
            "api/pull-file",
            200,
            data={"os_type": "puffin"}
        )
        
        if success and isinstance(response, dict):
            print(f"   Success: {response.get('success')}")
            print(f"   Message: {response.get('message', 'No message')}")
            return True
        return False

    def test_pull_file_fos(self):
        """Test pull file for FOS"""
        success, response = self.run_test(
            "Pull File (FOS)",
            "POST",
            "api/pull-file",
            200,
            data={"os_type": "fos"}
        )
        
        if success and isinstance(response, dict):
            print(f"   Success: {response.get('success')}")
            print(f"   Message: {response.get('message', 'No message')}")
            return True
        return False

    def test_pull_file_no_os_type(self):
        """Test pull file without OS type"""
        success, response = self.run_test(
            "Pull File (No OS Type)",
            "POST",
            "api/pull-file",
            200,
            data={}
        )
        
        if success and isinstance(response, dict):
            if not response.get('success', True):
                print("   ✅ Correctly rejected request without OS type")
                return True
        return False

    def test_pull_file_invalid_os(self):
        """Test pull file with invalid OS type"""
        success, response = self.run_test(
            "Pull File (Invalid OS)",
            "POST",
            "api/pull-file",
            200,
            data={"os_type": "invalid_os"}
        )
        
        if success and isinstance(response, dict):
            print(f"   Success: {response.get('success')}")
            print(f"   Message: {response.get('message', 'No message')}")
            return True
        return False

    def test_invalid_endpoint(self):
        """Test invalid endpoint returns 404"""
        success, response = self.run_test(
            "Invalid Endpoint",
            "GET",
            "api/invalid-endpoint",
            404
        )
        return success

def main():
    print("="*60)
    print("🧪 ADB GUI Tool - Backend API Testing")
    print("="*60)
    
    # Check if server is running
    tester = ADBGUITester()
    
    # Test server connectivity first
    try:
        response = requests.get(f"{tester.base_url}/", timeout=5)
        print(f"✅ Server is running on {tester.base_url}")
    except:
        print(f"❌ Server is not accessible at {tester.base_url}")
        print("   Make sure the ADB GUI application is running")
        return 1

    print(f"🚀 Starting comprehensive API testing...")
    print("="*60)

    # Run all tests
    test_results = []
    
    # Basic functionality tests
    test_results.append(("Main Page", tester.test_main_page()))
    test_results.append(("Device Detection", tester.test_device_detection()))
    
    # Logging API tests
    test_results.append(("Start Logging (No Device)", tester.test_start_logging_no_device()))
    test_results.append(("Start Logging (Invalid Device)", tester.test_start_logging_invalid_device()))
    test_results.append(("Stop Logging", tester.test_stop_logging()))
    test_results.append(("Clear Logs", tester.test_clear_logs()))
    test_results.append(("Get Logs", tester.test_get_logs()))
    test_results.append(("Get Logs (With Filter)", tester.test_get_logs_with_filter()))
    test_results.append(("Save Logs", tester.test_save_logs()))
    
    # File pull tests
    test_results.append(("Pull File (Vega)", tester.test_pull_file_vega()))
    test_results.append(("Pull File (Puffin)", tester.test_pull_file_puffin()))
    test_results.append(("Pull File (FOS)", tester.test_pull_file_fos()))
    test_results.append(("Pull File (No OS Type)", tester.test_pull_file_no_os_type()))
    test_results.append(("Pull File (Invalid OS)", tester.test_pull_file_invalid_os()))
    
    # Error handling tests
    test_results.append(("Invalid Endpoint", tester.test_invalid_endpoint()))

    # Print summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed_tests = []
    failed_tests = []
    
    for test_name, result in test_results:
        if result:
            passed_tests.append(test_name)
            print(f"✅ {test_name}")
        else:
            failed_tests.append(test_name)
            print(f"❌ {test_name}")
    
    print(f"\n📈 Results: {len(passed_tests)}/{len(test_results)} tests passed")
    print(f"🎯 Success Rate: {(len(passed_tests)/len(test_results)*100):.1f}%")
    
    if failed_tests:
        print(f"\n❌ Failed Tests:")
        for test in failed_tests:
            print(f"   - {test}")
    
    print("="*60)
    
    return 0 if len(failed_tests) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())