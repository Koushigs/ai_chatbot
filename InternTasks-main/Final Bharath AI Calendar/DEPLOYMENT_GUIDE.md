# Step-by-Step Server Hosting & Deployment Guide

This guide details how to deploy the **FastAPI Application** to a Linux VPS (Ubuntu / Debian / AWS EC2 / DigitalOcean) using **Docker**, **Docker Compose**, and **Nginx**.

---

## Step 1: Connect to your VPS Server via SSH

Open your Terminal (macOS/Linux) or PowerShell / Command Prompt (Windows) and connect to your server:

```bash
ssh root@YOUR_SERVER_IP
# Or if using an SSH key (AWS EC2):
# ssh -i "your-key.pem" ubuntu@YOUR_SERVER_IP
```

---

## Step 2: Install Docker & Docker Compose on the Server

Run the following commands on your server to update packages and install Docker:

```bash
# 1. Update package index
sudo apt update && sudo apt upgrade -y

# 2. Install prerequisites
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common git nginx certbot python3-certbot-nginx

# 3. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 4. Verify Docker installation
docker --version
docker compose version
```

---

## Step 3: Transfer / Clone Project Files to the Server

Option A: **Via Git (Recommended)**
```bash
cd /var/www
# If /var/www doesn't exist: sudo mkdir -p /var/www && cd /var/www
git clone https://github.com/Koushigs/ai_chatbot.git app
cd app/"InternTasks-main/Final Bharath AI Calendar"
```

Option B: **Via SCP / FileZilla**
Transfer the `Final Bharath AI Calendar` folder directly to `/var/www/app`.

---

## ⚡ Quick 1-Command Automated Deployment (Easiest)

We've provided a fully automated deployment script [`deploy_on_server.sh`](deploy_on_server.sh) that installs Docker, Nginx, configures the firewall, sets up the databases, and launches the container in one go:

```bash
cd /var/www/app/"InternTasks-main/Final Bharath AI Calendar"

# 1. Fill in your environment variables (.env)
nano .env

# 2. Make script executable and run it
chmod +x deploy_on_server.sh
./deploy_on_server.sh
```

---

## Manual Step-by-Step Deployment (Alternative)

---

## Step 4: Configure Environment Variables (.env)

Create or edit the `.env` file on the server:

```bash
nano .env
```

Paste your production secrets:
```env
SARVAM_API_KEY=your_sarvam_api_key_here
KUNDALI_PRICE=129
JANMARASHI_PRICE=20
KUNDALI_PDF_API=https://debug.bharatcalendars.in:8443/api/kundali/generate-pdf
JANMARASHI_API=https://debug.bharatcalendars.in:8443/api/janamrashi/moon-rashi
KUNDALI_SKU=buy.short.kundli
JANMARASHI_SKU=getrashi
```
Press `Ctrl + O`, `Enter` to save, and `Ctrl + X` to exit.

---

## Step 5: Build & Launch Docker Container

Run Docker Compose to build and start your application in detached (background) mode:

```bash
# Build & start container
sudo docker compose up -d --build

# Check running status
sudo docker compose ps

# View container logs
sudo docker compose logs -f
```

Your FastAPI app is now live locally on port `8000` (`http://localhost:8000`).

---

## Step 6: Configure Nginx & SSL Certificate (Domain & Port 80/443)

### 1. Copy Nginx Configuration
```bash
sudo cp nginx.conf /etc/nginx/sites-available/bharat-ai
sudo ln -s /etc/nginx/sites-available/bharat-ai /etc/nginx/sites-enabled/
```

### 2. Edit domain name in Nginx configuration:
```bash
sudo nano /etc/nginx/sites-available/bharat-ai
```
Replace `yourdomain.com` with your actual domain or server IP address.

### 3. Test and Reload Nginx:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

### 4. Enable Free SSL (HTTPS) with Certbot:
```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```
Certbot will automatically configure HTTPS and auto-renewal.

---

## Management & Maintenance Commands

- **View Live Logs**: `sudo docker compose logs -f`
- **Restart Application**: `sudo docker compose restart`
- **Update Application Code**:
  ```bash
  git pull
  sudo docker compose up -d --build
  ```
