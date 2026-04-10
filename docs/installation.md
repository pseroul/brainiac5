# Installation Guide

This guide covers two scenarios:

- **Option A** — Local development setup (your laptop or desktop)
- **Option B** — Production deployment on a Raspberry Pi 4

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.11+ | 3.12 also works |
| Node.js | 20+ | LTS recommended |
| npm | 10+ | Bundled with Node 20 |
| git | any | For cloning the repo |
| nginx | any | Production only |

**Hardware (production):** Raspberry Pi 4 (aarch64, 4 GB RAM recommended due to ChromaDB's memory footprint).

---

## Option A: Local Development Setup

### 1. Clone the repository

```bash
git clone https://github.com/pseroul/consensia.git
cd consensia
```

### 2. Backend setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

> **Note (Raspberry Pi / aarch64 only):** If `import torch` raises `Illegal Instruction`, install a compatible CPU build:
> ```bash
> pip install torch==2.6.0+cpu --extra-index-url https://download.pytorch.org/whl/cpu
> ```

#### Create the data directory

```bash
mkdir -p data
```

#### Configure CORS origins

Create `backend/data/site.json`:

```json
{
  "origins": [
    "http://localhost:5173",
    "http://127.0.0.1:5173"
  ]
}
```

#### Set the JWT secret key

The server requires a secret key to sign authentication tokens. Export it in your shell (or add to your `.bashrc` / `.zshrc`):

```bash
export JWT_SECRET_KEY="replace-with-a-long-random-string"
```

Generate a secure value with:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

#### Add the first user

Consensia uses TOTP (Google Authenticator) — there are no passwords. To create your first account:

```bash
python authenticator.py your@email.com
```

The command prints a provisioning URI. Open it in a QR-code renderer or paste it directly into Google Authenticator → **Set up account** → **Enter a setup key**.

#### Start the backend

```bash
python main.py
```

The API is now available at `http://localhost:8000`.  
Swagger UI: `http://localhost:8000/docs`

### 3. Frontend setup

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

The app is now available at `http://localhost:5173`.

---

## Option B: Raspberry Pi Production Deployment

This section walks through a complete, from-scratch production setup on a Raspberry Pi 4.

### Step 1 — Flash and configure the Pi

1. Download [Raspberry Pi Imager](https://www.raspberrypi.com/software/) and flash **Raspberry Pi OS Lite (64-bit)** to an SD card.
2. In the imager's advanced options, enable SSH and set your username/password.
3. Insert the SD card, boot the Pi, and SSH in:

```bash
ssh youruser@<pi-ip-address>
```

> **Tip:** Assign your Pi a static IP via your router's DHCP reservation settings, or configure it in `/etc/dhcpcd.conf`. This makes the deployment URL stable.

### Step 2 — Update the system

```bash
sudo apt-get update && sudo apt-get upgrade -y
```

### Step 3 — Install system dependencies

```bash
sudo apt-get install -y git python3.11 python3.11-venv python3-pip nginx
```

Install Node.js 20 via NodeSource:

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

Verify:

```bash
python3.11 --version   # Python 3.11.x
node --version         # v20.x.x
nginx -v               # nginx/1.x.x
```

### Step 4 — Open firewall ports

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw reload
```

Also forward ports **80** and **443** on your home router to the Pi's local IP address (consult your router's documentation).

### Step 5 — Clone the repository

```bash
cd ~
git clone https://github.com/pseroul/consensia.git
cd consensia
```

### Step 6 — Backend setup

```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

> **aarch64 PyTorch fix:** If startup fails with `Illegal Instruction`:
> ```bash
> pip install torch==2.6.0+cpu --extra-index-url https://download.pytorch.org/whl/cpu
> ```

Create the data directory:

```bash
mkdir -p data
```

Create `backend/data/site.json` — include your domain (and localhost for testing):

```json
{
  "origins": [
    "http://localhost:5173",
    "https://yourdomain.com",
    "http://yourdomain.com"
  ]
}
```

Set the JWT secret key persistently (edit `/etc/environment` so it survives reboots):

```bash
sudo nano /etc/environment
```

Add this line:

```
JWT_SECRET_KEY="replace-with-a-long-random-string"
```

Generate a secure value:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Add the first admin user:

```bash
source venv/bin/activate
python authenticator.py admin@yourdomain.com
```

Scan the printed QR code with Google Authenticator.

### Step 7 — Build the frontend

> **Do this on your development machine** (not the Pi), to avoid installing Node.js on the server.

```bash
cd frontend
npm install
VITE_API_URL=https://yourdomain.com/api npm run build
```

> If you are using an IP address instead of a domain, use `http://<your-public-ip>/api`.

Commit and push the built output so the Pi can pull it:

```bash
git add frontend/dist
git commit -m "build: production frontend"
git push
```

Back on the Pi, pull the build:

```bash
cd ~/consensia
git pull
```

### Step 8 — Deploy the frontend

```bash
sudo mkdir -p /var/www/html/consensia
sudo rm -rf /var/www/html/consensia/*
sudo cp -r frontend/dist/* /var/www/html/consensia/
```

### Step 9 — Configure nginx

Create the nginx site configuration:

```bash
sudo nano /etc/nginx/sites-available/consensia
```

Paste the following (replace `your_public_ip_address` with your Pi's public IP or domain name):

```nginx
server {
    listen 80;
    server_name your_public_ip_address;

    # Frontend (React SPA)
    location / {
        root /var/www/html/consensia;
        index index.html;
        try_files $uri /index.html;
    }

    # Backend (FastAPI) via reverse proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable the site and restart nginx:

```bash
sudo ln -s /etc/nginx/sites-available/consensia /etc/nginx/sites-enabled/
sudo nginx -t          # verify config is valid
sudo systemctl restart nginx
```

### Step 10 — Create the systemd service

This runs Gunicorn as a persistent background service that restarts on failure and starts on boot.

```bash
sudo nano /etc/systemd/system/consensia.service
```

Paste (replace `youruser` with your actual username):

```ini
[Unit]
Description=Gunicorn instance to serve Consensia
After=network.target

[Service]
User=youruser
WorkingDirectory=/home/youruser/consensia/backend
EnvironmentFile=/etc/environment
Environment="PATH=/home/youruser/consensia/backend/venv/bin"
ExecStart=/home/youruser/consensia/backend/venv/bin/gunicorn \
    -w 1 \
    -k uvicorn.workers.UvicornWorker \
    main:app \
    --bind 127.0.0.1:8000

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable consensia.service
sudo systemctl start consensia.service
```

### Step 11 — Verify the deployment

```bash
# Service is running
sudo systemctl status consensia

# Backend responds
curl http://localhost:8000/health
# Expected: {"status":"healthy"}

# nginx serves the frontend
curl -I http://localhost
# Expected: HTTP/1.1 200 OK
```

Open `http://<your-public-ip>` in a browser, log in with your email and the OTP from Google Authenticator.

---

## Optional: HTTPS with a Custom Domain

> **Requires a domain name.** IP-only deployments cannot use Certbot.

### 1. Register a domain and configure DNS

Buy a domain from any registrar (OVH, Namecheap, Cloudflare, etc.). Then:

- Go to your registrar's DNS settings
- Set the **A record** for `yourdomain.com` and `www.yourdomain.com` to your Pi's public IP address
- Wait for DNS propagation (up to 24 h, usually minutes)

### 2. Update nginx to use the domain

Edit `/etc/nginx/sites-available/consensia` — replace `server_name`:

```nginx
server_name yourdomain.com www.yourdomain.com;
```

Also rebuild the frontend with the new URL:

```bash
# On your dev machine:
VITE_API_URL=https://yourdomain.com/api npm run build
git add frontend/dist && git commit -m "build: update API URL to domain" && git push

# On the Pi:
git pull
sudo cp -r frontend/dist/* /var/www/html/consensia/
```

### 3. Issue the TLS certificate

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Certbot automatically rewrites the nginx configuration to redirect HTTP → HTTPS and serves the certificate.

### 4. Close the HTTP port (optional but recommended)

```bash
sudo ufw delete allow 80/tcp
sudo ufw reload
```

Certbot sets up automatic renewal via a systemd timer — no further action needed.

---

## Updating the Application

See [operations.md](operations.md#updating-the-application) for the standard update procedure.
