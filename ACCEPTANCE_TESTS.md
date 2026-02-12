# ADB GUI Tool - Acceptance Tests

## Prerequisites
- ADB installed and in PATH
- USB debugging enabled on test devices
- Devices authorized for ADB connection
- Python 3.7+ with Flask and psutil installed

## Test Environment Setup

### 1. Install Dependencies
```bash
pip install -r requirements_adb_gui.txt
```

### 2. Start ADB GUI Tool
```bash
python3 adb_gui.py
```

### 3. Note the Port
The tool will display:
```
🌐 Access the GUI at: http://localhost:<PORT>
```

## Automated Tests (No Device Required)

### Run Test Suite
```bash
# Update BASE_URL in test_adb_gui.py if needed
python3 test_adb_gui.py
```

**Expected**: All tests pass, demonstrating:
- API endpoints work
- Error handling is graceful
- Repeated start/stop cycles don't crash
- Invalid inputs are rejected properly

## Manual Acceptance Tests (Device Required)

### Test 1: Windows + FOS Device Detection

**Setup**: 
- Windows machine
- FOS device connected via USB

**Steps**:
1. Start `adb_gui.py`
2. Open browser to `http://localhost:<PORT>`
3. Click "Refresh" in Connected Devices section
4. Verify FOS device appears in list

**Expected**: Device shows as "online" with serial number

**Pass Criteria**: ✅ Device detected within 5 seconds

---

### Test 2: Windows + FOS Logging (30s Detection)

**Setup**: Same as Test 1

**Steps**:
1. Select FOS device from dropdown
2. Click "Start" button
3. Wait up to 30 seconds for detection
4. Observe "All Logs" tab

**Expected**:
- Detection message: "✅ Auto-detected: FOS"
- Logs appear with timestamps
- Base patterns (CosineSimilarityCache, eventType=Speech, etc.) are present

**Pass Criteria**: ✅ Logs streaming within 30 seconds

---

### Test 3: Windows + FOS Stop/Start Cycles

**Setup**: Same as Test 1, with logging active

**Steps**:
1. Click "Stop" button
2. Wait 3 seconds
3. Click "Start" button
4. Repeat 10 times

**Expected**:
- Each stop completes within 5 seconds
- Each start succeeds within 30 seconds
- No error messages about orphaned processes
- `logfetcher_debug.log` shows clean cleanup cycles

**Pass Criteria**: ✅ All 10 cycles complete without errors

---

### Test 4: Mac + Vega Device Detection

**Setup**:
- Mac machine
- Vega device connected via USB

**Steps**:
1. Start `adb_gui.py`
2. Open browser
3. Click "Refresh"
4. Verify Vega device appears

**Expected**: Device shows as "online"

**Pass Criteria**: ✅ Device detected within 5 seconds

---

### Test 5: Mac + Vega Logging (journalctl)

**Setup**: Same as Test 4

**Steps**:
1. Select Vega device
2. Click "Start"
3. Wait up to 30 seconds
4. Observe logs

**Expected**:
- Detection message: "✅ Auto-detected: VEGA"
- journalctl logs appear
- Timestamps present

**Pass Criteria**: ✅ Logs streaming within 30 seconds

---

### Test 6: User Filters (Case-Insensitive)

**Setup**: Any device with active logging

**Steps**:
1. Enter "ERROR" in Filter 1
2. Enter "warning" in Filter 2  
3. Click "Apply"
4. Switch to "Filtered Logs" tab
5. Observe output

**Expected**:
- Only lines containing "error" or "warning" (case-insensitive) appear
- All Logs tab still shows all base-pattern matches
- Filter indicator shows: "Active Filters: ERROR, warning"

**Pass Criteria**: ✅ Filtering works case-insensitively

---

### Test 7: Fallback Mode (Detection Failure)

**Setup**: Device that doesn't generate logs immediately

**Steps**:
1. Start logging on device
2. Wait 60+ seconds (past detection period)
3. Observe messages

**Expected**:
- After 60s: "[WARN] Detection failed for both methods"
- Message: "Entering RAW FALLBACK MODE with logcat"
- All logs shown without pattern filtering
- Detection verdict: "⚠️ Fallback Mode: logcat (no pattern filtering)"

**Pass Criteria**: ✅ Fallback mode activates and shows all logs

---

### Test 8: Device Disconnect During Logging

**Setup**: Any device with active logging

**Steps**:
1. Start logging successfully
2. Physically disconnect USB cable
3. Observe UI and logs

**Expected**:
- Error message: "[ERROR] Device <SERIAL> disconnected!"
- Logging stops gracefully
- No crash or hang
- Debug log shows disconnect detection

**Pass Criteria**: ✅ Graceful handling of disconnect

---

### Test 9: File Pull - FOS CHR.db

**Setup**: FOS device connected

**Steps**:
1. Click "Pull FOS CHR.db" button
2. Wait for response
3. Check current directory

**Expected**:
- Success popup: "✅ Successfully pulled FOS CHR.db..."
- File exists: `CHR_fos_<timestamp>.db`
- File size > 0 bytes

**Pass Criteria**: ✅ File pulled successfully with retries (check debug log)

---

### Test 10: File Pull - Vega CHR.db

**Setup**: Vega device connected

**Steps**:
1. Click "Pull Vega CHR.db" button
2. Wait for response
3. Check directory

**Expected**:
- Success popup with file path
- File exists and has content

**Pass Criteria**: ✅ File pulled successfully

---

### Test 11: Save Logs with Custom Filename

**Setup**: Any device with active logging and logs captured

**Steps**:
1. Click "Save" button
2. Enter custom filename: "my_test_logs"
3. Click "Save"
4. Check directory

**Expected**:
- Success message: "✅ X log entries saved to my_test_logs.txt..."
- File exists and contains logs
- File has header with timestamp and platform info

**Pass Criteria**: ✅ Logs saved successfully

---

### Test 12: Memory Stability (Long Run)

**Setup**: Any device

**Steps**:
1. Start logging
2. Let run for 60 minutes
3. Monitor memory usage (Task Manager / Activity Monitor)
4. Check log buffer size in debug log

**Expected**:
- Memory usage stays below 200MB
- Buffer capped at 2000 lines
- No memory leaks
- Process remains responsive

**Pass Criteria**: ✅ Memory stable, no leaks

---

### Test 13: Cleanup Verification (Process Check)

**Setup**: Any device

**Steps**:
1. Start logging (note process IDs from debug log)
2. Click "Stop"
3. Check running processes:
   - Windows: `tasklist | findstr adb`
   - Mac: `ps aux | grep adb`
4. Check device processes:
   - `adb shell ps | grep logcat`
   - `adb shell ps | grep journalctl`

**Expected**:
- No orphaned `adb` processes on host
- No orphaned `logcat` or `journalctl` on device
- Debug log shows "AGGRESSIVE CLEANUP COMPLETE"

**Pass Criteria**: ✅ All processes cleaned up

---

### Test 14: ADB Server Reset Verification

**Setup**: Any device, logging active

**Steps**:
1. Start logging
2. Stop logging
3. Check debug log for "Resetting ADB server"
4. Check debug log for "ADB server reset complete"
5. Run `adb devices` from terminal

**Expected**:
- ADB server restarted during cleanup
- `adb devices` responds normally
- No "server out of date" errors

**Pass Criteria**: ✅ ADB server healthy after cleanup

---

### Test 15: Cross-Platform Consistency

**Setup**: Same device tested on both Windows and Mac

**Steps**:
1. Test on Windows: Start logging, verify logs appear
2. Test on Mac: Start logging, verify logs appear
3. Compare log output and behavior

**Expected**:
- Both platforms detect device correctly
- Both show similar log output
- Both handle start/stop cycles cleanly
- UI behavior is identical

**Pass Criteria**: ✅ Consistent behavior across platforms

---

## Performance Acceptance Criteria

| Metric | Target | Test Method |
|--------|--------|-------------|
| Device detection | < 5s | Time from page load to device list populated |
| Log detection (success) | < 30s | Time from "Start" to first log appearing |
| Stop cleanup | < 5s | Time from "Stop" click to "stopped successfully" message |
| Memory usage | < 200MB | Monitor during 60min run |
| CPU usage (idle logging) | < 5% | Monitor during active logging with low log rate |
| Buffer size | Max 2000 lines | Check log_buffer length in debug log |

## Debugging Failed Tests

### Check Debug Log
```bash
tail -f logfetcher_debug.log
```

### Common Issues

**Detection Fails**:
- Check device is generating logs (test with `adb logcat` or `adb shell journalctl -f`)
- Verify base patterns are present in device output
- Check debug log for "Detection attempt X/2" messages

**Cleanup Hangs**:
- Check debug log for process termination messages
- Verify psutil is installed
- Check for permission issues on Windows

**Orphaned Processes**:
- Run `adb kill-server && adb start-server`
- Check device-side processes with `adb shell ps`

## Reporting Results

For each test, record:
- ✅ PASS or ❌ FAIL
- Platform (Windows/Mac/Linux)
- Device type (FOS/Vega/Puffin)
- Any error messages
- Relevant debug log excerpts

## Success Criteria Summary

**Must Pass All**:
- Tests 1-6 (basic functionality)
- Test 9 or 10 (file pull for at least one OS type)
- Test 13 (cleanup verification)

**Should Pass**:
- Tests 7-8 (error handling)
- Tests 11-12 (stability)
- Test 14-15 (cross-platform)

**Total**: 13/15 tests passing = PASS
