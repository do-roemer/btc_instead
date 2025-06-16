#!/bin/bash

# Define paths (makes it easier to manage)
HOME_DIR="/root"
PROJECT_DIR="$HOME_DIR/code_repository/btc_instead"
VENV_PATH="$PROJECT_DIR/.venv/bin/activate"
SCRIPT_PATH="$PROJECT_DIR/bash_scripts/execute_weekly_pipelines.py"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$PROJECT_DIR/logs/weekly_pipelines.log" # Ensure 'logs' directory exists


echo "----------------------------------------" >> "$LOG_FILE"
echo "Job started at: $(date)" >> "$LOG_FILE"
echo "Script running as user: $(whoami)" >> "$LOG_FILE" # Should show 'root'
echo "HOME_DIR used in script: $HOME_DIR" >> "$LOG_FILE"
echo "PROJECT_DIR used in script: $PROJECT_DIR" >> "$LOG_FILE"
echo "LOG_DIR used in script: $LOG_DIR" >> "$LOG_FILE"
echo "Current working directory before cd: $(pwd)" >> "$LOG_FILE"

# Activate virtual environment
if [ -f "$VENV_PATH" ]; then
    . "$VENV_PATH" # Note the space after the dot
    echo "Virtual environment activated using: . $VENV_PATH" >> "$LOG_FILE"
else
    echo "ERROR: Virtual environment activate script not found at $VENV_PATH" >> "$LOG_FILE"
    exit 1
fi

# Navigate to the project directory
cd "$PROJECT_DIR"
if [ "$?" -ne 0 ]; then
    echo "ERROR: Failed to cd to $PROJECT_DIR" >> "$LOG_FILE"
    echo "Current working directory after failed cd: $(pwd)" >> "$LOG_FILE"
    exit 1
else
    echo "Successfully changed to directory: $(pwd)" >> "$LOG_FILE"
fi

# Execute the Python script
echo "Attempting to execute Python script: python $SCRIPT_PATH" >> "$LOG_FILE"
python "$SCRIPT_PATH" >> "$LOG_FILE" 2>&1
SCRIPT_EXIT_CODE=$?

echo "Python script finished with exit code: $SCRIPT_EXIT_CODE" >> "$LOG_FILE"
echo "Job finished at: $(date)" >> "$LOG_FILE"

exit $SCRIPT_EXIT_CODE
