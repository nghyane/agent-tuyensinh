#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Set PYTHONPATH to include src directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

export $(cat .env | grep -v '^#' | xargs)

echo "✅ Environment activated!"
echo "✅ PYTHONPATH set to: $PYTHONPATH"
echo "✅ Ready to run the project!" 