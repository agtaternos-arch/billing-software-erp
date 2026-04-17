# Billing ERP System

A lightweight, comprehensive ERP (Enterprise Resource Planning) system built with Python and Django. Designed for small to medium-sized businesses with modular architecture for easy feature expansion.

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

## ✨ Features

### Core Modules

1. **Authentication & Authorization**
   - Role-based access control (Admin, Staff, Viewer)
   - Secure login/logout with session management
   - User profile management
   - Audit logging for all user actions

2. **Billing System**
   - Create and manage invoices
   - Track payments (multiple payment methods)
   - Expense tracking and categorization
   - PDF/Excel export functionality
   - Invoice status tracking (Draft, Sent, Paid, Overdue, etc.)

3. **Inventory Management**
   - Product catalog with SKU tracking
   - Real-time stock level management
   - Low stock alerts
   - Supplier management
   - Purchase order system
   - Stock movement history

4. **Customer Management**
   - Comprehensive customer database
   - Contact person management
   - Purchase history tracking
   - Customer segmentation
   - Credit limit management

5. **Reports & Analytics**
   - Sales reports with charts
   - Inventory analysis
   - Profit & Loss statements
   - Customer performance metrics
   - Expense reports by category
   - Interactive dashboards

6. **Advanced Features**
   - REST API endpoints for all modules
   - Responsive web interface with Bootstrap
   - Real-time notifications
   - Batch operations
   - Data export (PDF, Excel)
   - AI-powered stock prediction (ML-based)

## 🛠️ Tech Stack

- **Backend**: Django 4.2
- **API**: Django REST Framework
- **Database**: PostgreSQL / SQLite
- **Frontend**: HTML5, CSS3, Bootstrap 5
- **Task Queue**: Celery with Redis
- **Charting**: Chart.js, Matplotlib
- **Reporting**: ReportLab, Openpyxl, Pandas
- **ML/AI**: Scikit-learn, Pandas
- **Deployment**: Docker, Gunicorn, Nginx
- **Testing**: pytest, factory-boy

## 📦 Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 14+ (or use SQLite for development)
- Redis (optional, for Celery tasks)
- Docker & Docker Compose (optional, for containerized deployment)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd billing_softwareerp
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create .env file**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your configuration.

5. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Collect static files**
   ```bash
   python manage.py collectstatic --noinput
   ```

### Docker Setup

```bash
# Build and start containers
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# View logs
docker-compose logs -f web
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com

# Database
DB_ENGINE=postgresql
DB_NAME=billing_erp
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432

# Security (set to True in production)
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False

# Celery & Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-password
```

## 🚀 Running the Application

### Development Server

```bash
python manage.py runserver
```

Access the application at `http://localhost:8000`

### Production Server (with Gunicorn)

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### Celery Workers (for async tasks)

```bash
# Start worker
celery -A config worker -l info

# Start beat scheduler
celery -A config beat -l info
```

## 📚 API Documentation

### Base URL
```
http://localhost:8000/api/v1/
```

### Authentication
All API endpoints require authentication. Use token authentication:

```bash
curl -H "Authorization: Token YOUR_TOKEN" http://localhost:8000/api/v1/customers/
```

### Main Endpoints

**Customers**
- `GET /api/v1/customers/` - List all customers
- `POST /api/v1/customers/` - Create customer
- `GET /api/v1/customers/{id}/` - Get customer details
- `PATCH /api/v1/customers/{id}/` - Update customer
- `DELETE /api/v1/customers/{id}/` - Delete customer

**Products**
- `GET /api/v1/products/` - List all products
- `POST /api/v1/products/` - Create product
- `GET /api/v1/products/low_stock/` - Get low stock items
- `POST /api/v1/products/{id}/adjust_stock/` - Adjust stock level

**Invoices**
- `GET /api/v1/invoices/` - List invoices
- `POST /api/v1/invoices/` - Create invoice
- `GET /api/v1/invoices/overdue/` - Get overdue invoices
- `POST /api/v1/invoices/{id}/mark_paid/` - Mark invoice as paid

**Payments**
- `POST /api/v1/payments/` - Record payment
- `GET /api/v1/payments/` - List payments

**Reports**
- `GET /api/v1/sales-reports/` - Sales reports
- `GET /api/v1/inventory-reports/` - Inventory reports
- `GET /api/v1/p-and-l/` - Profit & Loss statements

## 📁 Project Structure

```
billing_softwareerp/
├── apps/
│   ├── accounts/                # Authentication & user management
│   │   ├── models.py           # UserProfile, AuditLog
│   │   ├── views.py            # Login, registration, profile
│   │   ├── forms.py            # Auth forms
│   │   ├── decorators.py       # Role-based access control
│   │   └── urls.py
│   ├── billing/                # Invoice & payment management
│   │   ├── models.py           # Invoice, Payment, Expense
│   │   ├── views.py            # Billing views
│   │   └── forms.py
│   ├── inventory/              # Product & stock management
│   │   ├── models.py           # Product, StockMovement, PurchaseOrder
│   │   ├── views.py            # Inventory views
│   │   └── forms.py
│   ├── customers/              # Customer management
│   │   ├── models.py           # Customer, ContactPerson
│   │   ├── views.py            # Customer views
│   │   └── forms.py
│   ├── reports/                # Reports & analytics
│   │   ├── models.py           # Report models
│   │   ├── views.py            # Report generation
│   │   └── forms.py
│   └── api/                    # REST API
│       ├── serializers.py      # DRF serializers
│       ├── views.py            # API viewsets
│       └── urls.py
├── config/                     # Project settings
│   ├── settings.py             # Django settings
│   ├── urls.py                 # URL routing
│   ├── wsgi.py                 # WSGI configuration
│   └── celery.py               # Celery configuration
├── templates/                  # HTML templates
│   ├── base.html              # Base template
│   ├── dashboard.html         # Dashboard
│   ├── accounts/              # Auth templates
│   ├── billing/               # Billing templates
│   ├── inventory/             # Inventory templates
│   ├── customers/             # Customer templates
│   └── reports/               # Report templates
├── static/                    # Static files (CSS, JS, images)
│   ├── css/
│   ├── js/
│   └── images/
├── media/                     # User uploads (products, receipts)
├── logs/                      # Application logs
├── manage.py                  # Django management script
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker configuration
├── docker-compose.yml         # Docker Compose for local dev
├── .env.example              # Environment variables template
└── README.md                 # This file
```

## 🚢 Deployment

### Heroku Deployment

1. **Install Heroku CLI**
   ```bash
   brew install heroku/brew/heroku
   ```

2. **Login to Heroku**
   ```bash
   heroku login
   ```

3. **Create procfile**
   ```bash
   echo "web: gunicorn config.wsgi --log-file -" > Procfile
   ```

4. **Deploy**
   ```bash
   git push heroku main
   heroku run python manage.py migrate
   heroku run python manage.py createsuperuser
   ```

### AWS Deployment (EC2 + RDS)

See `deployment/AWS_SETUP.md` for detailed instructions.

## 🔐 Security Features

- CSRF protection on all forms
- SQL injection prevention (ORM/parameterized queries)
- Password hashing with PBKDF2
- Secure password reset via email
- Rate limiting on API endpoints
- HTTPS/SSL support
- Audit logging of all user actions
- Input validation on all forms
- XSS protection

## 📊 AI/ML Features

### Predictive Stock Alerts

The system includes an ML model for predicting stock requirements:

```python
# Example usage
from apps.inventory.ml import predict_stock_needs
prediction = predict_stock_needs(product_id=1, days_ahead=30)
```

Features:
- Historical sales trend analysis
- Seasonal adjustment
- Supplier lead time consideration
- Automatic reorder recommendations

## 📝 API Testing

```bash
# Install test requirements
pip install pytest pytest-django factory-boy faker

# Run tests
pytest

# Run with coverage
pytest --cov=apps
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

## 📧 Support

For support, email support@billingerp.com or create an issue in the repository.

## 🗺️ Roadmap

- [ ] Mobile app (React Native)
- [ ] Advanced reporting with BI integration
- [ ] Multi-currency support
- [ ] Workflow automation
- [ ] Approval workflows
- [ ] Budget management
- [ ] Multi-location support
- [ ] Accounting integration (QuickBooks, Xero)
- [ ] Inventory forecasting improvements
- [ ] Customer portal

## 📚 Additional Documentation

- [API Reference](docs/API.md)
- [Database Schema](docs/SCHEMA.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [User Manual](docs/USER_MANUAL.md)
- [Developer Guide](docs/DEVELOPER.md)

---

**Last Updated**: April 1, 2026
**Version**: 1.0.0
**Status**: Production Ready
