# ClothCRM

ClothCRM is the internal back-office customer relationship management (CRM) and system dashboard for a wholesale clothing distribution company.

## Tech Stack
- **Backend:** Python 3.11, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, Jinja2 Templates
- **Frontend:** HTML/CSS/JS, Bootstrap 5, Chart.js
- **Database:** PostgreSQL 15 (DigitalOcean Managed PostgreSQL in Production)
- **Containerization:** Docker, Docker Compose, Nginx (for proxying & caching)
- **CI/CD:** GitHub Actions

---

## Getting Started

### Option 1: Running Locally (Development)

1. **Prerequisites:** Python 3.11 installed locally.
2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   ```
3. **Activate virtual environment:**
   - **Windows PowerShell:**
     ```powershell
     .venv\Scripts\Activate.ps1
     ```
   - **Git Bash / macOS / Linux:**
     ```bash
     source .venv/bin/activate
     ```
4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
5. **Set up Environment Variables:**
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   Modify `DATABASE_URL` in `.env` to point to your local PostgreSQL instance (e.g., `postgresql://postgres:1111111@localhost:5432/clothcrm`).
6. **Start the Application:**
   ```bash
   uvicorn app.main:app --reload
   ```

### Option 2: Running with Docker Compose (Recommended)

Docker Compose automatically spins up the FastAPI application and a PostgreSQL database.

1. **Start Services:**
   ```bash
   docker-compose up --build
   ```
2. **Stop Services:**
   ```bash
   docker-compose down
   ```

---

## Verification and Testing

You can verify and run tests locally via pytest:
```bash
.venv\Scripts/python -m pytest -v tests/
```

Once the application is running, you can access:
- **Dashboard (Home Page):** [http://localhost:8000/](http://localhost:8000/)
- **Health Check API:** [http://localhost:8000/health](http://localhost:8000/health)

---

## Production Deployment on DigitalOcean

ClothCRM uses a secure, production-ready cloud architecture on DigitalOcean:
- **VPC Network:** Groups Droplets and Database inside a private network, shielding DB access from the public internet.
- **Managed Database:** A highly-available managed PostgreSQL 15 instance.
- **Nginx & Docker Compose:** Containerized reverse proxy and Gunicorn web server inside a DigitalOcean Droplet.
- **Load Balancer:** Standard DO Load Balancer handling SSL termination and distributing traffic.

### Step-by-Step Setup Guide

#### 1. Setup VPC Network
- Go to the DigitalOcean console -> **VPC Networks** -> **Create VPC Network**.
- Select your target region (e.g. `nyc1`) and name it `clothcrm-vpc`. Keep default IP ranges.

#### 2. Create DigitalOcean Managed PostgreSQL Database
- Navigate to **Databases** -> **Create Database Cluster**.
- Select **PostgreSQL 15**. Select the same region (e.g. `nyc1`).
- Under **Network Details**, choose your newly created `clothcrm-vpc` network.
- Complete the creation of the cluster.
- Once created, go to the **Connection Details** tab, switch the network mode to **Private Network**, and copy the private Connection String. (It should have host suffix like `.private.ondigitalocean.com`).

#### 3. Spin Up Droplet
- Navigate to **Droplets** -> **Create Droplet**.
- Choose Ubuntu 22.04 LTS. Select the same region (e.g. `nyc1`).
- Under **VPC Network**, select `clothcrm-vpc` to enable private networking.
- Choose SSH keys for authentication.
- Create the Droplet. Note down its public IP address (for deployment) and private IP.

#### 4. Configure Droplet Environment & Docker
- SSH into the Droplet:
  ```bash
  ssh root@your_droplet_public_ip
  ```
- Install Docker and Docker Compose:
  ```bash
  apt-get update
  apt-get install -y docker.io docker-compose-v2
  systemctl enable docker
  systemctl start docker
  ```
- Create the deployment directory `/app/clothcrm` and clone the repository inside it.
- Create `/app/clothcrm/.env.production` based on `.env.production.example` and input your private DB connection string:
  ```bash
  DATABASE_URL=postgresql://doadmin:[password]@your-db-host.private.ondigitalocean.com:25060/clothcrm?sslmode=require
  SECRET_KEY=your_generated_secure_secret_key
  ENV=production
  ```

#### 5. Configure DigitalOcean Load Balancer (SSL Termination)
- Go to **Networking** -> **Load Balancers** -> **Create Load Balancer**.
- Select the same region. Choose the `clothcrm-vpc` network.
- Add your newly created Droplet as the backend target.
- Set up **Forwarding Rules**:
  - HTTP: Forward port `80` to backend Droplet port `80`.
  - HTTPS: Forward port `443` (SSL terminated using a Let's Encrypt certificate managed by DigitalOcean) to backend Droplet port `80`.
- In the Load Balancer settings, enable **Redirect HTTP to HTTPS** to automatically secure traffic.

#### 6. Configure DigitalOcean Firewalls (Security Rules)
To lock down the infrastructure, create a Cloud Firewall:
- **Inbound Rules:**
  - HTTP (Port 80): Restrict source to **Load Balancers** only.
  - HTTPS (Port 443): Restrict source to **Load Balancers** only.
  - SSH (Port 22): Restrict source to your corporate IP addresses (or keep public but configure SSH keys only).
- **Outbound Rules:**
  - Allow all outbound traffic.
- Assign the firewall to your Droplet.

---

## CI/CD Pipeline (GitHub Actions)

When you push code to the `main` branch, the pipeline triggers automatically:
1. **Lint & Test:** Runs tests inside a containerized PostgreSQL environment.
2. **Build:** Builds the production Docker image using `Dockerfile.prod` (multi-stage, non-root).
3. **Registry:** Pushes the production Docker image to GitHub Container Registry (GHCR).
4. **Deploy:** Logs in to the Droplet via SSH, pulls the new image, runs migrations, and restarts the containers.

### GitHub Secrets Setup
To enable the pipeline, configure the following secrets in your GitHub Repository under **Settings** -> **Secrets and variables** -> **Actions**:
- `SSH_HOST`: The public IP address of your DigitalOcean Droplet.
- `SSH_USER`: The SSH login username (usually `root`).
- `SSH_PRIVATE_KEY`: Your SSH private key corresponding to the public key authorized on the Droplet.
- `GITHUB_TOKEN`: Automatically provided by GitHub (requires write permissions to write packages to GHCR).


nima gap?
what's up?

heading 2