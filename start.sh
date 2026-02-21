#!/bin/bash

# Xfce Desktop Environment Startup Script for HuggingFace Spaces

set -e

echo "========================================="
echo "Starting Xfce Desktop Environment"
echo "========================================="

# Set environment variables
export DISPLAY=:1
export VNC_PASSWORD=${VNC_PASSWORD:-huggingface}
export RESOLUTION=${RESOLUTION:-1280x720}

# Function to handle cleanup on exit
cleanup() {
    echo "Cleaning up..."
    pkill -9 Xvfb 2>/dev/null || true
    pkill -9 x11vnc 2>/dev/null || true
    pkill -9 websockify 2>/dev/null || true
    pkill -9 startxfce4 2>/dev/null || true
    exit 0
}

# Set trap for cleanup
trap cleanup SIGINT SIGTERM

# Kill any existing processes
echo "Cleaning up existing processes..."
pkill -9 Xvfb 2>/dev/null || true
pkill -9 x11vnc 2>/dev/null || true
pkill -9 websockify 2>/dev/null || true
pkill -9 startxfce4 2>/dev/null || true
sleep 1

# Start Xvfb (Virtual Framebuffer)
echo "Starting Xvfb..."
Xvfb :1 -screen 0 ${RESOLUTION}x24 -ac +extension GLX &
XVFB_PID=$!
sleep 2

# Verify Xvfb started
if ! kill -0 $XVFB_PID 2>/dev/null; then
    echo "ERROR: Xvfb failed to start"
    exit 1
fi
echo "Xvfb started successfully (PID: $XVFB_PID)"

# Start Xfce4
echo "Starting Xfce4..."
export DISPLAY=:1
startxfce4 &
XFCE_PID=$!
sleep 3
echo "Xfce4 started (PID: $XFCE_PID)"

# Create VNC password file
echo "Setting up VNC password..."
mkdir -p /tmp
echo "$VNC_PASSWORD" > /tmp/vnc_passwd
chmod 600 /tmp/vnc_passwd

# Start x11vnc server
echo "Starting x11vnc server..."
x11vnc -display :1 -localhost -forever -shared -rfbport 5900 -rfbauth /tmp/vnc_passwd -o /tmp/x11vnc.log -bg
sleep 2
echo "x11vnc started on port 5900"

# Start websockify for noVNC
echo "Starting websockify..."
# Check if noVNC is installed, if not install it
if [ ! -d "/home/user/novnc" ]; then
    echo "Installing noVNC..."
    cd /tmp
    git clone https://github.com/novnc/noVNC.git
    cp -r noVNC /home/user/novnc
    rm -rf noVNC
fi

websockify --web /home/user/novnc 6080 localhost:5900 &
WEBSOCKIFY_PID=$!
sleep 2
echo "websockify started on port 6080 (PID: $WEBSOCKIFY_PID)"

# Verify all services are running
echo ""
echo "========================================="
echo "Desktop Environment Status:"
echo "========================================="
echo "Xvfb: $(pgrep -f 'Xvfb :1' | head -1)"
echo "x11vnc: $(pgrep -f x11vnc | head -1)"
echo "websockify: $(pgrep -f websockify | head -1)"
echo "Xfce4: $(pgrep -f startxfce4 | head -1)"
echo ""

# Start Flask application
echo "Starting Flask web server..."
cd /workspace
python3 app/main.py
