#!/bin/bash
# Setup script for FAEN API client

set -e

echo "🔧 Setting up FAEN API client environment..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Verify installation
echo "✅ Verifying installation..."
python -c "import console_utils, faen_client, cde_client, data_utils; print('✓ All modules imported successfully')"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To use the FAEN client:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Copy and configure your .env file: cp env.template .env"
echo "3. Run the client: python faen_consumption_client.py"
echo ""