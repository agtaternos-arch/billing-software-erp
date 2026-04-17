"""
URL patterns for reports app.
"""
from django.urls import path
from apps.reports import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_dashboard_view, name='dashboard'),
]
