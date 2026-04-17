from django.urls import path
from apps.billing import views

app_name = 'billing'

urlpatterns = [
    # Invoice management
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/create/', views.invoice_create, name='invoice_create'),
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<int:pk>/edit/', views.invoice_edit, name='invoice_edit'),
    path('invoices/<int:pk>/pdf/', views.invoice_pdf, name='invoice_pdf'),
    path('invoices/<int:pk>/thermal/', views.invoice_thermal_preview, name='invoice_thermal'),
    path('invoices/<int:pk>/delete/', views.invoice_delete, name='invoice_delete'),
    
    # POS Terminal
    path('pos/', views.pos_terminal_view, name='pos_terminal'),
    
    # Payment management
    path('invoices/<int:invoice_id>/payment/', views.payment_create, name='payment_create'),
    
    # Expenses
    path('expenses/', views.expense_list_view, name='expense_list'),
    path('expenses/create/', views.expense_create, name='expense_create'),
    path('expenses/export/pdf/', views.expense_export_pdf_view, name='expense_export_pdf'),
    
    # Reports
    path('reports/gst/', views.report_gst_view, name='report_gst'),
    path('reports/profit-loss/', views.report_profit_loss_view, name='report_profit_loss'),
    
    # API endpoints
    path('api/product/<int:product_id>/price/', views.get_product_price, name='get_product_price'),
    path('api/customer/<int:customer_id>/detail/', views.get_customer_detail, name='get_customer_detail'),
    path('api/v1/pos/ai_process/', views.ai_process_view, name='ai_process'),
]
