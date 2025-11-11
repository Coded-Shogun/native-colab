# Native Colab - Deployment Guide

Complete guide for deploying Native Colab to production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Docker Deployment](#docker-deployment)
4. [Manual Deployment](#manual-deployment)
5. [Cloud Providers](#cloud-providers)
6. [SSL/HTTPS Setup](#ssl-https-setup)
7. [Database Migration](#database-migration)
8. [Monitoring & Logging](#monitoring--logging)
9. [Scaling](#scaling)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required
- **Domain Name** - For SSL and production access
- **PostgreSQL 15+** - Production database
- **Docker & Docker Compose** - For containerized deployment
- **Minimum 2GB RAM** - For single server deployment
- **50GB Storage** - For application and file storage

### Recommended
- **Redis** - For caching and session management
- **S3/MinIO** - For file storage
- **CDN** - For static assets (CloudFlare, AWS CloudFront)
- **Load Balancer** - For high availability

---

## Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-org/native-colab.git
cd native-colab
```

### 2. Configure Environment Variables

**Backend (.env)**:
```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` with production values:
```env
# Database
DATABASE_URL=postgresql://user:password@postgres:5432/native_colab

# Security
SECRET_KEY=<generate-strong-random-key-min-32-chars>
CORS_ORIGINS=["https://yourdomain.com"]

# Email
SMTP_HOST=smtp.sendgrid.net
SMTP_USER=apikey
SMTP_PASSWORD=<your-sendgrid-api-key>

# Storage
S3_ENDPOINT=https://s3.amazonaws.com
S3_ACCESS_KEY=<your-aws-access-key>
S3_SECRET_KEY=<your-aws-secret-key>
S3_BUCKET=native-colab-production
```

**Frontend (.env)**:
```bash
cp frontend/.env.example frontend/.env
```

Edit `frontend/.env`:
```env
VITE_API_URL=https://api.yourdomain.com
VITE_SOCKET_URL=https://api.yourdomain.com
VITE_APP_ENVIRONMENT=production
```

### 3. Generate Secret Key

```bash
# Generate a secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Docker Deployment

### Quick Start (Recommended for Production)

1. **Build and Start Services**:

```bash
# Production deployment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

2. **Run Database Migrations**:

```bash
docker-compose exec backend alembic upgrade head
```

3. **Create Initial Admin User**:

```bash
docker-compose exec backend python -m app.scripts.create_admin \
  --email admin@yourdomain.com \
  --password <secure-password>
```

### Service URLs

- **Frontend**: http://localhost:3000 (or your domain)
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001

---

## Manual Deployment

### Backend Deployment

1. **Install Python Dependencies**:

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Run Migrations**:

```bash
alembic upgrade head
```

3. **Start with Gunicorn**:

```bash
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

### Frontend Deployment

1. **Build Production Bundle**:

```bash
cd frontend
npm install
npm run build
```

2. **Serve with Nginx**:

Create `/etc/nginx/sites-available/native-colab`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    root /var/www/native-colab/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /socket.io {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/native-colab /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Cloud Providers

### AWS Deployment

#### Using EC2 + RDS + S3

1. **Launch EC2 Instance** (t3.medium or larger)
2. **Create RDS PostgreSQL Instance** (db.t3.micro or larger)
3. **Create S3 Bucket** for file storage
4. **Configure Security Groups**:
   - Allow 80, 443 (HTTP/HTTPS)
   - Allow 22 (SSH)
   - Database: 5432 (PostgreSQL)

5. **Deploy Application**:

```bash
# SSH into EC2
ssh -i your-key.pem ubuntu@your-ec2-ip

# Clone and setup
git clone https://github.com/your-org/native-colab.git
cd native-colab

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Deploy
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### DigitalOcean Deployment

#### Using App Platform

1. **Create App**:
   - Frontend: Static Site from `frontend/` directory
   - Backend: Web Service from `backend/` directory

2. **Add Database**:
   - Create Managed PostgreSQL Database
   - Add connection string to environment variables

3. **Configure Build**:
   - Frontend Build Command: `npm install && npm run build`
   - Frontend Output Directory: `dist`
   - Backend Run Command: `gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker`

### Heroku Deployment

```bash
# Create apps
heroku create native-colab-api
heroku create native-colab-frontend

# Add PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev -a native-colab-api

# Deploy backend
cd backend
git push heroku main

# Deploy frontend
cd ../frontend
heroku buildpacks:set heroku/nodejs
git push heroku main
```

---

## SSL/HTTPS Setup

### Using Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Generate certificate
sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

### Using CloudFlare

1. Point your domain to CloudFlare nameservers
2. Enable SSL/TLS (Full or Full Strict)
3. Enable HSTS, Always Use HTTPS
4. Set up page rules for caching

---

## Database Migration

### Initial Setup

```bash
# Run all migrations
docker-compose exec backend alembic upgrade head

# Check current version
docker-compose exec backend alembic current

# Rollback one version
docker-compose exec backend alembic downgrade -1
```

### Creating New Migration

```bash
# Auto-generate migration from model changes
docker-compose exec backend alembic revision --autogenerate -m "description"

# Create empty migration
docker-compose exec backend alembic revision -m "description"
```

### Backup Before Migration

```bash
# Backup database
docker-compose exec postgres pg_dump -U postgres native_colab > backup_$(date +%Y%m%d).sql

# Restore if needed
docker-compose exec -T postgres psql -U postgres native_colab < backup_20231201.sql
```

---

## Monitoring & Logging

### Application Logs

```bash
# View backend logs
docker-compose logs -f backend

# View frontend logs
docker-compose logs -f frontend

# Export logs
docker-compose logs backend > backend_$(date +%Y%m%d).log
```

### Health Checks

```bash
# Backend health
curl https://api.yourdomain.com/health

# Database connection
curl https://api.yourdomain.com/health/db
```

### Error Tracking

#### Sentry Integration

1. **Create Sentry Project**: https://sentry.io

2. **Add to Backend**:
```python
# backend/app/main.py
import sentry_sdk
sentry_sdk.init(dsn="your-sentry-dsn")
```

3. **Add to Frontend**:
```env
VITE_SENTRY_DSN=your-sentry-dsn
VITE_SENTRY_ENVIRONMENT=production
```

### Performance Monitoring

#### Using Prometheus + Grafana

```bash
# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Access Grafana
http://localhost:3001 (admin/admin)
```

---

## Scaling

### Horizontal Scaling

#### Backend (Multiple Instances)

```bash
# Scale backend to 3 instances
docker-compose up -d --scale backend=3

# Add load balancer (nginx config)
upstream backend {
    server backend:8000;
    server backend:8001;
    server backend:8002;
}
```

#### Database (Read Replicas)

```yaml
# docker-compose.yml
postgres-replica:
  image: postgres:15
  environment:
    POSTGRES_MASTER_SERVICE_HOST: postgres
```

### Vertical Scaling

Increase resources in `docker-compose.yml`:

```yaml
backend:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 4G
      reservations:
        cpus: '1'
        memory: 2G
```

### Caching Strategy

Enable Redis caching:

```env
# backend/.env
REDIS_ENABLED=true
REDIS_URL=redis://redis:6379/0
```

---

## Troubleshooting

### Common Issues

#### Backend Won't Start

```bash
# Check logs
docker-compose logs backend

# Common fixes:
# 1. Database not ready
docker-compose up -d postgres
sleep 10
docker-compose up backend

# 2. Migration pending
docker-compose exec backend alembic upgrade head
```

#### Frontend Build Fails

```bash
# Clear cache
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

#### Database Connection Issues

```bash
# Test connection
docker-compose exec backend python -c "from app.core.database import engine; print(engine.url)"

# Check PostgreSQL
docker-compose exec postgres psql -U postgres -c "SELECT version();"
```

#### File Upload Errors

```bash
# Check S3/MinIO credentials
docker-compose exec backend python -c "from app.core.config import settings; print(settings.S3_BUCKET)"

# Test S3 connection
aws s3 ls s3://your-bucket
```

### Performance Issues

```bash
# Check resource usage
docker stats

# Optimize database
docker-compose exec postgres vacuumdb -U postgres -d native_colab --analyze

# Clear Redis cache
docker-compose exec redis redis-cli FLUSHALL
```

### Debug Mode

Enable debug logging:

```env
# backend/.env
DEBUG=true
LOG_LEVEL=DEBUG
```

---

## Security Checklist

- [ ] Change default admin password
- [ ] Generate strong SECRET_KEY
- [ ] Enable HTTPS/SSL
- [ ] Set up firewall rules
- [ ] Configure CORS properly
- [ ] Enable rate limiting
- [ ] Regular security updates
- [ ] Database backups automated
- [ ] Implement monitoring/alerting
- [ ] Review user permissions
- [ ] Enable audit logging

---

## Maintenance

### Regular Tasks

**Daily**:
- Check application logs
- Monitor error rates
- Verify backups completed

**Weekly**:
- Review performance metrics
- Check disk space
- Update dependencies (if needed)

**Monthly**:
- Security audit
- Database optimization
- Review user feedback
- Update documentation

### Backup Strategy

```bash
# Automated daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d)
docker-compose exec postgres pg_dump -U postgres native_colab | gzip > backup_$DATE.sql.gz
aws s3 cp backup_$DATE.sql.gz s3://your-backup-bucket/
find . -name "backup_*.sql.gz" -mtime +30 -delete
```

---

## Support

- **Documentation**: https://docs.nativecolab.com
- **Issues**: https://github.com/your-org/native-colab/issues
- **Email**: support@nativecolab.com

---

**Last Updated**: December 2024
**Version**: 1.0.0
