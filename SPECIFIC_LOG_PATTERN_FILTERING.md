# ADB GUI Tool - Specific Log Pattern Filtering Update

## Enhanced Log Filtering Implementation

The ADB GUI Tool now includes specific log pattern filtering as requested, with cross-platform compatibility for Windows (findstr) and Mac/Linux (grep).

### New Log Commands Implemented

#### FOS Devices
```bash
# Mac/Linux
adb -s {device_id} shell "logcat | grep -iE 'CosineSimilarityCache::LookupImpl|eventType=Speech|RESULT_GENERATOR|Calling onCacheUpdate'"

# Windows  
adb.exe -s {device_id} shell "logcat | findstr /I /C:\"CosineSimilarityCache::LookupImpl\" /C:\"eventType=Speech\" /C:\"RESULT_GENERATOR\" /C:\"Calling onCacheUpdate\""
```

#### Vega Devices
```bash
# Mac/Linux
adb -s {device_id} shell "journalctl -f | grep -iE 'CosineSimilarityCache::LookupImpl|eventType=Speech|RESULT_GENERATOR|Calling onCacheUpdate'"

# Windows
adb.exe -s {device_id} shell "journalctl -f | findstr /I /C:\"CosineSimilarityCache::LookupImpl\" /C:\"eventType=Speech\" /C:\"RESULT_GENERATOR\" /C:\"Calling onCacheUpdate\""
```

### Target Log Patterns

The tool now specifically filters for these patterns:
1. **CosineSimilarityCache::LookupImpl** - Cache lookup operations
2. **eventType=Speech** - Speech-related events  
3. **RESULT_GENERATOR** - Result generation processes
4. **Calling onCacheUpdate** - Cache update notifications

### Two-Layer Filtering System

#### Layer 1: Base ADB Filtering (Hardware Level)
- Built into the ADB shell command
- Filters at device level before transmission
- Platform-specific (grep vs findstr)
- Always active when logging starts

#### Layer 2: User Filtering (UI Level)  
- Additional 3 filter inputs in the UI
- Applied on top of base filtering
- User-controlled via "Apply" button
- Filters the already-filtered base logs

### Cross-Platform Implementation

#### Windows (findstr)
```python
# Windows syntax for multiple pattern matching
filter_args = '/I /C:"CosineSimilarityCache::LookupImpl" /C:"eventType=Speech" /C:"RESULT_GENERATOR" /C:"Calling onCacheUpdate"'
```

#### Mac/Linux (grep)
```python  
# Unix syntax for extended regex pattern matching
filter_args = '-iE "CosineSimilarityCache::LookupImpl|eventType=Speech|RESULT_GENERATOR|Calling onCacheUpdate"'
```

### Enhanced Features

#### Intelligent Log Detection
- Tests both FOS and Vega methods with specific patterns
- Shows sample log entries when patterns are detected
- Provides detailed feedback about pattern matching

#### Better User Feedback
- Shows which platform and filter command is being used
- Lists target patterns in startup message
- Reports when waiting for matching patterns
- Clear error messages when no patterns match

#### Improved Performance  
- Filters at device level reduce network traffic
- Only relevant logs are transmitted and stored
- More efficient than client-side filtering

### Usage Instructions

1. **Start Tool**: Run `python adb_gui.py`
2. **Connect Device**: USB connection with debugging enabled
3. **Select Device**: Choose from dropdown in UI
4. **Start Logging**: Click "Start" - automatically detects FOS/Vega and applies base pattern filtering
5. **Add User Filters**: Enter additional keywords in 3 filter inputs (optional)
6. **Apply Filters**: Click "Apply" to activate user filters
7. **View Results**: 
   - **All Logs Tab**: Shows base pattern-filtered logs
   - **Filtered Logs Tab**: Shows user-filtered subset of base logs

### Technical Implementation Details

#### Enhanced Start Logging Process
```python
def start_logging(self, device_id):
    # Determine platform-specific commands
    adb_cmd = 'adb.exe' if windows else 'adb'  
    grep_cmd = 'findstr' if windows else 'grep'
    
    # Create filtered commands for each device type
    fos_cmd = f'{adb_cmd} -s {device_id} shell "logcat | {grep_cmd} {filter_args}"'
    vega_cmd = f'{adb_cmd} -s {device_id} shell "journalctl -f | {grep_cmd} {filter_args}"'
    
    # Test both methods, use the one that works
    for method in [fos_cmd, vega_cmd]:
        if test_log_availability(method):
            start_log_capture(method)
            return success
```

#### Windows File-Based Capture
```python
def _read_logs_windows(self):
    # Use the detected filtered command with file redirection
    cmd = f'{detected_method_command} > "{temp_log_file}"'
    
    # Tail file for new filtered content  
    while logging_active:
        new_content = read_new_file_content()
        apply_user_filters(new_content)  # Second layer filtering
```

#### Unix Pipe-Based Capture  
```python
def _read_logs_unix(self):
    # Direct pipe from filtered ADB command
    while logging_active:
        line = log_process.stdout.readline()  # Already base-filtered
        apply_user_filters(line)  # Second layer filtering  
```

### Troubleshooting

#### No Logs Appearing
- **Cause**: Target applications not generating the specific patterns
- **Solution**: Verify applications are running and generating speech/cache events

#### Windows findstr Issues
- **Cause**: Complex pattern syntax differences
- **Solution**: Tool automatically handles Windows vs Unix syntax differences

#### Empty Filtered Logs
- **Cause**: No logs match both base patterns AND user filters
- **Solution**: Remove user filters to see base pattern-filtered logs only

### Performance Benefits

1. **Reduced Network Traffic**: Filtering at device level
2. **Lower Memory Usage**: Only relevant logs stored  
3. **Faster UI Updates**: Less data to process and display
4. **Targeted Debugging**: Focus on specific application behaviors

The tool now provides highly targeted log filtering specifically designed for debugging speech recognition, cache operations, and result generation processes across different device types and operating systems.