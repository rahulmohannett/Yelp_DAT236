# EC2 Deployment Guide (Docker Compose)

This guide deploys Yelp Prototype on a single Ubuntu EC2 instance using Docker Compose.

## 1) Provision EC2

- AMI: Ubuntu 22.04 LTS
- Instance type: at least `t3.large` (CPU/memory headroom for Kafka + services)
- Storage: 30GB+ gp3
- Security Group inbound:
  - `22` (SSH) from your IP
  - `80` (HTTP) from `0.0.0.0/0`
  - `443` (HTTPS) from `0.0.0.0/0` (if using TLS)

Do not open backend ports (`8001-8006`, `9092`, `27017`) publicly.

## 2) Install Docker + Compose plugin

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
```

Log out and back in after adding your user to the docker group.

## 3) Configure environment

```bash
cp .env.ec2.example .env
```

Set real values in `.env`:

- `GOOGLE_API_KEY`
- `TAVILY_API_KEY`
- `SECRET_KEY` (strong random secret)
- `CORS_ORIGINS` (your real frontend domains only)

## 4) Start production stack

```bash
docker compose -f docker-compose.yml -f docker-compose.ec2.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.ec2.yml ps
```

Health checks:

```bash
curl -f http://localhost/health
curl -f http://localhost/auth/login -X OPTIONS
```

## 5) Operate and monitor

Logs:

```bash
docker compose -f docker-compose.yml -f docker-compose.ec2.yml logs -f
```

Restart one service:

```bash
docker compose -f docker-compose.yml -f docker-compose.ec2.yml restart user-service
```

Pull down stack:

```bash
docker compose -f docker-compose.yml -f docker-compose.ec2.yml down
```

## 6) TLS (recommended)

Put an ALB or Nginx reverse proxy with TLS in front of this EC2 instance and terminate HTTPS there.
If you stay direct-to-instance, install Certbot and terminate TLS on host nginx.

## 7) Recommended next hardening

- Move secrets to AWS Systems Manager Parameter Store or Secrets Manager.
- Set up CloudWatch Agent for logs and metrics.
- Add automatic backups/snapshots for data volumes.
- Add a CI pipeline that builds and pushes images (ECR) for predictable deploys.
