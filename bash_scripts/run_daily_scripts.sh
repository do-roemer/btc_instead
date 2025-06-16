#!/bin/bash

# --- Configuration ---
# Exit immediately if a command exits with a non-zero status.
set -e

# Define paths
HOME_DIR="/root"
PROJECT_DIR="$HOME_DIR/code_repository/btc_instead"
# Point directly to the Python executable in the venv
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"
SCRIPT_PATH="$PROJECT_DIR/server_scripts/execute_daily_pipelines.py"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/daily_pipelines.log"

# --- Pre-run Setup ---
# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Change to the project's root directory. All subsequent commands run from here.
# set -e will handle the error if this fails.
cd "$PROJECT_DIR"

# --- Execution & Logging ---
# Use a block to redirect all output to the log file at once.
{
    echo "----------------------------------------"
    echo "Job started at: $(date)"
    echo "Running as user: $(whoami) in directory: $(pwd)"
    
    # Check if the venv Python exists
    if [ ! -f "$VENV_PYTHON" ]; then
        echo "ERROR: Virtual environment Python not found at $VENV_PYTHON"
        exit 1
    fi
    
    echo "Executing script: $SCRIPT_PATH with interpreter $VENV_PYTHON"
    
    # Execute the Python script using the venv's interpreter
    # The '2>&1' ensures that Python errors (stderr) are also logged.
    "$VENV_PYTHON" "$SCRIPT_PATH"
    
    # The exit code will be captured by the 'set -e' and the final 'exit 0'
    
    echo "Job finished successfully at: $(date)"
    echo ""

} >> "$LOG_FILE" 2>&1

# If we get here, it means all commands succeeded due to 'set -e'
echo "Daily script executed successfully. See log for details: $LOG_FILE"
exit 0