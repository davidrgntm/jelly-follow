#!/bin/bash
# Jelly Follow — Deployment Script
# Usage: bash deploy/deploy.sh
set -e

APP_DIR="/home/jelly/jelly-follow"
VENV="$APP_DIR/venv"
SERVICE="jelly-follow"
LOG_DIR="/var/log/jelly-follow"

echo "=== [1/7] Creating directories ==="
sudo mkdir -p "$LOG_DIR"
sudo chown jelly:jelly "$LOG_DIR"

echo "=== [2/7] Creating virtual environment ==="
cd "$APP_DIR"
python3 -m venv venv
source venv/bin/activate

echo "=== [3/7] Installing dependencies ==="
pip install --upgrade pip
pip install -r requirements.txt

echo "=== [4/7] Creating static dirs ==="
mkdir -p static/qr templates

echo "=== [5/7] Checking .env ==="
if [ ! -f .env ]; then
    echo "ERROR: .env file not found! Copy .env.example and configure it."
    exit 1
fi

echo "=== [6/7] Installing systemd service ==="
sudo cp deploy/jelly-follow.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE"
sudo systemctl restart "$SERVICE"

echo "=== [7/7] Checking status ==="
sleep 2
sudo systemctl status "$SERVICE" --no-pager

echo ""
echo "✅ Deployment complete!"
echo ""
echo "   Service:  systemctl status $SERVICE"
echo "   Logs:     journalctl -u $SERVICE -f"
echo "   Nginx:    sudo cp deploy/nginx.conf /etc/nginx/sites-available/jelly-follow"
echo "   SSL:      sudo certbot --nginx -d follow.jelly.uz -d go.jelly.uz -d api.follow.jelly.uz"
