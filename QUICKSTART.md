# Quick Start Guide - Billing ERP System

## 5-Minute Setup

### On Windows:
```batch
# 1. Run setup script
setup.bat

# 2. Start development server
python manage.py runserver
```

### On Mac/Linux:
```bash
# 1. Make setup script executable
chmod +x setup.sh

# 2. Run setup script
./setup.sh

# 3. Start development server
python manage.py runserver
```

## First Login

**URL:** http://localhost:8000

**Default Credentials:**
- Username: `admin`
- Password: (created during setup)

## Main Features

### 1. Dashboard
- Real-time sales metrics
- Low stock alerts
- Overdue invoices
- Key performance indicators

### 2. Billing Module
- **Create Invoices:** /billing/invoices/
- **Track Payments:** /billing/payments/
- **Log Expenses:** /billing/expenses/
- Features: PDF export, payment tracking, invoice management

### 3. Inventory Management
- **Manage Products:** /inventory/products/
- **Supplier Management:** /inventory/suppliers/
- **Stock Tracking:** Real-time stock levels
- Features: Low stock alerts, ML-powered reorder recommendations

### 4. Customer Management
- **Customer Database:** /customers/
- **Contact Management:** Store multiple contacts per customer
- **Purchase History:** Track customer transactions

### 5. Reports & Analytics
- **Sales Reports:** /reports/
- **Inventory Analysis:** Stock level reports
- **Profit & Loss:** Financial statements
- **Export Options:** PDF, Excel download

## Admin Panel

Access Django admin: http://localhost:8000/admin

Manage all data models directly from the admin interface.

## API Endpoints

Base URL: `http://localhost:8000/api/v1/`

### Available Endpoints:
- `/customers/` - Customer management
- `/products/` - Product catalog
- `/invoices/` - Invoice management
- `/payments/` - Payment tracking
- `/reports/` - Financial reports

**Authentication:** Token-based (available in admin panel)

```bash
# Example request
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:8000/api/v1/customers/
```

## Docker Quick Start

```bash
# Start all services
docker-compose up -d

# Access application
# URL: http://localhost:8000
```

## File Structure

```
billing_softwareerp/
├── apps/                 # Core Django applications
│   ├── accounts/        # Authentication & users
│   ├── billing/         # Invoice & payments
│   ├── inventory/       # Products & stock
│   ├── customers/       # Customer management
│   ├── reports/         # Analytics & reports
│   └── api/             # REST API
├── templates/           # HTML templates
├── static/              # CSS, JS, images
├── config/              # Django configuration
├── manage.py            # Django management
└── requirements.txt     # Python dependencies
```

## Common Tasks

### Add a New User
```bash
python manage.py createsuperuser
# or via Admin: Admin > Users > Add User
```

### Create an Invoice
1. Go to Billing > Invoices
2. Click "Create Invoice"
3. Select customer, add items
4. Set due date and save
5. Option to send or export as PDF

### Import Stock
1. Go to Inventory > Products
2. Add product details
3. Set reorder point and initial stock
4. Save product

### Generate Reports
1. Go to Reports
2. Select report type (Sales, Inventory, P&L)
3. Choose date range
4. View or export (PDF/Excel)

## Troubleshooting

### Port Already in Use
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Mac/Linux
lsof -i :8000
kill -9 <PID>
```

### Database Errors
```bash
python manage.py migrate
python manage.py migrate --fake-initial
```

### Clear Cache
```bash
python manage.py flush
```

## Next Steps

1. **Customize Settings:**
   - Edit `.env` file
   - Configure email settings
   - Set up payment gateways

2. **Add Users:**
   - Create staff/admin accounts
   - Set role-based permissions
   - Configure department assignments

3. **Import Data:**
   - Add customers
   - Create product catalog
   - Setup suppliers

4. **Configure Automations:**
   - Setup low stock alerts
   - Configure email notifications
   - Schedule report generation

5. **Deploy to Production:**
   - Follow [DEPLOYMENT.md](DEPLOYMENT.md)
   - Set up SSL certificate
   - Configure backups

## Support & Help

- **Documentation:** See [README.md](README.md)
- **Deployment Help:** See [DEPLOYMENT.md](DEPLOYMENT.md)
- **API Docs:** See [API_REFERENCE.md](API_REFERENCE.md)
- **Issues:** Check GitHub Issues or contact support

## Key Contacts

- **Email:** support@billingerp.com
- **Documentation:** https://docs.billingerp.com
- **Status:** https://status.billingerp.com

---

**Ready to get started?** Launch your first invoice in less than 5 minutes!

For detailed information, see the full [README.md](README.md)
