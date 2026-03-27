#!/bin/bash
# Remote Desktop Setup - Installation Script
# Installs all required packages for Xvfb + x11vnc + noVNC setup

set -e

echo "=========================================="
echo "Remote Desktop Environment Installer"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
   echo "⚠️  Warning: Running as root. Some desktop features may not work correctly."
   echo "   Consider running as a regular user with sudo access."
   echo ""
fi

# Update package list
echo "📦 Updating package list..."
sudo apt-get update

# Install Xfce4 desktop environment (minimal)
echo "🖥️  Installing Xfce4 desktop environment..."
sudo apt-get install -y --no-install-recommends \
    xfce4 \
    xfce4-terminal \
    xfce4-panel \
    xfce4-session \
    xfce4-settings \
    xfdesktop4 \
    xfwm4 \
    xfce4-taskmanager \
    mousepad \
    thunar

# Install X virtual framebuffer
echo "🖼️  Installing Xvfb (virtual X server)..."
sudo apt-get install -y xvfb

# Install VNC server
echo "🔌 Installing x11vnc (VNC server)..."
sudo apt-get install -y x11vnc

# Install noVNC and websockify
echo "🌐 Installing noVNC and websockify..."
sudo apt-get install -y novnc websockify

# Install additional tools
echo "🛠️  Installing additional tools..."
sudo apt-get install -y \
    net-tools \
    curl \
    wget \
    htop \
    git

# Install Cloudflare Tunnel (cloudflared)
echo "☁️  Installing Cloudflare Tunnel (cloudflared)..."
if ! command -v cloudflared &> /dev/null; then
    # Download latest cloudflared
    curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
    sudo dpkg -i cloudflared.deb
    rm -f cloudflared.deb
    echo "✅ Cloudflare Tunnel installed"
else
    echo "✅ Cloudflare Tunnel already installed"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p ~/.vnc
mkdir -p ~/remote-desktop-logs

# Set VNC password (default: 123456)
echo "🔑 Setting default VNC password..."
echo "123456" | x11vnc -storepasswd ~/.vnc/passwd

echo ""
echo "=========================================="
echo "✅ Installation Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Run: bash scripts/setup.sh"
echo "2. Access desktop at: http://<server-ip>:6080/vnc.html"
echo ""
echo "Default VNC password: 123456"
echo "⚠️  Remember to change the password for security!"
echo ""
