#!/bin/bash
# Remote Desktop Setup - Cloudflare Tunnel Configuration
# Sets up secure external access via Cloudflare Tunnel

set -e

echo "=========================================="
echo "Cloudflare Tunnel Setup"
echo "=========================================="
echo ""

WEB_PORT="6080"

echo "☁️  This will create a secure HTTPS tunnel to your remote desktop."
echo ""

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo "❌ cloudflared not found. Please run install.sh first."
    exit 1
fi

# Check if websockify is running
if ! netstat -tuln 2>/dev/null | grep -q ":$WEB_PORT "; then
    echo "⚠️  Warning: websockify doesn't seem to be running on port $WEB_PORT"
    echo "   Please run setup.sh first to start the remote desktop services."
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "🔐 Authenticating with Cloudflare..."
echo "   A browser window will open for authentication."
echo ""

# Login to Cloudflare
cloudflared tunnel login

echo ""
echo "📝 Creating tunnel..."

# Generate a tunnel name
TUNNEL_NAME="remote-desktop-$(hostname | tr '[:upper:]' '[:lower:]' | tr -cd 'a-z0-9-')"
echo "   Tunnel name: $TUNNEL_NAME"

# Create tunnel
TUNNEL_OUTPUT=$(cloudflared tunnel create "$TUNNEL_NAME" 2>&1)
echo "$TUNNEL_OUTPUT"

# Extract tunnel ID
TUNNEL_ID=$(echo "$TUNNEL_OUTPUT" | grep -oP '(?<=id )[a-f0-9-]+' | head -1)

if [ -z "$TUNNEL_ID" ]; then
    # Try alternative extraction method
    TUNNEL_ID=$(cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}')
fi

if [ -z "$TUNNEL_ID" ]; then
    echo "❌ Failed to get tunnel ID. Please check the output above."
    exit 1
fi

echo "   Tunnel ID: $TUNNEL_ID"

# Create config file
CONFIG_DIR="$HOME/.cloudflared"
mkdir -p "$CONFIG_DIR"

CONFIG_FILE="$CONFIG_DIR/config.yml"

echo ""
echo "📝 Creating configuration file..."
cat > "$CONFIG_FILE" << EOF
tunnel: $TUNNEL_ID
credentials-file: $CONFIG_DIR/$TUNNEL_ID.json

ingress:
  - hostname: 
    service: http://localhost:$WEB_PORT
  - service: http_status:404
EOF

echo "   Config saved to: $CONFIG_FILE"

echo ""
echo "🌐 Routing traffic..."

# Get tunnel URL
cloudflared tunnel route dns "$TUNNEL_NAME" "$TUNNEL_NAME"

# Start tunnel
echo ""
echo "🚀 Starting Cloudflare Tunnel..."
echo "   Press Ctrl+C to stop the tunnel"
echo ""

# Show access URL
echo "=========================================="
echo "🎉 Remote Desktop Access URL:"
echo "   https://${TUNNEL_NAME}.trycloudflare.com/vnc.html"
echo "=========================================="
echo ""
echo "📋 To run the tunnel in background:"
echo "   cloudflared tunnel run $TUNNEL_NAME"
echo ""
echo "📋 To install as a system service:"
echo "   sudo cloudflared service install"
echo "   sudo systemctl start cloudflared"
echo ""

# Run tunnel
cloudflared tunnel run "$TUNNEL_NAME"
