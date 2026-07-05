#!/bin/bash
# DFT Audio Visualizer - PyQt6 Installation Script
# Automates the migration from PyQt5 to PyQt6

set -e  # Exit on error

echo "=================================="
echo "DFT Visualizer Qt6 Installation"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"
echo ""

# Step 1: Uninstall PyQt5
echo -e "${YELLOW}Step 1: Removing PyQt5 (if installed)...${NC}"
pip uninstall PyQt5 PyQt5-sip -y 2>/dev/null || true
echo -e "${GREEN}✓ PyQt5 removal complete${NC}"
echo ""

# Step 2: Install PyQt6 and dependencies
echo -e "${YELLOW}Step 2: Installing PyQt6 and dependencies...${NC}"
pip install -r requirements_qt6.txt
echo -e "${GREEN}✓ PyQt6 and dependencies installed${NC}"
echo ""

# Step 3: Verify installation
echo -e "${YELLOW}Step 3: Verifying installation...${NC}"

# Check PyQt6
if python3 -c "from PyQt6 import QtCore; print('PyQt6 OK')" 2>/dev/null; then
    echo -e "${GREEN}✓ PyQt6 imported successfully${NC}"
else
    echo -e "${RED}✗ Failed to import PyQt6${NC}"
    exit 1
fi

# Check PyQtGraph
if python3 -c "import pyqtgraph; print(f'PyQtGraph {pyqtgraph.__version__} OK')" 2>/dev/null; then
    echo -e "${GREEN}✓ PyQtGraph imported successfully${NC}"
else
    echo -e "${RED}✗ Failed to import PyQtGraph${NC}"
    exit 1
fi

# Check numpy
if python3 -c "import numpy; print(f'NumPy {numpy.__version__} OK')" 2>/dev/null; then
    echo -e "${GREEN}✓ NumPy imported successfully${NC}"
else
    echo -e "${RED}✗ Failed to import NumPy${NC}"
    exit 1
fi

# Check scipy
if python3 -c "import scipy; print(f'SciPy {scipy.__version__} OK')" 2>/dev/null; then
    echo -e "${GREEN}✓ SciPy imported successfully${NC}"
else
    echo -e "${RED}✗ Failed to import SciPy${NC}"
    exit 1
fi

# Check sounddevice
if python3 -c "import sounddevice; print(f'SoundDevice {sounddevice.__version__} OK')" 2>/dev/null; then
    echo -e "${GREEN}✓ SoundDevice imported successfully${NC}"
else
    echo -e "${RED}✗ Failed to import SoundDevice${NC}"
    exit 1
fi

# Check soundfile
if python3 -c "import soundfile; print(f'SoundFile {soundfile.__version__} OK')" 2>/dev/null; then
    echo -e "${GREEN}✓ SoundFile imported successfully${NC}"
else
    echo -e "${RED}✗ Failed to import SoundFile${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}=================================="
echo "Installation Successful! ✓"
echo "==================================${NC}"
echo ""
echo "Next steps:"
echo "1. Run tests: python test_dft_visualizer.py"
echo "2. Start visualizer: python dft_visualizer_production_qt6.py"
echo "3. Read guide: cat QT6_MIGRATION_GUIDE.md"
echo ""
echo "For audio input, ensure:"
echo "- Microphone is connected and enabled"
echo "- Audio drivers are installed"
echo "- No other apps are using the microphone"
echo ""
