# CampusPilot AI — Manual AWS EC2 Deployment Guide (Docker Compose)

This guide provides the complete, step-by-step procedure to deploy **CampusPilot AI** manually on an **AWS EC2** instance using **Docker Compose** and **Nginx Reverse Proxy**.

---

## Architecture Overview

```
                          Internet (Clients / Students)
                                       │
                                       ▼ (Port 80 / 443 HTTPS)
                   ┌────────────────────────────────────────┐
                   │               AWS EC2                  │
                   │                                        │
                   │   ┌────────────────────────────────┐   │
                   │   │     Nginx Reverse Proxy        │   │
                   │   │    (Rate limit, SSE, SSL)      │   │
                   │   └───────────────┬────────────────┘   │
                   │                   │                    │
                   │         ┌─────────┴─────────┐          │
                   │         │                   │          │
                   │   / (HTML, JS, CSS)      /api/         │
                   │         ▼                   ▼          │
                   │  ┌─────────────┐     ┌─────────────┐   │
                   │  │ Next.js 16  │     │ FastAPI     │   │
                   │  │ (Port 3000) │     │ (Port 8000) │   │
                   │  └─────────────┘     └──────┬──────┘   │
                   └─────────────────────────────┼──────────┘
                                                 │
                                                 ▼
                                     ┌───────────────────────┐
                                     │  External Cloud APIs  │
                                     │  • Google Gemini API  │
                                     │  • Supabase Database  │
                                     │  • Razorpay Payments  │
                                     └───────────────────────┘
```

---

## 1. Prerequisites & EC2 Specifications

### Recommended Instance Types
| Workload Level | Recommended Instance | vCPUs | RAM | Storage | Est. Monthly Cost (On-Demand) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Development / Test** | `t3.small` (with 2GB Swap) | 2 | 2 GB | 25 GB gp3 | ~$15 / mo |
| **Production (Recommended)**| `t3.medium` | 2 | 4 GB | 30 GB gp3 | ~$30 / mo |
| **Low-Traffic Pilot** | `t3.micro` (with 2GB Swap) | 2 | 1 GB | 20 GB gp3 | Free Tier / ~$7 / mo |

> [!IMPORTANT]
> If using `t3.micro` (1 GB RAM), **you MUST enable a 2 GB swap file** (Step 3) before running `docker compose build`, otherwise the Node.js/TypeScript Next.js build may be terminated by the Linux Out-Of-Memory (OOM) killer.

### AWS Security Group Requirements
Ensure the EC2 Security Group permits the following inbound traffic:
- **SSH (Port 22)**: Restricted to your IP address.
- **HTTP (Port 80)**: `0.0.0.0/0` (Anywhere for web traffic & Certbot ACME verification).
- **HTTPS (Port 443)**: `0.0.0.0/0` (Anywhere for encrypted production traffic).

> [!NOTE]
> Ports `3000` (Frontend) and `8000` (Backend) are kept strictly internal within the Docker network and should **NOT** be opened in the AWS Security Group. All traffic flows securely through Nginx on ports 80/443.

---

## 2. Server Preparation & System Packages

Connect to your EC2 instance via SSH:
```bash
ssh -i /path/to/your-key.pem ubuntu@<YOUR_EC2_PUBLIC_IP>
```

### Update OS and Install Base Utilities
```bash
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y curl git ufw fail2ban ca-certificates gnupg lsb-release
```

---

## 3. Memory Optimization (Configure 2GB Swap)

Run these commands to prevent OOM errors on 1GB or 2GB RAM instances:

```bash
# Check existing swap
sudo swapon --show

# Allocate 2GB swap file
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make swap persistent across reboots
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Tune swappiness for optimal memory caching
sudo sysctl vm.swappiness=20
echo 'vm.swappiness=20' | sudo tee -a /etc/sysctl.conf

# Verify active memory and swap
free -h
```

---

## 4. Install Docker Engine & Docker Compose

Install the latest official Docker Engine and Docker Compose v2:

```bash
# 1. Add Docker's official GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# 2. Add Docker repository to Apt sources
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 3. Install Docker packages
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 4. Add your user to the docker group (avoids needing sudo for docker commands)
sudo usermod -aG docker $USER

# 5. Apply new group membership (or log out and back in)
newgrp docker

# 6. Verify Docker installation
docker --version
docker compose version
```

---

## 5. Clone Repository & Configure Environment

### Clone the Repository
```bash
cd /home/ubuntu
git clone https://github.com/GANDHIKALASI/CampusPilotAI.git
cd CampusPilotAI
```

### Create the Production Environment File (`.env`)
```bash
cp .env.example .env
nano .env
```

Populate the `.env` file with your verified production values:

```ini
# Application Configuration
APP_NAME=CampusPilot AI
APP_ENV=production
DEBUG=false
HOST=0.0.0.0
PORT=8000

# CORS & Trusted Hosts (Replace with your actual EC2 public IP or domain)
CORS_ORIGINS=http://<YOUR_EC2_PUBLIC_IP>,https://yourdomain.com
ALLOWED_HOSTS=*

# Google Gemini API
GEMINI_API_KEY=your_verified_gemini_api_key
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_EMBEDDING_MODEL=gemini-embedding-2

# Supabase Managed Database & Auth
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_PUBLISHABLE_KEY=your_supabase_anon_publishable_key
SUPABASE_SECRET_KEY=your_supabase_service_role_key
SUPABASE_JWT_SECRET=your_supabase_jwt_secret

# Frontend Client-side Injection (Next.js)
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=your_supabase_anon_publishable_key
NEXT_PUBLIC_API_URL=/api

# Razorpay Payment Gateway (Optional in testing)
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_secret_key
RAZORPAY_WEBHOOK_SECRET=your_razorpay_webhook_secret


# Business Limits
ADMIN_EMAILS=admin@campuspilot.ai
MAX_UPLOAD_SIZE_BYTES=10485760
VISITOR_CHAT_LIMIT=3
INITIAL_FREE_CREDITS=20
```

> [!WARNING]
> Keep permissions on `.env` locked down so other OS users cannot inspect API credentials:
> ```bash
> chmod 600 .env
> ```

---

## 6. Build and Launch Containers

Validate your compose specification and start all services in detached mode:

```bash
# 1. Validate Docker Compose configuration
docker compose config

# 2. Build and start services in the background
docker compose up --build -d
```

---

## 7. Operational Monitoring & Health Checks

### Check Running Containers
```bash
docker compose ps
```
All three containers (`campuspilot-backend`, `campuspilot-frontend`, `campuspilot-nginx`) should display `Up (healthy)`.

### Inspect Container Logs
```bash
# Stream all logs
docker compose logs -f

# Inspect specific service logs
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f nginx
```

### Test Health Endpoints from Terminal
```bash
# Test through Nginx reverse proxy
curl -i http://localhost/health
curl -i http://localhost/api/health

# Test directly from external browser
curl -i http://<YOUR_EC2_PUBLIC_IP>/health
```
Expected output:
```json
HTTP/1.1 200 OK
{"status":"healthy","app_name":"CampusPilot AI","version":"1.0.0","env":"production"}
```

---

## 8. Domain & SSL/TLS Configuration (Certbot HTTPS)

Once your custom domain name (e.g. `campuspilot.yourdomain.com`) points to your EC2 instance's Elastic IP address via an **A record**:

### 1. Request SSL Certificate using Certbot
Run Certbot via temporary Docker container using the shared `certbot-www` and `certbot-etc` volumes:

```bash
docker run -it --rm \
  -v campuspilotai_certbot-etc:/etc/letsencrypt \
  -v campuspilotai_certbot-var:/var/lib/letsencrypt \
  -v campuspilotai_certbot-www:/var/www/html \
  certbot/certbot certonly --webroot \
  --webroot-path=/var/www/html \
  -d yourdomain.com -d www.yourdomain.com \
  --email your-email@domain.com --agree-tos --no-eff-email
```

### 2. Enable HTTPS in Nginx
Open `nginx/conf.d/default.conf`:
```bash
nano nginx/conf.d/default.conf
```
Uncomment the HTTPS `server { listen 443 ssl ... }` block at the bottom of the file and replace `yourdomain.com` with your real domain.

### 3. Reload Nginx
```bash
docker compose exec nginx nginx -s reload
```

### 4. Automated Certificate Renewal Cron Job
Set up an automated monthly certificate renewal in `cron`:
```bash
sudo crontab -e
```
Add the following line to run renewal every Monday at 3:00 AM:
```cron
0 3 * * 1 docker run --rm -v campuspilotai_certbot-etc:/etc/letsencrypt -v campuspilotai_certbot-var:/var/lib/letsencrypt -v campuspilotai_certbot-www:/var/www/html certbot/certbot renew --webroot -w /var/www/html --quiet && docker compose exec -T nginx nginx -s reload
```

---

## 9. Day-to-Day Maintenance & Update Procedures

### Restart Services
```bash
docker compose restart
```

### Stop Services Gracefully
```bash
docker compose down
```

### Update Application to Latest GitHub Commit (Zero Data Loss)
```bash
# 1. Pull latest code from GitHub
git pull origin main

# 2. Rebuild and relaunch containers seamlessly
docker compose up --build -d

# 3. Clean up dangling/unused images to reclaim disk space
docker image prune -f
```

---

## 10. Troubleshooting Common Issues

### Issue 1: `bind: address already in use` on Port 80
- **Cause**: Apache or an existing system Nginx is running directly on the host OS.
- **Solution**:
  ```bash
  sudo systemctl stop apache2 nginx 2>/dev/null
  sudo systemctl disable apache2 nginx 2>/dev/null
  sudo lsof -i :80
  docker compose up -d
  ```

### Issue 2: Frontend Build Freezes or Exits with Code 137 (OOM)
- **Cause**: Insufficient RAM during Next.js webpack/turbopack compilation.
- **Solution**:
  Verify swap is active with `free -h`. If no swap exists, follow **Section 3** to create a 2GB swap file.

### Issue 3: AI Chat Streaming Hangs or Delivers All Words at Once
- **Cause**: Nginx proxy buffering is enabled, delaying chunks until the response completes.
- **Solution**:
  Verify `nginx/conf.d/default.conf` has `proxy_buffering off;` and `chunked_transfer_encoding on;` under `location /api/`.

### Issue 4: CORS Errors in Browser Console
- **Cause**: The browser's domain or EC2 IP is not listed in `CORS_ORIGINS`.
- **Solution**:
  Update `CORS_ORIGINS` in `.env` to include your exact domain and protocol:
  ```ini
  CORS_ORIGINS=http://<YOUR_EC2_PUBLIC_IP>,https://yourdomain.com
  ```
  Then restart backend:
  ```bash
  docker compose restart backend
  ```

---

## 11. Estimated Resource Footprint

| Service | CPU (Idle) | Memory (Idle) | Memory (Peak Load) |
| :--- | :---: | :---: | :---: |
| **FastAPI Backend (2 workers)** | < 1% | ~120 MB | ~280 MB |
| **Next.js 16 Standalone** | < 1% | ~65 MB | ~180 MB |
| **Nginx Alpine** | < 0.1% | ~12 MB | ~25 MB |
| **Host Ubuntu OS** | ~1% | ~280 MB | ~350 MB |
| **Total System Footprint** | **~2%** | **~477 MB** | **~835 MB** |

On a **`t3.small`** instance (2 GB RAM) with a **2 GB Swap file**, CampusPilot AI operates comfortably with over **1.2 GB of free physical headroom**.
