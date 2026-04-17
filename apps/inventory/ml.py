"""
Machine Learning utilities for inventory management.

This module provides AI-powered predictions for stock management,
including demand forecasting and stock reorder recommendations.
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from django.db.models import Sum, Count
from apps.inventory.models import Product, StockMovement
from apps.billing.models import Invoice, InvoiceItem
from sklearn.linear_model import LinearRegression
import logging

logger = logging.getLogger(__name__)


class StockPredictor:
    """
    Machine learning model for predicting stock requirements.
    
    Uses historical sales data to predict future demand and recommend
    reorder quantities considering supplier lead times.
    """
    
    def __init__(self, product_id, look_back_days=90):
        """
        Initialize the predictor with a product.
        
        Args:
            product_id: ID of the product to predict for
            look_back_days: Number of days of historical data to use
        """
        self.product_id = product_id
        self.look_back_days = look_back_days
        self.product = Product.objects.get(id=product_id)
    
    def get_historical_sales(self):
        """
        Retrieve historical sales data for the product.
        
        Returns:
            DataFrame with dates and quantities sold
        """
        start_date = datetime.now() - timedelta(days=self.look_back_days)
        
        sales_data = InvoiceItem.objects.filter(
            product=self.product,
            invoice__invoice_date__gte=start_date
        ).values('invoice__invoice_date').annotate(
            quantity=Sum('quantity')
        ).order_by('invoice__invoice_date')
        
        if not sales_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(sales_data)
        df.columns = ['date', 'quantity']
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Fill missing dates with 0 sales
        date_range = pd.date_range(start=start_date, end=datetime.now(), freq='D')
        df = df.set_index('date').reindex(date_range.to_series().index, fill_value=0)
        df['date'] = df.index
        df = df.reset_index(drop=True)
        
        return df
    
    def predict_demand(self, days_ahead=30):
        """
        Predict future demand for the product.
        
        Args:
            days_ahead: Number of days into the future to predict
            
        Returns:
            Dictionary with predictions and metrics
        """
        try:
            hist_data = self.get_historical_sales()
            
            if hist_data.empty or len(hist_data) < 7:
                logger.warning(f"Insufficient data for product {self.product_id}")
                return {
                    'error': 'Insufficient historical data',
                    'predicted_daily_demand': self.product.reorder_quantity / 30,
                    'confidence': 0
                }
            
            # Prepare data for ML model
            X = np.arange(len(hist_data)).reshape(-1, 1)
            y = hist_data['quantity'].values
            
            # Train linear regression model
            model = LinearRegression()
            model.fit(X, y)
            
            # Make predictions
            future_X = np.arange(
                len(hist_data),
                len(hist_data) + days_ahead
            ).reshape(-1, 1)
            future_predictions = model.predict(future_X)
            
            # Ensure non-negative predictions
            future_predictions = np.maximum(future_predictions, 0)
            
            # Calculate metrics
            average_daily_demand = np.mean(y)
            total_predicted_demand = np.sum(future_predictions)
            std_dev = np.std(y)
            
            # Calculate confidence level (from 0 to 1)
            # Based on R-squared score
            from sklearn.metrics import r2_score
            r2 = r2_score(y, model.predict(X))
            confidence = max(0, min(1, r2))
            
            return {
                'predicted_daily_demand': average_daily_demand,
                'predicted_total_demand': total_predicted_demand,
                'standard_deviation': std_dev,
                'predictions': future_predictions.tolist(),
                'confidence': confidence,
                'error': None
            }
        except Exception as e:
            logger.error(f"Error predicting demand for product {self.product_id}: {str(e)}")
            return {
                'error': str(e),
                'predicted_daily_demand': self.product.reorder_quantity / 30,
                'confidence': 0
            }
    
    def recommend_reorder(self, supplier_lead_days=7, safety_stock_days=5):
        """
        Recommend reorder quantity based on predictions.
        
        Args:
            supplier_lead_days: Expected days for supplier to deliver
            safety_stock_days: Days of safety stock to maintain
            
        Returns:
            Dictionary with reorder recommendations
        """
        try:
            prediction = self.predict_demand(supplier_lead_days + safety_stock_days)
            
            if prediction.get('error'):
                return {
                    'recommended_quantity': self.product.reorder_quantity,
                    'reason': 'Using default reorder quantity due to insufficient data',
                    'confidence': 0
                }
            
            daily_demand = prediction['predicted_daily_demand']
            std_dev = prediction['standard_deviation']
            
            # Calculate safety stock using z-score (95% service level)
            z_score = 1.65  # 95% confidence interval
            safety_stock = z_score * std_dev * np.sqrt(supplier_lead_days)
            
            # Calculate reorder point
            lead_time_demand = daily_demand * supplier_lead_days
            reorder_point = lead_time_demand + safety_stock
            
            # Calculate recommended quantity
            # EOQ = sqrt(2DS/H) where D=demand, S=order cost, H=holding cost
            # Simplified: recommend 30 days of stock
            recommended_quantity = int(daily_demand * 30)
            
            return {
                'recommended_quantity': max(recommended_quantity, 1),
                'reorder_point': int(max(reorder_point, 0)),
                'daily_demand': daily_demand,
                'safety_stock': int(safety_stock),
                'confidence': prediction['confidence'],
                'reason': f'Based on {self.look_back_days} days of sales history'
            }
        except Exception as e:
            logger.error(f"Error recommending reorder for product {self.product_id}: {str(e)}")
            return {
                'recommended_quantity': self.product.reorder_quantity,
                'reorder_point': self.product.low_stock_threshold,
                'confidence': 0,
                'error': str(e)
            }
    
    @staticmethod
    def get_low_stock_alerts():
        """
        Get all products with low stock and their recommendations.
        
        Returns:
            List of products with reorder recommendations
        """
        low_stock_products = Product.objects.filter(
            quantity_in_stock__lte=models.F('low_stock_threshold'),
            is_active=True
        )
        
        alerts = []
        for product in low_stock_products:
            try:
                predictor = StockPredictor(product.id)
                recommendation = predictor.recommend_reorder()
                recommendation['product'] = product
                alerts.append(recommendation)
            except Exception as e:
                logger.error(f"Error generating alert for product {product.id}: {str(e)}")
        
        return alerts


# Import models for F() function
from django.db import models
