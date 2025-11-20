"""
Debug script to see ALL prices on the page.
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

async def debug_all_prices():
    """Debug: Show all prices found on the page."""

    test_url = "https://amazon.co.uk/dp/B004XAKAYE"

    print("\n" + "="*80)
    print("DEBUGGING ALL PRICES ON PAGE")
    print("="*80)
    print(f"URL: {test_url}\n")

    config = {"headless": False, "use_cookies": True, "save_cookies": True}
    scraper = AmazonUKScraper(config)

    try:
        await scraper.initialize_browser()
        await scraper.navigate_to_product(test_url)

        print("\n" + "="*80)
        print("FINDING ALL .a-price ELEMENTS")
        print("="*80 + "\n")

        # Get all price elements
        price_elements = await scraper.page.query_selector_all(".a-price")
        print(f"Found {len(price_elements)} price elements\n")

        for idx, price_elem in enumerate(price_elements, 1):
            try:
                # Get the whole price HTML for inspection
                html = await price_elem.inner_html()

                # Get offscreen text
                offscreen = await price_elem.query_selector(".a-offscreen")
                if offscreen:
                    offscreen_text = await offscreen.inner_text()
                else:
                    offscreen_text = "NO OFFSCREEN"

                # Get visible text
                visible_text = await price_elem.inner_text()

                # Get parent context
                parent = await price_elem.evaluate("el => el.parentElement?.className || 'no parent'")

                print(f"Price #{idx}:")
                print(f"  Offscreen: {offscreen_text}")
                print(f"  Visible: {visible_text[:100]}")
                print(f"  Parent class: {parent}")
                print(f"  HTML snippet: {html[:150]}...")
                print()

            except Exception as e:
                print(f"Price #{idx}: Error - {e}\n")

        # Also check for specific selectors
        print("\n" + "="*80)
        print("TESTING SPECIFIC SELECTORS")
        print("="*80 + "\n")

        test_selectors = [
            "#corePrice_feature_div .a-price.a-text-price .a-offscreen",
            "#corePrice_feature_div .a-price .a-offscreen",
            ".a-price.reinventPricePriceToPayMargin .a-offscreen",
            "span.a-price.reinventPricePriceToPayMargin span.a-offscreen",
        ]

        for selector in test_selectors:
            try:
                elem = await scraper.page.query_selector(selector)
                if elem:
                    text = await elem.inner_text()
                    print(f"✓ {selector}")
                    print(f"  Value: {text}\n")
                else:
                    print(f"✗ {selector} - NOT FOUND\n")
            except Exception as e:
                print(f"✗ {selector} - ERROR: {e}\n")

    finally:
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(debug_all_prices())
