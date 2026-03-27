#!/bin/bash
# Remote Desktop Setup - Status Check Script

LOG_DIR="$HOME/remote-desktop-logs"
VNC_PORT="5901"
WEB_PORT="6080"
DISPLAY_NUM="1"

echo "=========================================="
echo "Remote Desktop Service Status"
echo "=========================================="
echo ""

# Function to check if process is running
check_process() {
    local name=$1
    local pid_file="$LOG_DIR/$2.pid"
    
    if pgrep -f "$name" > /dev/null; then
        local pid=$(pgrep -f "$name" | head -1)
        echo "✅ Running (PID: $pid)"
        return 0
    else
        echo "❌ Stopped"
        return 1
    fi
}

# Function to check port
check_port() {
    local port=$1
    local name=$2
    
    if netstat -tuln 2>/dev/null | grep -q ":$port "; then
        echo "✅ $name listening on port $port"
        return 0
    else
        echo "❌ $name not listening on port $port"
        return 1
    fi
}

echo "🖥️  X Components:"
echo "   Xvfb:       $(check_process "Xvfb :$DISPLAY_NUM" "xvfb")"
echo "   Xfce4:      $(check_process "xfce4-session" "xfce4")"
echo ""

echo "🔌 Network Services:"
check_port $VNC_PORT "x11vnc"
check_port $WEB_PORT "websockify"
echo ""

echo "☁️  Cloudflare Tunnel:"
if pgrep -f "cloudflared tunnel" > /dev/null; then
    TUNNEL_PID=$(pgrep -f "cloudflared tunnel" | head -1)
    echo "   Status:     ✅ Running (PID: $TUNNEL_PID)"
    
    # Try to get tunnel URL
    if [ -f "$HOME/.cloudflared/config.yml" ]; then
        TUNNEL_ID=$(grep "^tunnel:" "$HOME/.cloudflared/config.yml" | awk '{print $2}')
        if [ -n "$TUNNEL_ID" ]; then
            echo "   Tunnel ID:  $TUNNEL_ID"
        fi
    fi
else
    echo "   Status:     ❌ Not running"
fi
echo ""

echo "📊 Resource Usage:"
echo "   Xvfb:       $(ps aux | grep -E "Xvfb :$DISPLAY_NUM" | grep -v grep | awk '{print $5, $6}' | head -1 || echo "N/A")"
echo "   Xfce4:      $(ps aux | grep xfce4-session | grep -v grep | awk '{print $5, $6}' | head -1 || echo "N/A")"
echo ""

echo "📁 Log Files:"
if [ -d "$LOG_DIR" ]; then
    for log in "$LOG_DIR"/*.log; do
        if [ -f "$log" ]; then
            name=$(basename "$log")
            size=$(du -h "$log" | cut -f1)
            echo "   $name: $size"
        fi
    done
else
    echo "   Log directory not found"
fi
echo ""

echo "🔗 Access URLs:"
LOCAL_IP=$(hostname -I | awk '{print $1}')
echo "   Local:      http://localhost:$WEB_PORT/vnc.html"
echo "   Network:    http://$LOCAL_IP:$WEB_PORT/vnc.html"
echo ""
