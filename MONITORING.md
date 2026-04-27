# 📊 NowShare — Monitoring Setup Guide

Complete production-ready monitoring with Docker, Prometheus, and Grafana.

---

## 📁 Project Structure

```
nowshare/
├── Dockerfile                              # Production app image
├── .dockerignore                           # Build context exclusions
├── docker-compose.yml                      # One-command orchestration
├── app.py                                  # Flask app (with Prometheus metrics)
├── requirements.txt                        # Python dependencies
├── MONITORING.md                           # ← You are here
├── monitoring/
│   ├── prometheus/
│   │   └── prometheus.yml                  # Scrape configuration
│   └── grafana/
│       ├── provisioning/
│       │   ├── datasources/
│       │   │   └── prometheus.yml          # Auto-connect to Prometheus
│       │   └── dashboards/
│       │       └── dashboard.yml           # Auto-load dashboards
│       └── dashboards/
│           └── nowshare-dashboard.json     # Professional dashboard (12 panels)
└── k8s/                                    # Kubernetes manifests
    ├── namespace.yml
    ├── app-deployment.yml
    ├── app-service.yml
    ├── prometheus-configmap.yml
    ├── prometheus-deployment.yml
    ├── prometheus-service.yml
    ├── grafana-deployment.yml
    └── grafana-service.yml
```

---

## 🚀 Quick Start (One Command)

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- Ports `3000`, `9090`, `3001` available

### Run Everything

```bash
docker-compose up -d --build
```

This starts 3 services:

| Service    | URL                        | Purpose                  |
|------------|----------------------------|--------------------------|
| **App**    | http://localhost:3000      | NowShare application     |
| **Prometheus** | http://localhost:9090  | Metrics collection       |
| **Grafana** | http://localhost:3001     | Dashboard visualization  |

### Stop Everything

```bash
docker-compose down
```

### Stop and Remove All Data

```bash
docker-compose down -v
```

---

## 🔐 Grafana Login

| Field     | Value     |
|-----------|-----------|
| **URL**   | http://localhost:3001 |
| **Username** | `admin` |
| **Password** | `admin` |

On first login, Grafana will ask you to change the password. You can skip this for development.

### Dashboard Location

The **"NowShare — Production Dashboard"** is automatically loaded. Find it at:
- Left sidebar → **Dashboards** → **NowShare — Production Dashboard**

---

## 📊 Dashboard Panels

### Row 1: Application Health
| Panel | Description | PromQL |
|-------|-------------|--------|
| ⏱️ Uptime | Time since app started | `time() - process_start_time_seconds` |
| 📊 Total Requests | Cumulative request count | `sum(flask_http_requests_total)` |
| 🚨 Total Errors | Cumulative error count (4xx+5xx) | `sum(flask_http_errors_total)` |
| 💚 App Status | Health indicator + version | `flask_app_info` |

### Row 2: Request Metrics
| Panel | Description | PromQL |
|-------|-------------|--------|
| 📈 Request Rate | Requests/sec by endpoint | `rate(flask_http_requests_total[5m])` |
| ⏱️ Latency P95/P50 | Response time percentiles | `histogram_quantile(0.95, ...)` |
| 🔴 Error Rate | Error percentage gauge | `(errors / total) * 100` |
| 🥧 Status Codes | Donut chart of status distribution | `increase(...[1h]) by (status)` |
| 🏆 Top Endpoints | Horizontal bar chart by traffic | `topk(5, ...)` |

### Row 3: System Metrics
| Panel | Description | PromQL |
|-------|-------------|--------|
| 🔥 CPU Usage | Python process CPU time | `rate(process_cpu_seconds_total[5m])` |
| 💾 Memory Usage | RSS + Virtual memory | `process_resident_memory_bytes` |
| 📂 Open File Descriptors | File handle count | `process_open_fds` |

---

## ⚙️ Environment Variables

The app reads these from your `.env` file (or set them in `docker-compose.yml`):

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `3000` | App listen port |
| `SECRET_KEY` | `nowshare-docker-dev-key` | Flask session key |
| `MONGO_URI` | *(empty)* | MongoDB Atlas URI (optional) |
| `MAX_FILE_SIZE_MB` | `100` | Max upload size |
| `FILE_EXPIRY_MINUTES` | `10` | Auto-delete timer |
| `FLASK_DEBUG` | `false` | Debug mode |

> **Note:** The app works without `MONGO_URI` — the contact form will be disabled, but file sharing works fine.

---

## 🧪 Verification Steps

### 1. Verify App is Running

```bash
curl http://localhost:3000/health
```
**Expected:** `{"app":"nowshare","status":"healthy","version":"1.0.0"}`

### 2. Verify Metrics Endpoint

```bash
curl http://localhost:3000/metrics
```
**Expected:** Prometheus text format with `flask_http_requests_total`, `flask_http_request_duration_seconds`, etc.

### 3. Verify Prometheus is Scraping

```bash
curl http://localhost:9090/api/v1/targets
```
**Expected:** JSON with `"health": "up"` for the `nowshare-app` target.

Or visit http://localhost:9090/targets in your browser — the `nowshare-app` target should show **UP** in green.

### 4. Verify Grafana Shows Data

1. Open http://localhost:3001
2. Login with `admin` / `admin`
3. Go to **Dashboards** → **NowShare — Production Dashboard**
4. Panels should show live data within 30 seconds

### 5. Generate Test Traffic

```bash
# Upload a file
curl -X POST -F "file=@README.md" http://localhost:3000/upload

# Hit various endpoints to generate metrics
curl http://localhost:3000/
curl http://localhost:3000/get_history
curl http://localhost:3000/nonexistent
```

---

## 🧠 Troubleshooting

### Docker Networking Issues

**Problem:** Prometheus can't reach the app (`context deadline exceeded`)

**Fix:** Services communicate via Docker Compose service names, not `localhost`.
- ✅ Correct: `app:3000`
- ❌ Wrong: `localhost:3000`

This is already configured correctly in `monitoring/prometheus/prometheus.yml`.

---

### Port Conflicts

**Problem:** `docker-compose up` fails with "port already in use"

**Fix:**
```bash
# Find what's using the port (Windows)
netstat -ano | findstr :3000

# Kill the process
taskkill /PID <PID> /F

# Or change ports in docker-compose.yml:
# "3000:3000" → "3002:3000"  (app)
# "9090:9090" → "9091:9090"  (prometheus)
# "3001:3000" → "3003:3000"  (grafana)
```

---

### Metrics Endpoint Not Reachable

**Problem:** `curl http://localhost:3000/metrics` returns error

**Possible causes:**
1. App container not running — check `docker-compose ps`
2. App crashed on startup — check `docker-compose logs app`
3. Port not exposed — ensure `ports: "3000:3000"` in docker-compose.yml

**Fix:**
```bash
# Check container status
docker-compose ps

# View app logs
docker-compose logs -f app
```

---

### Prometheus Scrape Failures

**Problem:** Prometheus targets page shows target as **DOWN**

**Fix:**
1. Check Prometheus logs: `docker-compose logs prometheus`
2. Verify the app is healthy: `docker-compose exec prometheus wget -qO- http://app:3000/metrics`
3. If app is still starting, wait for health check to pass (15s start period)

---

### Grafana Connection Issues

**Problem:** Grafana shows "No data" on dashboard panels

**Possible causes:**
1. Prometheus data source not configured — check **Settings → Data Sources**
2. Prometheus not scraping — check http://localhost:9090/targets
3. No traffic generated yet — hit the app endpoints to create metrics

**Fix:**
```bash
# Generate some traffic
for i in {1..10}; do curl -s http://localhost:3000/ > /dev/null; done

# Wait 30 seconds for Prometheus to scrape, then check Grafana
```

---

### Container Restart Loops

**Problem:** `docker-compose ps` shows containers restarting

**Fix:**
```bash
# Check which container is failing
docker-compose ps

# View logs for the failing container
docker-compose logs --tail=50 <service-name>

# Common causes:
# - app: Missing dependency → rebuild with --no-cache
docker-compose build --no-cache app

# - prometheus: Bad config → validate prometheus.yml
docker run --rm -v ./monitoring/prometheus:/etc/prometheus prom/prometheus:v2.51.0 promtool check config /etc/prometheus/prometheus.yml

# - grafana: Permission issues on volume
docker-compose down -v && docker-compose up -d
```

---

### Missing Dependencies

**Problem:** App fails to start with `ModuleNotFoundError`

**Fix:**
```bash
# Rebuild the app image without cache
docker-compose build --no-cache app
docker-compose up -d app
```

---

### Railway Deployment Limitations

**Note:** This Docker Compose setup is for **local development monitoring only**. On Railway:
- Prometheus and Grafana are NOT deployed (Railway doesn't support multi-container with Docker Compose)
- The `/metrics` endpoint is available on your Railway deployment at `https://share-now.up.railway.app/metrics`
- For production monitoring on Railway, use external Prometheus (e.g., Grafana Cloud Free Tier) that scrapes your Railway endpoint

---

## ☁️ Kubernetes Setup (Optional — Minikube)

### Prerequisites

```bash
# Install Minikube
# Windows: winget install minikube
# Mac: brew install minikube
# Linux: curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64

# Start Minikube
minikube start
```

### Build App Image in Minikube

```bash
# Point Docker to Minikube's Docker daemon
eval $(minikube docker-env)    # Mac/Linux
# Windows PowerShell:
& minikube -p minikube docker-env --shell powershell | Invoke-Expression

# Build the app image inside Minikube
docker build -t nowshare-app:latest .
```

### Deploy All Manifests

```bash
# Apply all Kubernetes manifests in order
kubectl apply -f k8s/namespace.yml
kubectl apply -f k8s/app-deployment.yml
kubectl apply -f k8s/app-service.yml
kubectl apply -f k8s/prometheus-configmap.yml
kubectl apply -f k8s/prometheus-deployment.yml
kubectl apply -f k8s/prometheus-service.yml
kubectl apply -f k8s/grafana-deployment.yml
kubectl apply -f k8s/grafana-service.yml

# Or apply all at once:
kubectl apply -f k8s/
```

### Access Services

```bash
# Get Minikube IP
minikube ip

# Access services:
# App:        http://<minikube-ip>:30000
# Prometheus: http://<minikube-ip>:30090
# Grafana:    http://<minikube-ip>:30010

# Or use minikube service:
minikube service nowshare-app -n nowshare
minikube service prometheus -n nowshare
minikube service grafana -n nowshare
```

### Create Secrets (Optional — for MongoDB)

```bash
kubectl create secret generic nowshare-secrets \
  --from-literal=secret-key='your-secret-key' \
  --from-literal=mongo-uri='mongodb+srv://...' \
  -n nowshare
```

### Tear Down

```bash
kubectl delete namespace nowshare
```

---

## 📋 Commands Reference

| Action | Command |
|--------|---------|
| Start all services | `docker-compose up -d --build` |
| Stop all services | `docker-compose down` |
| View logs | `docker-compose logs -f` |
| View specific service logs | `docker-compose logs -f app` |
| Rebuild without cache | `docker-compose build --no-cache` |
| Check service status | `docker-compose ps` |
| Enter app container | `docker-compose exec app sh` |
| Enter Prometheus container | `docker-compose exec prometheus sh` |
| Restart a service | `docker-compose restart app` |
| Remove all data | `docker-compose down -v` |
