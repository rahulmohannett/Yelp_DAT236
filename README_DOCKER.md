# Docker Setup Guide - Yelp Prototype

## Prerequisites

- Docker Desktop (with Docker Compose)
- Git
- `.env` file with API keys

## Environment Setup

Before running docker-compose, ensure you have a `.env` file in the project root:

```bash
# Example .env file
GOOGLE_API_KEY=your_google_gemini_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

## Quick Start

### 1. Build and Start the Full Stack

```bash
docker compose up --build
```

This will start 6 services:
- **mysql** (localhost:3306) - Database
- **user-service** (localhost:8001) - Auth, profile, favorites, history
- **restaurant-service** (localhost:8002) - Restaurants, AI chatbot
- **review-service** (localhost:8003) - Reviews
- **owner-service** (localhost:8004) - Owner dashboard
- **frontend** (localhost:80) - React SPA

### 2. Access the Application

- **Frontend**: http://localhost
- **API Docs**:
  - User Service: http://localhost:8001/docs
  - Restaurant Service: http://localhost:8002/docs
  - Review Service: http://localhost:8003/docs
  - Owner Service: http://localhost:8004/docs

### 3. Test Login

Use the pre-seeded test accounts:
- **Customer**: customer@test.com / password
- **Owner**: owner@test.com / password

## Database Operations

### View Database Logs

```bash
docker compose logs mysql
```

### Connect to MySQL Directly

```bash
docker exec -it yelp-mysql mysql -u root -prootpass yelp_db
```

### Reset Database

```bash
# Stop services
docker compose down

# Remove database volume
docker volume rm yelp-prototype_mysql_data

# Restart (will reinitialize from init.sql)
docker compose up
```

## Service Development

### View Logs for a Specific Service

```bash
docker compose logs user-service -f
docker compose logs restaurant-service -f
docker compose logs review-service -f
docker compose logs owner-service -f
```

### Restart a Single Service

```bash
docker compose restart user-service
```

### Execute Commands in a Container

```bash
# Access user service shell
docker compose exec user-service /bin/bash

# Run a Python command
docker compose exec user-service python -c "print('hello')"
```

## Troubleshooting

### Services Won't Connect to MySQL

Check MySQL health:
```bash
docker compose ps
# Look for "mysql" service status
```

If MySQL isn't healthy, check logs:
```bash
docker compose logs mysql
```

### API Keys Not Working

Verify your `.env` file has the correct keys:
```bash
docker compose config | grep GOOGLE_API_KEY
docker compose config | grep TAVILY_API_KEY
```

### Port Conflicts

If ports are already in use:
```bash
# Change ports in docker-compose.yml or:
lsof -i :80
lsof -i :3306
# Kill the process using the port
```

### Frontend Nginx Proxy Issues

Check nginx logs:
```bash
docker compose exec frontend cat /var/log/nginx/error.log
```

Verify backend services are responding:
```bash
docker compose exec frontend curl http://user-service:8001/health
docker compose exec frontend curl http://restaurant-service:8002/health
```

## File Structure

```
project_root/
├── docker-compose.yml       # Full stack orchestration
├── .env                     # Environment variables (not in git)
├── frontend/
│   ├── Dockerfile           # Multi-stage React build + nginx
│   ├── nginx.conf           # Nginx reverse proxy config
│   ├── package.json
│   ├── src/
│   └── dist/               # Built by Docker (not in git)
├── backend/
│   ├── Dockerfile           # Python 3.13 FastAPI
│   ├── app/
│   │   ├── main_user.py        # User service entrypoint
│   │   ├── main_restaurant.py  # Restaurant service entrypoint
│   │   ├── main_review.py      # Review service entrypoint
│   │   ├── main_owner.py       # Owner service entrypoint
│   │   ├── main.py            # Original monolithic (for local dev)
│   │   ├── routers/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── ...
│   ├── requirements.txt
│   ├── uploads/             # Shared volume
│   └── .env               # Backend-specific env (optional)
└── database/
    └── init.sql            # Database initialization script
```

## CI/CD Considerations

For production deployments:

1. Use secrets management (AWS Secrets Manager, HashiCorp Vault, etc.)
2. Push images to a registry (Docker Hub, ECR, etc.)
3. Use environment-specific docker-compose files
4. Add resource limits to prevent runaway containers
5. Implement proper logging and monitoring

## Development Workflow

For active development:

```bash
# Start services in background
docker compose up -d

# Watch logs in real-time
docker compose logs -f

# Make code changes - services auto-reload due to volume mounts
# Edit backend/app/routers/auth.py for example
# Changes are reflected immediately (uvicorn --reload)

# Stop when done
docker compose down
```

## Next Steps

Once comfortable with docker-compose, move to Kubernetes (see `k8s/README.md`).

For single-host AWS deployment, use the EC2 production override and runbook in `EC2_DEPLOYMENT.md`.