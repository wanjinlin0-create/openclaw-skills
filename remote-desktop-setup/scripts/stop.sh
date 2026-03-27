#!/bin/bash
# Remote Desktop Setup - Stop Script

echo "=========================================="
echo "Stopping Remote Desktop Services"
echo "=========================================="
echo ""

LOG_DIR="$HOME/remote-desktop-logs"

# Function to stop process
stop_process() {
    local name=$1
    local pattern=$2
    
    if pgrep -f "$pattern" > /dev/null; then
        echo "🛑 Stopping $name..."
        pkill -f "$pattern" 2>/dev/null || true
        sleep 1
        
        # Force kill if still running
        if pgrep -f "$pattern" > /dev/null; then
            pkill -9 -f "$pattern" 2>/dev/null || true
        fi
        
        echo "   ✅ $name stopped"
    else
        echo "   ℹ️  $name not running"
    fi
}

# Stop Cloudflare Tunnel first
stop_process "Cloudflare Tunnel" "cloudflared tunnel"
echo ""

# Stop websockify
stop_process "websockify" "websockify"
echo ""

# Stop x11vnc
stop_process "x11vnc" "x11vnc"
echo ""

# Stop Xfce4
stop_process "Xfce4" "xfce4-session"
echo ""

# Stop Xvfb
stop_process "Xvfb" "Xvfb :"
echo ""

# Clean up PID files
if [ -d "$LOG_DIR" ]; then
    echo "🧹 Cleaning up PID files..."
    rm -f "$LOG_DIR"/*.pid
    echo "   ✅ Done"
fi

echo ""
echo "=========================================="
echo "✅ All services stopped"
echo "=========================================="
