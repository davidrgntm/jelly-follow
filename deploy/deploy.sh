#!/bin/bash
# ============================================================
# Jelly Follow — Deployment Script
# Usage: bash deploy/deploy.sh
# ============================================================
set -e

APP_DIR="/home/jelly/jelly-follow"
VENV="$APP_DIR/venv"
SERVICE="jelly-follow"
LOG_DIR="/var/log/jelly-follow"

echo "=== [1/6] Creating log directory ==="
sudo mkdir -p "$LOG_DIR"
sudo chown jelly:jelly "$LOG_DIR"

echo "=== [2/6] Creating virtual environment ==="
cd "$APP_DIR"
python3 -m venv venv
source venv/bin/activate

echo "=== [3/6] Installing dependencies ==="
pip install --upgrade pip
pip install -r requirements.txt

echo "=== [4/6] Creating static dirs ==="
mkdir -p static/qr templates

echo "=== [5/6] Installing systemd service ==="
sudo cp deploy/jelly-follow.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE"
sudo systemctl restart "$SERVICE"

echo "=== [6/6] Checking service status ==="
sudo systemctl status "$SERVICE" --no-pager

echo ""
echo "✅ Deployment complete!"
echo "   Logs: journalctl -u $SERVICE -f"
echo "   Status: systemctl status $SERVICE"
