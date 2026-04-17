# Deployment Guide - Billing ERP System

## Table of Contents
1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Heroku Deployment](#heroku-deployment)
4. [AWS Deployment](#aws-deployment)
5. [Production Checklist](#production-checklist)
6. [Monitoring & Maintenance](#monitoring--maintenance)

## Local Development

### Prerequisites
- Python 3.11+
- PostgreSQL 14+ (optional, SQLite for dev)
- Redis (optional, for Celery)

### Setup Steps
```bash
# Clone repository
git clone <repo-url>
cd billing_softwareerp

# Run setup script
chmod +x setup.sh
./setup.sh
# OR on Windows
setup.bat

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

### Run Development Server
```bash
python manage.py runserver
```

Access at: http://localhost:8000

## Docker Deployment

### Using Docker Compose (Recommended for Local)

```bash
# Start services
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput
```

Access at: http://localhost:8000

### Building Custom Image
```bash
# Build image
docker build -t billing-erp:latest .

# Run container
docker run -d -p 8000:8000 \
  -e DEBUG=False \
  -e SECRET_KEY=your-secret-key \
  -e DB_ENGINE=postgresql \
  -e DB_HOST=db-host \
  billing-erp:latest
```

## Heroku Deployment

### Prerequisites
- Heroku account
- Heroku CLI installed

### Deployment Steps

1. **Prepare app for Heroku:**
```bash
# Create Procfile
echo "web: gunicorn config.wsgi --log-file -" > Procfile

# Create runtime.txt
echo "python-3.11.10" > runtime.txt
```

2. **Create Heroku app:**
```bash
heroku login
heroku create billing-erp-app
```

3. **Configure environment variables:**
```bash
heroku config:set SECRET_KEY="your-secret-key"
heroku config:set DEBUG=False
heroku config:set ALLOWED_HOSTS="billing-erp-app.herokuapp.com"
```

4. **Add PostgreSQL database:**
```bash
heroku addons:create heroku-postgresql:standard-0
```

5. **Deploy:**
```bash
git push heroku main

# Run migrations
heroku run python manage.py migrate

# Create superuser
heroku run python manage.py createsuperuser

# View logs
heroku logs --tail
```

6. **Access application:**
```
https://billing_erp_app.herokuapp.com
```

## Render Deployment

### Prerequisites
- [Render](https://render.com/) account
- GitHub or GitLab repository containing this code

### Deployment Steps (The Easy Way)

1. **Connect Repository:**
   - Log in to your Render Dashboard.
   - Click **New +** and select **Blueprint**.
   - Connect your GitHub/GitLab repository.

2. **Deploy:**
   - Render will automatically detect the `render.yaml` file I created.
   - It will show a list of services to be created (Web Service, Database, Redis).
   - Click **Apply**.

3. **Post-Deployment:**
   - Once the database is ready, the web service will build using the `Dockerfile`.
   - The initial migration will run automatically if defined, but you can manually run them via the Render Shell:
     ```bash
     python manage.py migrate
     python manage.py createsuperuser
     ```

### Manual Configuration (Web Service)

If you prefer to set it up manually:
- **Service Type**: Web Service
- **Runtime**: Docker
- **Environment Variables**:
  - `DEBUG`: `False`
  - `SECRET_KEY`: (generate a random string)
  - `DB_ENGINE`: `postgresql`
  - `DATABASE_URL`: (from your Render Postgres instance)
  - `CELERY_BROKER_URL`: (from your Render Redis instance)

## AWS Deployment

### Architecture
- EC2 for application server
- RDS for PostgreSQL database
- ElastiCache for Redis
- S3 for media files
- CloudFront for CDN

### Prerequisites
- AWS account
- AWS CLI configured

### Step 1: Create EC2 Instance

```bash
# Create security group
aws ec2 create-security-group \
  --group-name billing-erp-sg \
  --description "Security group for Billing ERP"

# Authorize ports
aws ec2 authorize-security-group-ingress \
  --group-name billing-erp-sg \
  --protocol tcp --port 80 --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-name billing-erp-sg \
  --protocol tcp --port 443 --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-name billing-erp-sg \
  --protocol tcp --port 22 --cidr YOUR_IP/32
```

### Step 2: Create RDS Database

```bash
aws rds create-db-instance \
  --db-instance-identifier billing-erp-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username admin \
  --master-user-password your-secure-password \
  --allocated-storage 20
```

### Step 3: Create ElastiCache Redis Cluster

```bash
aws elasticache create-cache-cluster \
  --cache-cluster-id billing-erp-cache \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1
```

### Step 4: Deploy Application

1. Connect to EC2 instance:
```bash
ssh -i your-key.pem ec2-user@your-instance-ip
```

2. Install dependencies:
```bash
sudo yum update -y
sudo yum install python3 python3-pip git postgresql -y
sudo pip3 install --upgrade pip
```

3. Clone and setup:
```bash
git clone <repo-url>
cd billing_softwareerp
pip3 install -r requirements.txt

# Configure .env file
cp .env.example .env
# Edit .env with AWS RDS and ElastiCache endpoints
```

4. Run migrations and collect static:
```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

5. Configure Gunicorn and Nginx:

Create `/etc/systemd/system/billing-erp.service`:
```ini
[Unit]
Description=Billing ERP Gunicorn Service
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/billing_softwareerp
ExecStart=/usr/local/bin/gunicorn config.wsgi:application --workers 4 --bind 127.0.0.1:8000

[Install]
WantedBy=multi-user.target
```

Start service:
```bash
sudo systemctl start billing-erp
sudo systemctl enable billing-erp
```

### Step 5: Configure Nginx

Install Nginx:
```bash
sudo yum install nginx -y
```

Create `/etc/nginx/conf.d/billing-erp.conf`:
```nginx
upstream gunicorn {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;
    
    location /static/ {
        alias /home/ec2-user/billing_softwareerp/staticfiles/;
    }
    
    location /media/ {
        alias /home/ec2-user/billing_softwareerp/media/;
    }
    
    location / {
        proxy_pass http://gunicorn;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Start Nginx:
```bash
sudo systemctl start nginx
sudo systemctl enable nginx
```

### Step 6: SSL Certificate (Let's Encrypt)

```bash
sudo yum install certbot certbot-nginx -y
sudo certbot certonly --standalone -d your-domain.com
```

## Production Checklist

- [ ] Set `DEBUG = False` in production
- [ ] Update `SECRET_KEY` to a secure random value
- [ ] Configure `ALLOWED_HOSTS` with your domain
- [ ] Set up HTTPS/SSL certificates
- [ ] Enable CSRF protection and security headers
- [ ] Configure database backups (daily recommended)
- [ ] Set up email for notifications
- [ ] Enable logging and monitoring
- [ ] Create superuser account
- [ ] Test all critical workflows
- [ ] Set up monitoring alerts
- [ ] Configure rate limiting
- [ ] Implement firewall rules
- [ ] Enable automated backups
- [ ] Test disaster recovery process

## Monitoring & Maintenance

### Health Checks

```bash
# Check application health
curl -H "Authorization: Token YOUR_TOKEN" http://localhost:8000/api/v1/customers/

# Check database
python manage.py dbshell
```

### Backup Strategy

```bash
# Database backup (PostgreSQL)
pg_dump -U username dbname > backup_$(date +%Y%m%d).sql

# Media files backup
tar -czf media_backup_$(date +%Y%m%d).tar.gz media/

# Regular automated backups (cron job)
# 0 2 * * * pg_dump -U admin billing_erp > /backups/db_$(date +\%Y\%m\%d).sql
```

### Log Monitoring

```bash
# View Django logs
tail -f logs/erp.log

# View Celery logs
tail -f logs/celery.log

# View Nginx logs
tail -f /var/log/nginx/access.log
```

### Performance Tuning

1. Database optimization:
   - Create indexes on frequently queried fields
   - Analyze query plans
   - Enable query caching

2. Application optimization:
   - Enable Redis caching
   - Use CDN for static files
   - Optimize database queries

3. Server optimization:
   - Adjust worker count: `workers = 2 * CPU_CORES + 1`
   - Configure Nginx caching
   - Enable gzip compression

### Security Updates

```bash
# Regular dependency updates
pip install --upgrade pip
pip install -r requirements.txt --upgrade

# Update system packages
sudo yum update -y
sudo apt-get update && apt-get upgrade -y
```

## Troubleshooting

### Common Issues

1. **Database Connection Error:**
   - Check database credentials in .env
   - Verify database is running
   - Check network connectivity

2. **Static Files Not Loading:**
   ```bash
   python manage.py collectstatic --noinput
   ```

3. **Permission Issues:**
   ```bash
   chmod -R 755 media/
   sudo chown -R www-data:www-data /var/www/billing-erp
   ```

4. **Out of Memory:**
   - Reduce worker count in Gunicorn
   - Enable swap space
   - Optimize database queries

### Getting Help

- Check logs: `tail -f logs/erp.log`
- Run migrations: `python manage.py migrate`
- Test settings: `python manage.py check`

## Additional Resources

- [Django Deployment Documentation](https://docs.djangoproject.com/en/4.2/howto/deployment/)
- [Gunicorn Configuration](https://docs.gunicorn.org/en/stable/)
- [Nginx Configuration](https://nginx.org/en/docs/)
- [PostgreSQL Backups](https://www.postgresql.org/docs/14/backup.html)

---

**Last Updated**: April 1, 2026
