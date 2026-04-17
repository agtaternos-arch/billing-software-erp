"""
Machine Learning analysis for inventory labels.
"""
from PIL import Image
import random
import time
import re

def analyze_label(photo):
    """
    Simulated AI analysis of a product label photo.
    
    In a real-world scenario, this would use pytesseract or an AI API.
    For this prototype, it extracts some metadata and simulates analysis.
    """
    # Open image with Pillow to at least verify it's a valid image
    try:
        img = Image.open(photo)
        # Simulate processing time
        time.sleep(1)
        
        # Simulated OCR results based on some 'common' things in images
        # Or just generate believable mock data
        filename = photo.name.split('.')[0].replace('_', ' ').title()
        
        # Heuristic: if filename contains a number, use it as price
        price_match = re.search(r'\d+', filename)
        price = float(price_match.group()) if price_match else random.randint(10, 500)
        
        # Simulated extraction results
        return {
            'name': filename or "Scanned Product",
            'price': price,
            'sku': f"SKU-{random.randint(1000, 9999)}",
            'confidence': random.uniform(0.85, 0.98),
            'detected_text': f"Product analysis complete for {filename}. Detected price: ${price}."
        }
    except Exception as e:
        return {
            'name': "Unknown product",
            'price': 0,
            'sku': "ERROR",
            'error': str(e)
        }
