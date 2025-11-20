"""
Test batch scraping with a single product to verify the price fix.
"""

import asyncio
import sys
import pandas as pd
from pathlib import Path

# Monkey patch the logger to avoid emoji issues
from src import utils

class SimpleLogger:
    @staticmethod
    def info(msg):
        print(f"[INFO] {msg}")

    @staticmethod
    def success(msg):
        print(f"[SUCCESS] {msg}")

    @staticmethod
    def error(msg):
        print(f"[ERROR] {msg}")

    @staticmethod
    def warning(msg):
        print(f"[WARNING] {msg}")

# Replace the emoji logger
utils.Logger = SimpleLogger

from src.scraper import AmazonUKScraper

async def test_batch():
    """Test batch scraping with the problematic product."""

    test_url = "https://amazon.co.uk/dp/B0CVXSY9YS"

    print("\n" + "="*80)
    print("TESTING BATCH SCRAPING WITH SINGLE PRODUCT")
    print("="*80)
    print(f"URL: {test_url}")
    print("="*80 + "\n")

    config = {
        "headless": False,
        "use_cookies": True,
        "save_cookies": True
    }

    scraper = AmazonUKScraper(config)

    try:
        # Initialize browser once
        print("[INFO] Initializing browser...")
        await scraper.initialize_browser()

        # Scrape the product using fast method (like batch scraper does)
        print("\n[INFO] Scraping product using fast method...")
        product_data = await scraper.scrape_product_fast(test_url)

        # Display results
        print("\n" + "="*80)
        print("EXTRACTED DATA (BATCH MODE)")
        print("="*80)
        for key, value in product_data.items():
            print(f"{key}: {value}")
        print("="*80)

        # Check if price is correct
        extracted_price = product_data.get('price', '')
        if '£1.61' in str(extracted_price) or '1.61' in str(extracted_price):
            print("\n[ERROR] Still getting wrong price (£1.61)!")
            print("[ERROR] The fix didn't work in batch mode!")
        elif '£8' in str(extracted_price) or '8.5' in str(extracted_price) or '8.07' in str(extracted_price):
            print("\n[SUCCESS] Price looks correct in batch mode!")
            print(f"[SUCCESS] Extracted price: {extracted_price}")
        else:
            print(f"\n[WARNING] Unexpected price: {extracted_price}")

    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("\n[INFO] Closing browser...")
        await scraper.close()
        print("[INFO] Test complete!")

if __name__ == "__main__":
    try:
        asyncio.run(test_batch())
    except KeyboardInterrupt:
        print("\n\n[INFO] Test interrupted by user")
        sys.exit(0)
