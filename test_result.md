#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
## user_problem_statement: {problem_statement}
## backend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.py"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## frontend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.js"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 0
##   run_ui: false
##
## test_plan:
##   current_focus:
##     - "Task name 1"
##     - "Task name 2"
##   stuck_tasks:
##     - "Task name with persistent issues"
##   test_all: false
##   test_priority: "high_first"  # or "sequential" or "stuck_first"
##
## agent_communication:
##     -agent: "main"  # or "testing" or "user"
##     -message: "Communication message between agents"

# Protocol Guidelines for Main agent
#
# 1. Update Test Result File Before Testing:
#    - Main agent must always update the `test_result.md` file before calling the testing agent
#    - Add implementation details to the status_history
#    - Set `needs_retesting` to true for tasks that need testing
#    - Update the `test_plan` section to guide testing priorities
#    - Add a message to `agent_communication` explaining what you've done
#
# 2. Incorporate User Feedback:
#    - When a user provides feedback that something is or isn't working, add this information to the relevant task's status_history
#    - Update the working status based on user feedback
#    - If a user reports an issue with a task that was marked as working, increment the stuck_count
#    - Whenever user reports issue in the app, if we have testing agent and task_result.md file so find the appropriate task for that and append in status_history of that task to contain the user concern and problem as well 
#
# 3. Track Stuck Tasks:
#    - Monitor which tasks have high stuck_count values or where you are fixing same issue again and again, analyze that when you read task_result.md
#    - For persistent issues, use websearch tool to find solutions
#    - Pay special attention to tasks in the stuck_tasks list
#    - When you fix an issue with a stuck task, don't reset the stuck_count until the testing agent confirms it's working
#
# 4. Provide Context to Testing Agent:
#    - When calling the testing agent, provide clear instructions about:
#      - Which tasks need testing (reference the test_plan)
#      - Any authentication details or configuration needed
#      - Specific test scenarios to focus on
#      - Any known issues or edge cases to verify
#
# 5. Call the testing agent with specific instructions referring to test_result.md
#
# IMPORTANT: Main agent must ALWAYS update test_result.md BEFORE calling the testing agent, as it relies on this file to understand what to test next.

#====================================================================================================
# END - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================



#====================================================================================================
# Testing Data - Main Agent and testing sub agent both should log testing data below this section
#====================================================================================================

user_problem_statement: |
  Complete comprehensive rewrite of ADB GUI logging system to ensure robust Windows and Mac compatibility,
  particularly for FOS and Vega device log fetching. Key requirements:
  - Python-side filtering (no shell pipes with grep/findstr)
  - Aggressive cleanup using psutil for process management
  - Longer detection periods (30 seconds) for reliable device type detection
  - Proper thread management with daemon threads
  - Buffer clearing and state reset on every start/stop
  - Device-side cleanup with pkill commands
  - ADB server restart cycle (kill-server/start-server)
  - Works robustly on both Windows and Mac for FOS and Vega devices

backend:
  - task: "Unified start_logging method"
    implemented: true
    working: "NA"  # Needs testing
    file: "/app/adb_gui.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Created unified start_logging() method that delegates to start_logging_robust() for consistent entry point"
        
  - task: "Python-side log filtering"
    implemented: true
    working: "NA"  # Needs testing
    file: "/app/adb_gui.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          Implemented _read_logs_with_python_filtering() method that:
          - Runs raw 'adb shell logcat' or 'journalctl -f' without shell pipes
          - Filters logs line-by-line in Python using regex patterns
          - Matches base patterns (CosineSimilarityCache, eventType=Speech, RESULT_GENERATOR, onCacheUpdate)
          - Applies user filters on top of base patterns
          - Works identically on Windows and Mac
          
  - task: "Aggressive cleanup mechanism"
    implemented: true
    working: "NA"  # Needs testing
    file: "/app/adb_gui.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          Implemented aggressive_cleanup() method with:
          - Python process termination using psutil for process tree cleanup
          - Device-side pkill for logcat/journalctl processes
          - ADB server kill-server/start-server cycle
          - Thread cleanup with proper join
          - Buffer clearing for fresh start
          - State variable reset
          - Stabilization delays between operations
          
  - task: "Extended device detection (30s trial period)"
    implemented: true
    working: "NA"  # Needs testing
    file: "/app/adb_gui.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "start_logging_robust() now tests each log method for 30 seconds (increased from 5s) to ensure reliable FOS/Vega detection"
        
  - task: "Device connectivity validation"
    implemented: true
    working: "NA"  # Needs testing
    file: "/app/adb_gui.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Added test_device_connectivity() method with 3 retry attempts using 'adb shell getprop' to validate connection before starting logs"
        
  - task: "Code cleanup - remove duplicate methods"
    implemented: true
    working: true
    file: "/app/adb_gui.py"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
      - working: true
        agent: "main"
        comment: |
          Cleaned up adb_gui.py by removing:
          - Duplicate stop_logging() method (old approach)
          - Old _start_logging_unix() method (shell-pipe approach)
          - Old _read_logs_windows() method (file-based with findstr)
          - Old _read_logs_windows_direct() method
          - Old _read_logs_unix() method (pipe-based with grep)
          Reduced file from ~1878 to 1477 lines. Syntax validated successfully.

metadata:
  created_by: "main_agent"
  version: "1.0"
  test_sequence: 0
  run_ui: false

test_plan:
  current_focus:
    - "Python-side log filtering"
    - "Aggressive cleanup mechanism"
    - "Extended device detection (30s trial period)"
    - "Device connectivity validation"
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication:
  - agent: "main"
    message: |
      Completed comprehensive rewrite of logging system. Key changes:
      1. Unified Python-side filtering for both Windows and Mac (no more shell pipes)
      2. Aggressive cleanup with psutil for robust restart capability
      3. Extended 30-second detection period for reliable FOS/Vega identification
      4. Device connectivity validation before starting logs
      5. Removed all old/duplicate methods for cleaner codebase
      
      Ready for testing on both Windows and Mac with FOS and Vega devices.
      Test scenarios needed:
      - Windows + FOS device (logcat)
      - Windows + Vega device (journalctl)
      - Mac + FOS device (logcat)
      - Mac + Vega device (journalctl)
      - Stop/Start logging multiple times to verify cleanup
      - Apply user filters and verify case-insensitive matching