#!/bin/bash
# Build script for PE Memory OS macOS App (Launcher version)
# This creates a lightweight launcher app that starts the local Python environment.

set -e

echo "Building PE Memory OS macOS App (Launcher version)..."

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if we're in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
    else
        echo "Error: Virtual environment not found at .venv/"
        echo "Please create one: python -m venv .venv"
        exit 1
    fi
fi

# Check PyInstaller
if ! command -v pyinstaller &> /dev/null; then
    echo "Installing PyInstaller..."
    pip install pyinstaller
fi

# Build frontend
echo "Building frontend..."
npm run build

# Clean previous builds
rm -rf dist build_app

echo "Running PyInstaller (launcher-only)..."
pyinstaller PE_Memory_OS_Launcher.spec --clean --noconfirm

# Set up the app bundle
APP_NAME="PE Memory OS"
APP_BUNDLE="dist/${APP_NAME}.app"
CONTENTS_DIR="${APP_BUNDLE}/Contents"
RESOURCES_DIR="${CONTENTS_DIR}/Resources"
MACOS_DIR="${CONTENTS_DIR}/MacOS"

if [ ! -d "$APP_BUNDLE" ]; then
    echo "Error: App bundle not created"
    exit 1
fi

echo "Setting up app bundle..."

# Create Resources directory if it doesn't exist
mkdir -p "$RESOURCES_DIR"

# Copy backend code to Resources (so launcher can find it)
cp -r backend "$RESOURCES_DIR/"
cp requirements.txt "$RESOURCES_DIR/" 2>/dev/null || true

# Create a README for the user
cat > "$RESOURCES_DIR/README.txt" << 'EOF'
PE Memory OS
============

This is a launcher app for PE Memory OS.

First-time setup:
1. Ensure Python 3.10+ is installed
2. Create a virtual environment in the project folder:
   python -m venv .venv
3. Install dependencies:
   pip install -r requirements.txt

The app will automatically use the virtual environment at:
   <project_folder>/.venv

Your data is stored in:
   ~/Library/Application Support/PE Memory OS/
EOF

# Ensure the executable has correct permissions
chmod +x "$MACOS_DIR/"*

echo "App bundle created successfully!"
echo ""
echo "Location: $(pwd)/$APP_BUNDLE"
echo ""
echo "IMPORTANT: Before running the app:"
echo "1. Ensure you have a Python virtual environment at .venv/"
echo "2. Install dependencies: pip install -r requirements.txt"
echo ""
echo "To run:"
echo "  open '$APP_BUNDLE'"
echo ""
echo "Or to see debug output:"
echo "  '$APP_BUNDLE/Contents/MacOS/$APP_NAME'"
