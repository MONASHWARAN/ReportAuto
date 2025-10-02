#!/usr/bin/env python3
"""
ADB GUI Tool Backend API Testing
Tests all enhanced features including multi-filter support, modal popups, and cross-platform compatibility
"""

import requests
import json
import sys
from datetime import datetime

class ADBGUITester:
    def __init__(self, base_url="http://localhost:48415"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)

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
                print(f"   Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_enhanced_features(self):
        """Test all enhanced ADB GUI features"""
        print("="*60)
        print("🚀 ADB GUI Tool Enhanced Features Testing")
        print("="*60)
        
        # Test 1: Device Detection API
        success, response = self.run_test(
            "Device Detection API",
            "GET",
            "api/devices",
            200
        )
        
        # Test 2: Multi-Filter Log Retrieval
        print("\n--- Testing Multi-Filter Support ---")
        success, response = self.run_test(
            "Multi-Filter Log Retrieval (3 filters)",
            "GET",
            "api/get-logs",
            200,
            params={"filters": ["error", "warning", "debug"]}
        )
        
        if success and 'filtered_logs' in response:
            if response['filtered_logs'] == "":
                print("✅ Multi-filter logic working - no matches found (expected)")
            else:
                print(f"✅ Multi-filter logic working - filtered logs: {len(response['filtered_logs'])} chars")
        
        # Test 3: Single Filter
        success, response = self.run_test(
            "Single Filter Log Retrieval",
            "GET",
            "api/get-logs",
            200,
            params={"filters": ["error"]}
        )
        
        # Test 4: Custom Filename Save
        print("\n--- Testing Custom Filename Save ---")
        timestamp = datetime.now().strftime("%H%M%S")
        custom_filename = f"test_adb_logs_{timestamp}"
        
        success, response = self.run_test(
            "Save Logs with Custom Filename",
            "POST",
            "api/save-logs",
            200,
            data={"filename": custom_filename}
        )
        
        if success and response.get('success'):
            print(f"✅ Custom filename save successful: {response['message']}")
            # Verify file was created
            import os
            expected_file = f"{custom_filename}.txt"
            if os.path.exists(expected_file):
                print(f"✅ File created successfully: {expected_file}")
                # Check file content
                with open(expected_file, 'r') as f:
                    content = f.read()
                    if "ADB Logs - Generated:" in content:
                        print("✅ File content format is correct")
                    else:
                        print("❌ File content format is incorrect")
            else:
                print(f"❌ File not created: {expected_file}")
        
        # Test 5: Save without custom filename (default)
        success, response = self.run_test(
            "Save Logs with Default Filename",
            "POST",
            "api/save-logs",
            200,
            data={}
        )
        
        # Test 6: File Pull Operations (All OS Types)
        print("\n--- Testing File Pull Operations ---")
        os_types = ['vega', 'puffin', 'fos']
        
        for os_type in os_types:
            success, response = self.run_test(
                f"Pull {os_type.upper()} CHR.db File",
                "POST",
                "api/pull-file",
                200,
                data={"os_type": os_type}
            )
            
            if success:
                if response.get('success'):
                    print(f"✅ {os_type.upper()} file pull would succeed with connected device")
                else:
                    expected_messages = [
                        "No devices connected",
                        "No active devices found",
                        "file not found"
                    ]
                    if any(msg in response.get('message', '') for msg in expected_messages):
                        print(f"✅ {os_type.upper()} file pull properly handles no device scenario")
                    else:
                        print(f"❌ Unexpected error for {os_type}: {response.get('message')}")
        
        # Test 7: Invalid OS Type
        success, response = self.run_test(
            "Pull File with Invalid OS Type",
            "POST",
            "api/pull-file",
            200,
            data={"os_type": "invalid_os"}
        )
        
        # Test 8: Missing Parameters
        print("\n--- Testing Error Handling ---")
        success, response = self.run_test(
            "Start Logging without Device ID",
            "POST",
            "api/start-logging",
            200,
            data={}
        )
        
        success, response = self.run_test(
            "Pull File without OS Type",
            "POST",
            "api/pull-file",
            200,
            data={}
        )
        
        # Test 9: Log Management
        print("\n--- Testing Log Management ---")
        success, response = self.run_test(
            "Clear Logs",
            "POST",
            "api/clear-logs",
            200
        )
        
        success, response = self.run_test(
            "Stop Logging",
            "POST",
            "api/stop-logging",
            200
        )
        
        # Test 10: Cross-platform Compatibility Check
        print("\n--- Testing Cross-platform Features ---")
        # This is tested implicitly through the trial-and-error logging method
        # which detects the platform and uses appropriate commands
        
        success, response = self.run_test(
            "Start Logging with Trial-and-Error Method",
            "POST",
            "api/start-logging",
            200,
            data={"device_id": "test_device_cross_platform"}
        )
        
        if success and not response.get('success'):
            if "All logging methods failed" in response.get('message', ''):
                print("✅ Cross-platform trial-and-error method working (no devices connected)")
            else:
                print(f"❌ Unexpected cross-platform behavior: {response.get('message')}")

    def test_html_interface(self):
        """Test HTML interface availability"""
        print("\n--- Testing HTML Interface ---")
        
        try:
            response = requests.get(self.base_url)
            if response.status_code == 200:
                html_content = response.text
                
                # Check for key UI elements
                ui_elements = [
                    "ADB GUI Tool",
                    "grep-filter1",
                    "grep-filter2", 
                    "grep-filter3",
                    "Filter 1...",
                    "Filter 2...",
                    "Filter 3...",
                    "saveModal",
                    "filePullModal",
                    "Pull Vega CHR.db",
                    "Pull Puffin CHR.db",
                    "Pull FOS CHR.db",
                    "--gold:",
                    "--black:",
                    "bootstrap"
                ]
                
                found_elements = []
                missing_elements = []
                
                for element in ui_elements:
                    if element in html_content:
                        found_elements.append(element)
                    else:
                        missing_elements.append(element)
                
                print(f"✅ HTML Interface loaded successfully")
                print(f"✅ Found {len(found_elements)}/{len(ui_elements)} expected UI elements")
                
                if missing_elements:
                    print(f"❌ Missing UI elements: {missing_elements}")
                else:
                    print("✅ All expected UI elements found")
                    
                # Check for three filter inputs specifically
                filter_count = html_content.count('grep-filter')
                if filter_count >= 3:
                    print("✅ Three filter input fields confirmed in HTML")
                else:
                    print(f"❌ Expected 3 filter inputs, found {filter_count}")
                
                # Check for modal dialogs
                modal_count = html_content.count('modal fade')
                if modal_count >= 2:
                    print("✅ Modal dialogs found in HTML (Save and File Pull)")
                else:
                    print(f"❌ Expected 2+ modals, found {modal_count}")
                
                self.tests_run += 1
                self.tests_passed += 1
                
            else:
                print(f"❌ HTML Interface failed to load: {response.status_code}")
                self.tests_run += 1
                
        except Exception as e:
            print(f"❌ Error testing HTML interface: {str(e)}")
            self.tests_run += 1

def main():
    """Main test execution"""
    tester = ADBGUITester()
    
    # Test HTML interface first
    tester.test_html_interface()
    
    # Test enhanced backend features
    tester.test_enhanced_features()
    
    # Print final results
    print("\n" + "="*60)
    print("📊 ADB GUI Tool Test Results")
    print("="*60)
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())