"""
URL Configuration for billing_erp project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

from apps.billing import views as billing_views
from apps.accounts.urls import admin_urlpatterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('apps.api.urls')),
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('admin-panel/', include((admin_urlpatterns, 'adminpanel'), namespace='adminpanel')),
    path('billing/', include('apps.billing.urls', namespace='billing')),
    path('inventory/', include('apps.inventory.urls', namespace='inventory')),
    path('customers/', include('apps.customers.urls', namespace='customers')),
    path('reports/', include('apps.reports.urls', namespace='reports')),
    path('', billing_views.dashboard_view, name='dashboard'),
]

# Serve static/media files anyway if whitenoise isn't handling it or if in development
try:
    import whitenoise
    serve_manually = settings.DEBUG
except ImportError:
    serve_manually = True

if serve_manually:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
