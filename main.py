#!/usr/bin/env python3
"""
Amazon UK Product Scraper - Main Entry Point
Scrapes product information from Amazon UK including prices and Subscribe & Save details.
"""

import asyncio
import argparse
import sys
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.scraper import AmazonUKScraper
from src.utils import (
    Logger,
    load_config,
    save_to_json,
    display_results_table,
    ensure_directories
)


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Amazon UK Product Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape a product with visible browser
  python main.py --url "https://www.amazon.co.uk/dp/B0EXAMPLE"

  # Scrape with custom postcode
  python main.py --url "https://www.amazon.co.uk/dp/B0EXAMPLE" --postcode "SW1A 1AA"

  # Run in headless mode
  python main.py --url "https://www.amazon.co.uk/dp/B0EXAMPLE" --headless

  # Disable cookies
  python main.py --url "https://www.amazon.co.uk/dp/B0EXAMPLE" --no-cookies

  # Custom output filename
  python main.py --url "https://www.amazon.co.uk/dp/B0EXAMPLE" --output my_product.json
        """
    )

    parser.add_argument(
        "--url",
        type=str,
        required=True,
        help="Amazon UK product URL to scrape"
    )

    parser.add_argument(
        "--postcode",
        type=str,
        default=None,
        help="UK postcode for delivery location (default: from config or SE1 1)"
    )

    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode (default: visible browser)"
    )

    parser.add_argument(
        "--no-cookies",
        action="store_true",
        help="Disable cookie loading/saving"
    )

    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Custom output filename for JSON results"
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config/config.json",
        help="Path to configuration file (default: config/config.json)"
    )

    return parser.parse_args()


def build_config(args: argparse.Namespace, file_config: dict) -> dict:
    """
    Build configuration by merging command line args with file config.
    Command line arguments take precedence.

    Args:
        args: Parsed command line arguments
        file_config: Configuration loaded from file

    Returns:
        Merged configuration dictionary
    """
    config = file_config.copy()

    # Override with command line arguments
    if args.headless:
        config["headless"] = True
    elif "headless" not in config:
        config["headless"] = False

    if args.postcode:
        config["postcode"] = args.postcode
    elif "postcode" not in config:
        config["postcode"] = "SE1 1"

    if args.no_cookies:
        config["use_cookies"] = False
        config["save_cookies"] = False
    else:
        if "use_cookies" not in config:
            config["use_cookies"] = True
        if "save_cookies" not in config:
            config["save_cookies"] = True

    return config


async def main():
    """Main execution function."""
    logger = Logger()

    # Print banner
    print("\n" + "=" * 80)
    print("AMAZON UK PRODUCT SCRAPER".center(80))
    print("=" * 80 + "\n")

    try:
        # Parse arguments
        args = parse_arguments()

        # Ensure directories exist
        ensure_directories()

        # Load configuration
        file_config = load_config(args.config)
        config = build_config(args, file_config)

        # Log configuration
        logger.info(f"Product URL: {args.url}")
        logger.info(f"Postcode: {config['postcode']}")
        logger.info(f"Headless mode: {config['headless']}")
        logger.info(f"Using cookies: {config.get('use_cookies', True)}")

        # Validate URL
        if "amazon.co.uk" not in args.url.lower():
            logger.warning("⚠️  URL does not appear to be an Amazon UK URL")
            response = input("Continue anyway? (y/n): ")
            if response.lower() != "y":
                logger.info("Scraping cancelled")
                return

        print("\n" + "-" * 80 + "\n")

        # Create scraper instance
        scraper = AmazonUKScraper(config)

        # Scrape the product
        logger.info("Starting scraping process...")
        product_data = await scraper.scrape_product(args.url)

        print("\n" + "-" * 80 + "\n")

        # Check for errors
        if "error" in product_data:
            logger.error(f"Scraping failed: {product_data.get('error')}")
            logger.info("Check screenshots folder for debugging information")
            sys.exit(1)

        # Display results
        display_results_table(product_data)

        # Save to JSON
        output_filename = args.output
        filepath = save_to_json(product_data, output_filename)
        logger.success(f"Results saved to: {filepath}")

        # Check for missing data
        if not product_data.get("subscribe_save_price"):
            logger.warning("⚠️  Subscribe & Save price was not found")
            logger.info("This could mean:")
            logger.info("  - The product doesn't have Subscribe & Save option")
            logger.info("  - The location was not set correctly")
            logger.info("  - The page structure has changed")

        logger.success("\n✅ Scraping completed successfully!\n")

    except KeyboardInterrupt:
        logger.warning("\n\nScraping interrupted by user")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
