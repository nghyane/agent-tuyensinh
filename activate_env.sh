#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Set PYTHONPATH to include src directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Export environment variables from .env if it exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | grep -v '^$' | xargs)
    echo "✅ Environment variables loaded from .env"
else
    echo "⚠️  No .env file found, using system environment"
fi

echo "✅ Environment activated!"
echo "✅ PYTHONPATH set to: $PYTHONPATH"
echo "✅ Ready to run the project!" 