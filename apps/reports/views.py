"""
Django views for reports app.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.accounts.decorators import manager_required
from apps.reports.models import SalesReport, InventoryReport, ProfitAndLoss, ExpenseReport


@login_required(login_url='accounts:login')
@manager_required
def report_dashboard_view(request):
    """Display reports dashboard."""
    sales_reports = SalesReport.objects.all().order_by('-report_date')[:10]
    inventory_reports = InventoryReport.objects.all().order_by('-report_date')[:10]
    pl_reports = ProfitAndLoss.objects.all().order_by('-report_period')[:10]
    
    context = {
        'sales_reports': sales_reports,
        'inventory_reports': inventory_reports,
        'pl_reports': pl_reports,
        'title': 'Reports'
    }
    return render(request, 'reports/dashboard.html', context)
