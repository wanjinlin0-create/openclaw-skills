#!/bin/bash
# Remote Desktop Setup - Restart Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "Restarting Remote Desktop Services"
echo "=========================================="
echo ""

# Stop services
echo "🛑 Stopping services..."
bash "$SCRIPT_DIR/stop.sh"

echo ""
echo "⏳ Waiting 2 seconds..."
sleep 2

# Start services
echo ""
echo "🚀 Starting services..."
bash "$SCRIPT_DIR/setup.sh"

echo ""
echo "=========================================="
echo "✅ Restart complete"
echo "=========================================="
