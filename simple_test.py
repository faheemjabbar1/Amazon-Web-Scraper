"""
Simple test script without emoji logging issues.
Tests the problematic product URL.
"""

import asyncio
import sys

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

async def test_product():
    """Test the specific product that had wrong price."""

    # Test Ferrero Rocher - was showing £3.24 (unit price) instead of £17.00
    test_url = "https://amazon.co.uk/dp/B004XAKAYE"

    print("\n" + "="*80)
    print("TESTING SINGLE PRODUCT - FERRERO ROCHER")
    print("="*80)
    print(f"URL: {test_url}")
    print("Expected: ~£17.00 (NOT £3.24 unit price!)")
    print("="*80 + "\n")

    config = {
        "headless": False,  # Set to False so you can see what's happening
        "use_cookies": True,
        "save_cookies": True
    }

    scraper = AmazonUKScraper(config)

    try:
        # Initialize browser
        print("[INFO] Initializing browser...")
        await scraper.initialize_browser()

        # Navigate to product
        print("[INFO] Navigating to product...")
        success = await scraper.navigate_to_product(test_url)

        if not success:
            print("[ERROR] Failed to navigate to product")
            return

        # Take screenshot
        await scraper.take_screenshot("test_product_before_extraction")

        # Extract data
        from src.extractor import ProductExtractor
        extractor = ProductExtractor(scraper.page)

        print("\n[INFO] Extracting product data...")
        product_data = await extractor.extract_all_product_data(test_url)

        # Take final screenshot
        await scraper.take_screenshot("test_product_after_extraction")

        # Display results
        print("\n" + "="*80)
        print("EXTRACTED DATA")
        print("="*80)
        for key, value in product_data.items():
            print(f"{key}: {value}")
        print("="*80)

        # Check if price is correct
        extracted_price = product_data.get('price', '')
        if '£3.24' in str(extracted_price) or '3.24' in str(extracted_price):
            print("\n[ERROR] Still getting unit price (£3.24)! Should be £17.00!")
        elif '£17' in str(extracted_price) or '17.' in str(extracted_price):
            print("\n[SUCCESS] Price looks correct! Got £17.00")
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
        asyncio.run(test_product())
    except KeyboardInterrupt:
        print("\n\n[INFO] Test interrupted by user")
        sys.exit(0)
