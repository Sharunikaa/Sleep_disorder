#!/bin/bash

bash# Startup script for Sleep Disorder FHE Application
# This script uses the correct conda environment

echo "=================================================="
echo "  Sleep Disorder - FHE Prediction System"
echo "=================================================="
echo ""

# Set the correct Python path
PYTHON_PATH="/Users/Sharunikaa/anaconda3/envs/sleep_disorder_env/bin/python"

# Check if Python exists
if [ ! -f "$PYTHON_PATH" ]; then
    echo "Error: Python not found at $PYTHON_PATH"
    echo "Please create the conda environment first:"
    echo "  conda create -n sleep_disorder_env python=3.10"
    echo "  conda activate sleep_disorder_env"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Display Python version
echo "🐍 Using Python:"
$PYTHON_PATH --version
echo ""

# Check dependencies
echo "🔍 Checking dependencies..."
$PYTHON_PATH -c "
import sys
try:
    import flask
    print('  Flask')
except:
    print('  Flask not installed')
    sys.exit(1)

try:
    import pyrebase
    print('  Pyrebase')
except:
    print('  Pyrebase not installed')
    sys.exit(1)

try:
    import concrete.ml
    print('  Concrete-ML')
except:
    print('  Concrete-ML not installed')
    sys.exit(1)

print('  All dependencies OK')
" 2>/dev/null

if [ $? -ne 0 ]; then
    echo ""
    echo "Missing dependencies. Please install:"
    echo "  $PYTHON_PATH -m pip install -r requirements.txt"
    exit 1
fi

echo ""
echo "=================================================="
echo "  Starting Flask Application..."
echo "=================================================="
echo ""
echo "📍 Access the app at: http://127.0.0.1:5000"
echo "📊 Security Audit at: http://127.0.0.1:5000/security_audit"
echo "🔐 Predictions at: http://127.0.0.1:5000/predict"
echo ""
echo "Using REAL FHE (not demo mode)"
echo "Press Ctrl+C to stop the server"
echo ""

# Run the Flask app (REAL FHE VERSION)
$PYTHON_PATH app.py
