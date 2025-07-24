#!/bin/bash

# Activate virtual environment
source venv/bin/activate

export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
export $(cat .env | grep -v '^#' | grep -v '^$' | xargs)

