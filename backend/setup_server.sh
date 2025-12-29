#!/bin/bash
# ============================================
# Legal-Ops Server Setup Script
# ============================================
# Run this script on your Ubuntu/Debian server before pip install
# Usage: chmod +x setup_server.sh && sudo ./setup_server.sh

set -e  # Exit on error

echo "============================================"
echo "Legal-Ops Server Setup"
echo "============================================"

# Update package list
echo "[1/6] Updating package list..."
apt-get update

# Install Python build dependencies
echo "[2/6] Installing Python build dependencies..."
apt-get install -y \
    python3-dev \
    python3-pip \
    python3-venv \
    build-essential \
    libffi-dev \
    libssl-dev

# Install Tesseract OCR (for pytesseract)
echo "[3/6] Installing Tesseract OCR..."
apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-msa \
    libtesseract-dev

# Install PDF processing dependencies (for pdf2image, PyMuPDF)
echo "[4/6] Installing PDF processing dependencies..."
apt-get install -y \
    poppler-utils \
    libmupdf-dev \
    mupdf-tools

# Install other system dependencies
echo "[5/6] Installing additional dependencies..."
apt-get install -y \
    libpq-dev \
    redis-server \
    libxml2-dev \
    libxslt1-dev

# Download spaCy model
echo "[6/6] Setting up Python environment..."
if [ -d "venv" ]; then
    echo "Virtual environment exists, activating..."
    source venv/bin/activate
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
fi

# Upgrade pip
pip install --upgrade pip

# Install Python requirements
echo "Installing Python requirements..."
pip install -r requirements.txt

# Download spaCy English model
echo "Downloading spaCy English model..."
python -m spacy download en_core_web_sm || echo "Warning: spaCy model download failed, may not be needed"

echo "============================================"
echo "Setup Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "1. Copy your .env file to the backend directory"
echo "2. Run database migrations: alembic upgrade head"
echo "3. Start the server: uvicorn main:app --host 0.0.0.0 --port 8091"
echo ""
