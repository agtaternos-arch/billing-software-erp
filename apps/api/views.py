"""
REST API viewsets for all models.
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import datetime, timedelta

from apps.accounts.models import UserProfile
from apps.customers.models import Customer, ContactPerson
from apps.inventory.models import Product, Supplier, Category, StockMovement, PurchaseOrder
from apps.billing.models import Invoice, Payment, Expense
from apps.reports.models import SalesReport, InventoryReport, ProfitAndLoss
from apps.api.serializers import (
    UserProfileSerializer, CustomerSerializer, ContactPersonSerializer,
    SupplierSerializer, CategorySerializer, ProductSerializer, StockMovementSerializer,
    InvoiceSerializer, PaymentSerializer, ExpenseSerializer, SalesReportSerializer,
    InventoryReportSerializer, ProfitAndLossSerializer
)


class UserProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for UserProfile model."""
    queryset = UserProfile.objects.select_related('user').all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['role', 'is_active']
    search_fields = ['user__username', 'user__email', 'user__first_name']


class CustomerViewSet(viewsets.ModelViewSet):
    """ViewSet for Customer model."""
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'email', 'phone', 'company_name']
    ordering_fields = ['name', 'created_at']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['get'])
    def invoices(self, request, pk=None):
        """Get all invoices for a customer."""
        customer = self.get_object()
        invoices = customer.invoices.all()
        serializer = InvoiceSerializer(invoices, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get only active customers."""
        active_customers = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(active_customers, many=True)
        return Response(serializer.data)


class ContactPersonViewSet(viewsets.ModelViewSet):
    """ViewSet for ContactPerson model."""
    queryset = ContactPerson.objects.select_related('customer').all()
    serializer_class = ContactPersonSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['customer', 'is_primary']
    search_fields = ['name', 'email', 'phone']


class SupplierViewSet(viewsets.ModelViewSet):
    """ViewSet for Supplier model."""
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'email', 'phone']


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for Category model."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'code']


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet for Product model."""
    queryset = Product.objects.select_related('category', 'supplier').all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'supplier', 'is_active']
    search_fields = ['name', 'sku', 'description']
    ordering_fields = ['name', 'unit_price', 'quantity_in_stock']
    ordering = ['name']
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get all products with low stock."""
        low_stock_products = self.get_queryset().filter(
            quantity_in_stock__lte=models.F('low_stock_threshold')
        )
        serializer = self.get_serializer(low_stock_products, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def adjust_stock(self, request, pk=None):
        """Adjust stock for a product."""
        product = self.get_object()
        quantity = request.data.get('quantity', 0)
        reason = request.data.get('reason', 'adjustment')
        
        old_quantity = product.quantity_in_stock
        product.quantity_in_stock += quantity
        product.save()
        
        # Record stock movement
        StockMovement.objects.create(
            product=product,
            movement_type='adjustment',
            quantity=quantity,
            notes=reason,
            created_by=request.user
        )
        
        return Response({
            'status': 'success',
            'old_quantity': old_quantity,
            'new_quantity': product.quantity_in_stock,
            'change': quantity
        })


class StockMovementViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for StockMovement model (read-only)."""
    queryset = StockMovement.objects.select_related('product', 'created_by').all()
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['product', 'movement_type']
    ordering_fields = ['created_at']
    ordering = ['-created_at']


class InvoiceViewSet(viewsets.ModelViewSet):
    """ViewSet for Invoice model."""
    queryset = Invoice.objects.select_related('customer', 'created_by').all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['customer', 'status']
    search_fields = ['invoice_number', 'customer__name']
    ordering_fields = ['invoice_date', 'due_date', 'total_amount']
    ordering = ['-invoice_date']
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get all overdue invoices."""
        today = timezone.now().date()
        overdue_invoices = self.get_queryset().filter(
            due_date__lt=today,
            status__in=['sent', 'partial']
        )
        serializer = self.get_serializer(overdue_invoices, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        """Mark invoice as paid."""
        invoice = self.get_object()
        invoice.status = 'paid'
        invoice.paid_amount = invoice.total_amount
        invoice.save()
        serializer = self.get_serializer(invoice)
        return Response(serializer.data)


class PaymentViewSet(viewsets.ModelViewSet):
    """ViewSet for Payment model."""
    queryset = Payment.objects.select_related('invoice', 'created_by').all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['invoice', 'payment_method']
    ordering_fields = ['payment_date']
    ordering = ['-payment_date']


class ExpenseViewSet(viewsets.ModelViewSet):
    """ViewSet for Expense model."""
    queryset = Expense.objects.select_related('created_by').all()
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category']
    search_fields = ['title', 'description']
    ordering_fields = ['date', 'amount']
    ordering = ['-date']


class SalesReportViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for SalesReport model (read-only)."""
    queryset = SalesReport.objects.all()
    serializer_class = SalesReportSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['report_date']
    ordering = ['-report_date']


class InventoryReportViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for InventoryReport model (read-only)."""
    queryset = InventoryReport.objects.all()
    serializer_class = InventoryReportSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['report_date']
    ordering = ['-report_date']


class ProfitAndLossViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for ProfitAndLoss model (read-only)."""
    queryset = ProfitAndLoss.objects.all()
    serializer_class = ProfitAndLossSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['period_type']
    ordering_fields = ['report_period']
    ordering = ['-report_period']



from django.db import models  # Import for F() function in Product viewset

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import re

@csrf_exempt
@require_POST
def pos_ai_process(request):
    """
    Intelligent NLP processor for the Torvix AI Node.
    Handles product additions, restocking, and terminology simplifying.
    """
    try:
        data = json.loads(request.body)
        query = data.get('query', '').lower().strip()
        
        from apps.inventory.models import Product, StockMovement
        
        all_products = Product.objects.filter(is_active=True)
        found_products = []
        action_performed = None
        
        # 1. Check for "RESTOCK" intent
        is_restock = any(word in query for word in ['restock', 'add stock', 'refill', 'receive'])
        
        # 2. Check for "CHECKOUT" intent
        is_checkout = any(word in query for word in ['checkout', 'bill now', 'finish', 'complete', 'payment'])

        # 3. Fuzzy match products (Simple but smarter)
        for p in all_products:
            name = p.name.lower()
            code = p.sku.lower() if p.sku else ""
            
            # Match by name or code
            if name in query or (code and code in query):
                qty = 1
                # Regex to find quantity (e.g. "5 soaps", "add 10 biscuits")
                # Look for numbers before or after the name
                qty_match = re.search(r'(\d+)\s+' + re.escape(name), query)
                if not qty_match:
                    qty_match = re.search(re.escape(name) + r'\s+(\d+)', query)
                if qty_match:
                    qty = int(qty_match.group(1))

                if is_restock:
                    # Perform Restock Action
                    StockMovement.objects.create(
                        product=p,
                        movement_type='in',
                        quantity=qty,
                        notes=f'AI Voice/Chat Restock: {query}',
                        created_by=request.user if request.user.is_authenticated else None
                    )
                    found_products.append({'name': p.name, 'qty': qty, 'type': 'restock'})
                else:
                    # Add to Cart Action
                    found_products.append({
                        'id': p.id,
                        'name': p.name,
                        'price': float(p.unit_price),
                        'tax': float(p.tax_rate),
                        'stock': p.quantity_in_stock,
                        'qty': qty,
                        'type': 'cart'
                    })

        # 4. Generate Human-Friendly Response
        if is_restock and found_products:
            items = ", ".join([f"{i['qty']}x {i['name']}" for i in found_products])
            response_msg = f"✅ Stock updated! I've added {items} to the inventory database."
            action_performed = 'restock_complete'
        elif found_products:
            items = ", ".join([f"{i['qty']}x {i['name']}" for i in found_products])
            response_msg = f"🛒 Added {items} to your current billing cart."
            if is_checkout:
                response_msg += " Proceeding to checkout as requested..."
                action_performed = 'checkout'
        elif is_checkout:
            response_msg = "Proceeding to checkout with current cart items."
            action_performed = 'checkout'
        else:
            response_msg = "I didn't quite catch that. Try commands like 'Add 5 soaps', 'Restock 10 bread', or 'Checkout'."

        return JsonResponse({
            'status': 'success',
            'response': response_msg,
            'cart_updates': [p for p in found_products if p.get('type') == 'cart'],
            'action': action_performed
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'response': 'AI System Error: ' + str(e)}, status=400)
