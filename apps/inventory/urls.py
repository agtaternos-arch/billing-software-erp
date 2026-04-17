"""
URL patterns for inventory app.
"""
from django.urls import path
from apps.inventory import views

app_name = 'inventory'

urlpatterns = [
    # Product management
    path('products/', views.product_list, name='product_list'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/scan/', views.product_scan, name='product_scan'),
    path('products/discount/', views.update_discount, name='update_discount'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('products/<int:pk>/restock/', views.product_restock, name='product_restock'),
    
    # Supplier management
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/create/', views.supplier_create, name='supplier_create'),
    path('suppliers/<int:pk>/edit/', views.supplier_edit, name='supplier_edit'),
    
    # Category management
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
]
