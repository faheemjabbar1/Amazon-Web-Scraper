"""
Test both problematic products to ensure fixes work.
"""

import asyncio
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

utils.Logger = SimpleLogger

from src.scraper import AmazonUKScraper

async def test_both_products():
    """Test both problematic products."""

    test_products = [
        {
            "name": "Jelly Bean Factory",
            "url": "https://amazon.co.uk/dp/B0CVXSY9YS",
            "expected": "~£8.50",
            "wrong": "£1.61"
        },
        {
            "name": "Ferrero Rocher",
            "url": "https://amazon.co.uk/dp/B004XAKAYE",
            "expected": "~£17.00",
            "wrong": "£3.24"
        }
    ]

    print("\n" + "="*80)
    print("TESTING BOTH PROBLEMATIC PRODUCTS")
    print("="*80 + "\n")

    config = {"headless": False, "use_cookies": True, "save_cookies": True}
    scraper = AmazonUKScraper(config)

    results = []

    try:
        await scraper.initialize_browser()

        for idx, product in enumerate(test_products, 1):
            print(f"\n{'='*80}")
            print(f"TEST {idx}/2: {product['name']}")
            print("="*80)
            print(f"URL: {product['url']}")
            print(f"Expected: {product['expected']}, Should NOT be: {product['wrong']}")
            print("="*80 + "\n")

            # Scrape the product
            product_data = await scraper.scrape_product_fast(product['url'])

            # Check result
            extracted_price = product_data.get('price', '')
            print(f"\nExtracted: {extracted_price}")

            if product['wrong'] in str(extracted_price):
                print(f"[ERROR] Got wrong price {product['wrong']}!")
                results.append(("FAIL", product['name'], extracted_price))
            elif any(exp_part in str(extracted_price) for exp_part in ["8.5", "8.07", "17", "17."]):
                print(f"[SUCCESS] Price looks correct!")
                results.append(("PASS", product['name'], extracted_price))
            else:
                print(f"[WARNING] Unexpected price: {extracted_price}")
                results.append(("WARN", product['name'], extracted_price))

    finally:
        await scraper.close()

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    for status, name, price in results:
        status_emoji = {"PASS": "[SUCCESS]", "FAIL": "[ERROR]", "WARN": "[WARNING]"}[status]
        print(f"{status_emoji} {name}: {price}")
    print("="*80 + "\n")

    pass_count = sum(1 for r in results if r[0] == "PASS")
    print(f"\nPassed: {pass_count}/{len(results)}")

if __name__ == "__main__":
    asyncio.run(test_both_products())
