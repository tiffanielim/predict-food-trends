#!/bin/bash

# Food Trend Predictor - Complete Pipeline Runner
# This script runs the entire pipeline from data collection to dashboard

set -e  # Exit on error

echo "========================================"
echo "🍕 Food Trend Predictor Pipeline"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if .env exists
if [ ! -f .env ]; then
    print_error ".env file not found"
    echo "Run: cp .env.example .env and configure your credentials"
    exit 1
fi

# Default values
NUM_POSTS=${1:-10000}
SKIP_COLLECTION=${2:-false}
SKIP_TRAINING=${3:-false}

print_status "Pipeline Configuration:"
echo "  - Posts to collect: $NUM_POSTS"
echo "  - Skip collection: $SKIP_COLLECTION"
echo "  - Skip training: $SKIP_TRAINING"
echo ""

# Step 1: Data Collection
if [ "$SKIP_COLLECTION" != "true" ]; then
    print_status "Step 1/4: Collecting Reddit posts..."
    python etl.py collect $NUM_POSTS
    
    if [ $? -eq 0 ]; then
        print_status "✅ Data collection complete"
    else
        print_error "Data collection failed"
        exit 1
    fi
else
    print_warning "Skipping data collection"
fi

echo ""

# Step 2: Data Processing & Model Training
if [ "$SKIP_TRAINING" != "true" ]; then
    print_status "Step 2/4: Training ML model..."
    python model.py
    
    if [ $? -eq 0 ]; then
        print_status "✅ Model training complete"
    else
        print_error "Model training failed"
        exit 1
    fi
else
    print_warning "Skipping model training"
fi

echo ""

# Step 3: Generate Predictions
print_status "Step 3/4: Generating predictions..."
python predict_service.py report

if [ $? -eq 0 ]; then
    print_status "✅ Predictions generated"
else
    print_warning "Prediction generation had issues (non-critical)"
fi

echo ""

# Step 4: Launch Dashboard
print_status "Step 4/4: Launching dashboard..."
print_status "Dashboard will be available at: http://localhost:8501"
print_status "Press Ctrl+C to stop"
echo ""

streamlit run dashboard.py

# Note: This won't execute unless streamlit is stopped
print_status "Pipeline complete!"
