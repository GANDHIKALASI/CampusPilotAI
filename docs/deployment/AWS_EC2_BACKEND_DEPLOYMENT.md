# CampusPilot AI — AWS EC2 Backend Deployment Guide

**Target Server:** AWS EC2 (`t3.small`, 2 vCPUs, 2 GiB RAM, 20 GiB gp3, Ubuntu LTS)
**Production Frontend:** [https://campuspilotai.vercel.app](https://campuspilotai.vercel.app)
**Architecture:** FastAPI (in Docker, internal port 8000) behind Nginx (in Docker, ports 80 & 443)
**Payment Gateway:** Razorpay is deferred. Do not activate or supply real keys during this deployment.

---

## 1. Architectural Summary & Port Isolation

```
                   Browser / Vercel Frontend
                  (https://campuspilotai.vercel.app)
                                │
                                ▼ (Port 80 / 443 HTTPS)
                   ┌───────────────────────────┐
                   │          AWS EC2          │
                   │                           │
                   │   ┌───────────────────┐   │
                   │   │  Nginx Container  │   │
                   │   │   (Port 80/443)   │   │
                   │   └─────────┬─────────┘   │
                   │             │ Internal    │
                   │             ▼ Bridge Net  │
                   │   ┌───────────────────┐   │
                   │   │  FastAPI Backend  │   │
                   │   │   (Port 8000)     │   │
                   │   │ (Non-root appuser)│   │
                   │   └─────────┬─────────┘   │
                   └─────────────┼─────────────┘
                                 │
         ┌───────────────────────┴───────────────────────┐
         ▼                                               ▼
┌──────────────────┐                           ┌──────────────────┐
│  Google Gemini   │                           │  Supabase Cloud  │
│(RAG & Embeddings)│                           │  (DB, Auth, Vec) │
└──────────────────┘                           └──────────────────┘
```

### Security Rules:
1. **Port 8000 Internal Only:** FastAPI is exposed only inside the Docker network. **Never** open port 8000 in your AWS EC2 Security Group.
2. **Nginx Public Only:** Only Nginx publishes port 80 (HTTP) and port 443 (HTTPS) to the public internet.
3. **No Wildcard CORS or Hosts:** `CORS_ORIGINS` is explicitly locked down to `https://campuspilotai.vercel.app` and `http://localhost:3000`. `ALLOWED_HOSTS` matches your EC2 hostname or IP.

---

## 2. AWS Console Prerequisites (Manual Operations)

Before running commands on EC2, configure your AWS Security Group in the AWS Console:

### Security Group Inbound Rules:

| Type | Protocol | Port Range | Source | Reason |
|:---|:---|:---|:---|:---|
| **SSH** | TCP | 22 | Your Personal IP (`/32`) | Secure terminal access |
| **HTTP** | TCP | 80 | `0.0.0.0/0` | Public HTTP & Let's Encrypt validation |
| **HTTPS** | TCP | 443 | `0.0.0.0/0` | Encrypted API traffic from Vercel |

> [!WARNING]
> Do NOT open port 8000. All API traffic must route through Nginx.

---

## 3. Manual EC2 Deployment Instructions (Step-by-Step)

Connect to your EC2 instance via SSH:
```bash
ssh -i /path/to/your-key.pem ubuntu@<YOUR_EC2_PUBLIC_IP>
```

### Step 1: System Update & 2GB Swap Setup
Ensures the 2 GiB EC2 instance remains stable during builds and traffic spikes:
```bash
sudo apt update && sudo apt upgrade -y

# Check if swap exists
sudo swapon --show

# If no swap is active, create a 2GB swap file:
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Step 2: Clone the Repository
```bash
cd ~
git clone https://github.com/GANDHIKALASI/CampusPilotAI.git
cd CampusPilotAI
```

### Step 3: Configure Environment Variables
Copy the root `.env.example` template:
```bash
cp .env.example .env
nano .env
```

Set the production variables:
```env
APP_NAME=CampusPilot AI
APP_ENV=production
DEBUG=false
HOST=0.0.0.0
PORT=8000

# CORS: Configured for the live production frontend
CORS_ORIGINS=https://campuspilotai.vercel.app,http://localhost:3000

# Allowed hosts: Set to your EC2 public IP or domain name (DO NOT use "*")
ALLOWED_HOSTS=<YOUR_EC2_PUBLIC_IP_OR_HOSTNAME>,localhost,127.0.0.1

# Google Gemini API
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_EMBEDDING_MODEL=gemini-embedding-2

# Supabase Managed Database & Auth
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_PUBLISHABLE_KEY=your_supabase_anon_publishable_key
SUPABASE_SECRET_KEY=your_supabase_service_role_secret_key
SUPABASE_JWT_SECRET=your_supabase_jwt_secret

# Razorpay Payments: DEFERRED (Leave blank for now)
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
RAZORPAY_WEBHOOK_SECRET=

# Administrative email identities
ADMIN_EMAILS=admin@campuspilot.ai
```

### Step 4: Build & Start Containers
Launch FastAPI and Nginx in the background:
```bash
docker compose up -d --build
```

### Step 5: Verify Service Health
Check container status:
```bash
docker compose ps
```
Both containers should report running, and `campuspilot-backend` will report `(healthy)`.

Test the health check locally on EC2:
```bash
# Internal health check direct to backend
curl -i http://localhost:8000/health

# Health check via Nginx reverse proxy
curl -i http://localhost/health
curl -i http://localhost/api/health
```
Expected output:
```json
HTTP/1.1 200 OK
{"status":"healthy","app_name":"CampusPilot AI","version":"1.0.0","env":"production"}
```

Test from your local machine:
```bash
curl -i http://<YOUR_EC2_PUBLIC_IP>/health
```

---

## 4. HTTPS & Domain Setup (Separate Deployment Stage)

Because Vercel serves the frontend over HTTPS (`https://campuspilotai.vercel.app`), browser security (Mixed Content rules) will block API calls to an insecure `http://` backend.

You can configure HTTPS using either a custom domain or a free dynamic DNS hostname.

### Option A: Custom Domain (e.g. `api.yourdomain.com`)
1. Create an **A record** in your DNS provider (Cloudflare, Namecheap, Route 53) pointing `api.yourdomain.com` to your EC2 Public IP.
2. Update `ALLOWED_HOSTS` in `.env`:
   ```env
   ALLOWED_HOSTS=api.yourdomain.com,localhost,127.0.0.1
   ```
3. Issue a Let's Encrypt certificate using Certbot:
   ```bash
   export CERTBOT_ETC_VOL=$(docker volume ls -q | grep certbot-etc | head -n 1)
   export CERTBOT_WWW_VOL=$(docker volume ls -q | grep certbot-www | head -n 1)

   docker run -it --rm \
     -v "${CERTBOT_ETC_VOL}:/etc/letsencrypt" \
     -v "${CERTBOT_WWW_VOL}:/var/www/html" \
     certbot/certbot certonly --webroot \
     -w /var/www/html \
     -d api.yourdomain.com \
     --email your-email@example.com --agree-tos --no-eff-email
   ```
4. Enable the HTTPS block in `nginx/conf.d/default.conf`:
   - Replace `YOUR_API_DOMAIN_PLACEHOLDER` with `api.yourdomain.com`.
   - Uncomment the `server { listen 443 ssl ... }` block.
5. Reload Nginx:
   ```bash
   docker compose exec nginx nginx -s reload
   ```

### Option B: Free Dynamic DNS (e.g. DuckDNS)
1. Register a free subdomain at [DuckDNS](https://www.duckdns.org) (e.g. `campuspilot-api.duckdns.org`) pointing to your EC2 IP.
2. Run Certbot as shown in Option A using `campuspilot-api.duckdns.org`.
3. Update Nginx configuration and reload.

---

## 5. Day-to-Day Maintenance Commands

```bash
# View backend logs (including Uvicorn output)
docker compose logs -f backend

# View Nginx request and error logs
docker compose logs -f nginx

# Restart containers gracefully
docker compose restart backend
docker compose restart nginx

# Stop deployment
docker compose down
```
