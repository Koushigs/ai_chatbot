#!/bin/bash
set -e

echo "🚀 Starting deployment for FastAPI App on Server (165.232.177.1)..."

# 1. Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# 2. Install required dependencies
echo "🛠️ Installing Git, Curl, Nginx, Certbot..."
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common git nginx certbot python3-certbot-nginx

# 3. Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    rm get-docker.sh
else
    echo "✅ Docker is already installed."
fi

# 4. Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️ Warning: .env file not found! Creating default template..."
    cat <<EOT > .env
SARVAM_API_KEY=
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
KUNDALI_PRICE=199
JANMARASHI_PRICE=20
KUNDALI_PDF_API=https://debug.bharatcalendars.in:8443/api/kundali/generate-pdf
JANMARASHI_API=https://debug.bharatcalendars.in:8443/api/janamrashi/moon-rashi
EOT
    echo "❗ Please edit .env file to fill in your API secrets before running Docker compose."
fi

# 5. Fix SQLite & Json volume files (ensure they are files, not auto-created directories)
echo "💾 Initializing database files..."
sudo docker compose down || true

if [ -d "payments.db" ]; then sudo rm -rf payments.db; fi
if [ ! -f "payments.db" ]; then touch payments.db; fi

if [ -d "payments_db.json" ]; then sudo rm -rf payments_db.json; fi
if [ ! -f "payments_db.json" ]; then echo "{}" > payments_db.json; fi

if [ -d "affiliate_products_cache.json" ]; then sudo rm -rf affiliate_products_cache.json; fi
if [ ! -f "affiliate_products_cache.json" ]; then echo "{}" > affiliate_products_cache.json; fi

# 6. Build and launch Docker container
echo "🏗️ Building and starting Docker container..."
sudo docker compose up -d --build

# 7. Configure Nginx Reverse Proxy
echo "🌐 Configuring Nginx reverse proxy..."
sudo cp nginx.conf /etc/nginx/sites-available/bharat-ai
sudo ln -sf /etc/nginx/sites-available/bharat-ai /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx

# 8. Configure Firewall (UFW)
echo "🔒 Configuring UFW Firewall..."
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 8001/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

echo "✅ DEPLOYMENT COMPLETE!"
echo "📍 Access your application live at: http://165.232.177.1 or http://chat.bharatcalendars.in:8001"
echo "📜 View container logs anytime using: sudo docker compose logs -f"
