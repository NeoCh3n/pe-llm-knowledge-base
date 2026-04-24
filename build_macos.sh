#!/bin/bash
# Build script for PE Memory OS macOS App

set -e

echo "Building PE Memory OS macOS App..."

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment
source .venv/bin/activate

# Build frontend
echo "Building frontend..."
npm run build

# Create a simple icon if it doesn't exist
if [ ! -f "build/icon.icns" ]; then
    echo "Creating app icon..."
    mkdir -p build/icon.iconset
    # Create a simple colored square as placeholder icon
    for size in 16 32 64 128 256 512; do
        sips -Z $size /System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/GenericDocumentIcon.icns -o "build/icon.iconset/icon_${size}x${size}.png" 2>/dev/null || \
        convert -size ${size}x${size} xc:blue "build/icon.iconset/icon_${size}x${size}.png" 2>/dev/null || \
        echo "<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<svg width=\"${size}\" height=\"${size}\" xmlns=\"http://www.w3.org/2000/svg\">
  <rect width=\"100%\" height=\"100%\" fill=\"%233B82F6\"/>
  <text x=\"50%\" y=\"50%\" dominant-baseline=\"middle\" text-anchor=\"middle\" fill=\"white\" font-size=\"${size%??}\">PE</text>
</svg>" > "build/icon.iconset/icon_${size}x${size}.svg"
    done

    # Try to create icns from iconset
    iconutil -c icns build/icon.iconset -o build/icon.icns 2>/dev/null || echo "Using default icon"
    rm -rf build/icon.iconset
fi

# Clean previous builds
rm -rf dist build_app

echo "Running PyInstaller..."
pyinstaller PE_Memory_OS.spec --clean --noconfirm

# Create final app bundle structure
APP_NAME="PE Memory OS"
APP_BUNDLE="dist/${APP_NAME}.app"

echo "Creating app bundle at: $APP_BUNDLE"

# Ensure the app bundle has correct permissions
if [ -d "$APP_BUNDLE" ]; then
    chmod +x "$APP_BUNDLE/Contents/MacOS/"*
    echo "App bundle created successfully!"
    echo "Location: $(pwd)/$APP_BUNDLE"
    echo ""
    echo "To run:"
    echo "  open '$APP_BUNDLE'"
else
    echo "Error: App bundle not created"
    exit 1
fi
