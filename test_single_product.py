"""
Test script to debug price extraction for a single product.
This will help us identify exactly what prices are being found.
"""

import asyncio
from src.scraper import AmazonUKScraper
from src.utils import Logger, load_config, ensure_directories

async def debug_single_product():
    """Test scraping a single product with detailed debugging."""

    # The problematic product URL
    test_url = "https://amazon.co.uk/dp/B08Q9TR12P"

    logger = Logger()
    print("\n" + "=" * 80)
    print("SINGLE PRODUCT DEBUG TEST".center(80))
    print("=" * 80 + "\n")

    logger.info(f"Testing URL: {test_url}")

    # Ensure directories exist
    ensure_directories()

    # Load configuration
    config = load_config()
    if not config:
        logger.error("Failed to load configuration")
        return

    # Create scraper
    scraper = AmazonUKScraper(config)

    try:
        # Initialize browser
        await scraper.initialize_browser()

        # Navigate to product
        logger.info("Navigating to product page...")
        await scraper.navigate_to_product(test_url)

        # Take screenshot before extraction
        await scraper.take_screenshot("debug_01_page_loaded")

        # Now let's debug the price extraction step by step
        from src.extractor import ProductExtractor
        extractor = ProductExtractor(scraper.page)

        # Get title
        logger.info("\n--- EXTRACTING TITLE ---")
        title = await extractor.extract_product_title()
        logger.info(f"Title: {title}")

        # Try to extract Subscribe & Save price
        logger.info("\n--- EXTRACTING SUBSCRIBE & SAVE PRICE ---")
        sns_price = await extractor.extract_subscribe_save_price()
        logger.info(f"Subscribe & Save Price: {sns_price}")

        # Take screenshot after S&S attempt
        await scraper.take_screenshot("debug_02_after_sns_extraction")

        # Extract regular price
        logger.info("\n--- EXTRACTING REGULAR PRICE ---")
        regular_price = await extractor.extract_regular_price()
        logger.info(f"Regular Price: {regular_price}")

        # Now let's manually check ALL price elements on the page
        logger.info("\n--- FINDING ALL PRICE ELEMENTS ON PAGE ---")

        # Get all elements with class 'a-price'
        all_prices = await scraper.page.query_selector_all(".a-price")
        logger.info(f"Found {len(all_prices)} price elements with class 'a-price'")

        for idx, price_elem in enumerate(all_prices, 1):
            try:
                # Get the offscreen price (accessible text)
                offscreen = await price_elem.query_selector(".a-offscreen")
                if offscreen:
                    price_text = await offscreen.inner_text()
                    logger.info(f"  Price #{idx} (offscreen): {price_text}")
                else:
                    # Get visible price
                    visible_text = await price_elem.inner_text()
                    logger.info(f"  Price #{idx} (visible): {visible_text[:50]}")
            except Exception as e:
                logger.warning(f"  Price #{idx}: Error - {e}")

        # Check specific Subscribe & Save selectors
        logger.info("\n--- CHECKING SPECIFIC S&S SELECTORS ---")

        sns_selectors = [
            "#sns-tiered-price",
            "#sns-tiered-price .a-price .a-offscreen",
            "#sns-base-price",
            "#snsAccordionRowMiddle .a-price .a-offscreen",
            "#rcxsubsync_dealPrice_feature_div",
        ]

        for selector in sns_selectors:
            try:
                element = await scraper.page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    logger.success(f"  ✅ Found {selector}: {text[:100]}")
                else:
                    logger.warning(f"  ❌ Not found: {selector}")
            except Exception as e:
                logger.error(f"  ❌ Error with {selector}: {e}")

        # Take final screenshot
        await scraper.take_screenshot("debug_03_final")

        logger.info("\n--- FINAL EXTRACTION ---")
        product_data = await extractor.extract_all_product_data(test_url)

        print("\n" + "=" * 80)
        print("FINAL EXTRACTED DATA".center(80))
        print("=" * 80)
        for key, value in product_data.items():
            print(f"{key}: {value}")
        print("=" * 80 + "\n")

    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Close browser
        await scraper.close()
        logger.info("Test completed!")

if __name__ == "__main__":
    asyncio.run(debug_single_product())
