"""
API URL configuration for REST endpoints.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.api import views

router = DefaultRouter()
router.register(r'users', views.UserProfileViewSet, basename='user')
router.register(r'customers', views.CustomerViewSet, basename='customer')
router.register(r'contacts', views.ContactPersonViewSet, basename='contact')
router.register(r'suppliers', views.SupplierViewSet, basename='supplier')
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'stock-movements', views.StockMovementViewSet, basename='stock-movement')
router.register(r'invoices', views.InvoiceViewSet, basename='invoice')
router.register(r'payments', views.PaymentViewSet, basename='payment')
router.register(r'expenses', views.ExpenseViewSet, basename='expense')
router.register(r'sales-reports', views.SalesReportViewSet, basename='sales-report')
router.register(r'inventory-reports', views.InventoryReportViewSet, basename='inventory-report')
router.register(r'p-and-l', views.ProfitAndLossViewSet, basename='p-and-l')

app_name = 'api'

urlpatterns = [
    path('pos/ai_process/', views.pos_ai_process, name='pos-ai-process'),
    path('', include(router.urls)),
]
