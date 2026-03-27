#!/bin/bash
# Remote Desktop Setup - Service Startup Script
# Starts Xvfb, x11vnc, and websockify services

set -e

echo "=========================================="
echo "Starting Remote Desktop Services"
echo "=========================================="
echo ""

# Configuration
DISPLAY_NUM="1"
VNC_PORT="5901"
WEB_PORT="6080"
VNC_PASSWD="$HOME/.vnc/passwd"
LOG_DIR="$HOME/remote-desktop-logs"

# Create log directory
mkdir -p "$LOG_DIR"

# Function to check if a port is in use
check_port() {
    local port=$1
    if netstat -tuln 2>/dev/null | grep -q ":$port "; then
        return 0
    else
        return 1
    fi
}

# Function to kill existing processes
kill_existing() {
    local name=$1
    pkill -f "$name" 2>/dev/null || true
    sleep 1
}

echo "🧹 Cleaning up existing processes..."
kill_existing "Xvfb :$DISPLAY_NUM"
kill_existing "x11vnc"
kill_existing "websockify"

echo ""
echo "🖥️  Starting Xvfb (virtual X server) on display :$DISPLAY_NUM..."
Xvfb :$DISPLAY_NUM -screen 0 1920x1080x24 > "$LOG_DIR/xvfb.log" 2>&1 &
echo $! > "$LOG_DIR/xvfb.pid"
sleep 2

# Check if Xvfb started
if ! pgrep -f "Xvfb :$DISPLAY_NUM" > /dev/null; then
    echo "❌ Failed to start Xvfb. Check $LOG_DIR/xvfb.log"
    exit 1
fi
echo "✅ Xvfb started (PID: $(cat $LOG_DIR/xvfb.pid))"

echo ""
echo "🖼️  Starting Xfce4 desktop environment..."
export DISPLAY=":$DISPLAY_NUM"
xfce4-session > "$LOG_DIR/xfce4.log" 2>&1 &
echo $! > "$LOG_DIR/xfce4.pid"
sleep 3

# Check if Xfce4 started
if ! pgrep -f "xfce4-session" > /dev/null; then
    echo "⚠️  Warning: xfce4-session may not have started properly"
fi
echo "✅ Xfce4 session started"

echo ""
echo "🔌 Starting x11vnc (VNC server) on port $VNC_PORT..."
x11vnc -display :$DISPLAY_NUM -rfbport $VNC_PORT -rfbauth "$VNC_PASSWD" \
    -forever -shared -bg -o "$LOG_DIR/x11vnc.log" -noxdamage -noxfixes -noxrecord

sleep 2
if check_port $VNC_PORT; then
    echo "✅ x11vnc started on port $VNC_PORT"
else
    echo "❌ Failed to start x11vnc. Check $LOG_DIR/x11vnc.log"
    exit 1
fi

echo ""
echo "🌐 Starting websockify (noVNC) on port $WEB_PORT..."
websockify -D --web=/usr/share/novnc --cert=none --key=none \
    $WEB_PORT localhost:$VNC_PORT > "$LOG_DIR/websockify.log" 2>&1
echo $! > "$LOG_DIR/websockify.pid"

sleep 2
if check_port $WEB_PORT; then
    echo "✅ websockify started on port $WEB_PORT"
else
    echo "❌ Failed to start websockify. Check $LOG_DIR/websockify.log"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ All Services Started Successfully!"
echo "=========================================="
echo ""
echo "📱 Access your remote desktop:"
echo "   Local:    http://$(hostname -I | awk '{print $1}'):$WEB_PORT/vnc.html"
echo "   Local:    http://localhost:$WEB_PORT/vnc.html"
echo ""
echo "🔑 VNC Password: (stored in $VNC_PASSWD)"
echo ""
echo "📊 Service Status:"
echo "   Xvfb:       $(pgrep -f "Xvfb :$DISPLAY_NUM" >/dev/null && echo "Running" || echo "Stopped")"
echo "   x11vnc:     $(check_port $VNC_PORT && echo "Running on port $VNC_PORT" || echo "Stopped")"
echo "   websockify: $(check_port $WEB_PORT && echo "Running on port $WEB_PORT" || echo "Stopped")"
echo ""
echo "📝 Logs: $LOG_DIR/"
echo ""
echo "⚠️  To setup external access via Cloudflare Tunnel, run:"
echo "   bash scripts/setup-tunnel.sh"
echo ""
