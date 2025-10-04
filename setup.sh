#!/bin/bash

# BloomWatch Setup Script
# NASA Space Apps Challenge 2025

echo "🌸 =============================================="
echo "   BloomWatch - NASA Bloom Monitoring Tool"
echo "   Setup Script"
echo "=============================================="
echo ""

# Check Python version
echo "📋 Checking Python version..."
python3 --version

if [ $? -ne 0 ]; then
    echo "❌ Error: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Create virtual environment
echo ""
echo "🔧 Creating virtual environment..."
python3 -m venv venv

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to create virtual environment"
    exit 1
fi

# Activate virtual environment
echo "✅ Virtual environment created"
echo ""
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "📦 Installing dependencies (this may take a few minutes)..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "⚠️  Warning: Some packages failed to install"
    echo "You may need to install system dependencies"
    echo ""
    echo "On Ubuntu/Debian:"
    echo "  sudo apt-get install gdal-bin libgdal-dev python3-dev"
    echo ""
    echo "On macOS:"
    echo "  brew install gdal"
    echo ""
fi

# Create necessary directories
echo ""
echo "📁 Creating project directories..."
mkdir -p data/cache
mkdir -p data/downloads
mkdir -p data/processed
mkdir -p logs

# Copy environment file
echo ""
echo "⚙️  Setting up environment configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env file"
    echo "⚠️  Please edit .env and add your NASA Earthdata credentials"
else
    echo "ℹ️  .env file already exists"
fi

# Create cache directory
echo ""
echo "💾 Setting up cache directory..."
mkdir -p ~/.config/earthdata
echo "✅ Cache directory created"

# Summary
echo ""
echo "🎉 =============================================="
echo "   Setup Complete!"
echo "=============================================="
echo ""
echo "📝 Next Steps:"
echo ""
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Configure NASA Earthdata credentials:"
echo "   - Register at: https://urs.earthdata.nasa.gov/"
echo "   - Edit .env file and add your credentials"
echo ""
echo "3. Run the application:"
echo "   Option A: Backend API"
echo "     cd backend && python app.py"
echo ""
echo "   Option B: Jupyter Notebook"
echo "     jupyter notebook notebooks/bloom_analysis.ipynb"
echo ""
echo "   Option C: Web Interface"
echo "     Open frontend/index.html in your browser"
echo ""
echo "4. Test with demo mode (no credentials needed):"
echo "   The system will automatically use demo data if"
echo "   NASA credentials are not configured"
echo ""
echo "📚 Documentation:"
echo "   - Quick Start: QUICKSTART.md"
echo "   - Full README: README.md"
echo "   - Contributing: CONTRIBUTING.md"
echo ""
echo "🆘 Need Help?"
echo "   - Check QUICKSTART.md for troubleshooting"
echo "   - Visit NASA Earthdata: https://earthdata.nasa.gov/"
echo ""
echo "Happy bloom watching! 🌸🛰️"
echo ""
