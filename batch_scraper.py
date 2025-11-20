"""
Batch Amazon UK Product Scraper
Processes multiple products from an Excel file.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd

from src.scraper import AmazonUKScraper
from src.utils import Logger, load_config, ensure_directories


class BatchScraper:
    """Handles batch scraping of multiple Amazon products."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = Logger()
        self.results = []
        self.output_file = None

    def load_urls_from_excel(self, excel_path: str) -> List[str]:
        """
        Load product URLs from Excel file.

        Args:
            excel_path: Path to the Excel file

        Returns:
            List of product URLs
        """
        try:
            self.logger.info(f"Loading URLs from: {excel_path}")

            # Read Excel file
            df = pd.read_excel(excel_path)

            # Look for URL column (flexible column name matching)
            url_column = None
            for col in df.columns:
                if 'url' in col.lower() or 'link' in col.lower() or 'asin' in col.lower():
                    url_column = col
                    break

            if url_column is None:
                # If no URL column found, assume first column contains URLs
                url_column = df.columns[0]
                self.logger.warning(f"No URL column found. Using first column: {url_column}")

            # Extract URLs and clean them
            urls = df[url_column].dropna().tolist()
            urls = [str(url).strip() for url in urls if str(url).strip()]

            # Ensure URLs are proper Amazon UK URLs
            cleaned_urls = []
            for url in urls:
                url = str(url).strip()
                # If it's just an ASIN, convert to full URL
                if not url.startswith('http'):
                    url = f"https://www.amazon.co.uk/dp/{url}"
                # Ensure it's amazon.co.uk
                elif 'amazon.com' in url and 'amazon.co.uk' not in url:
                    url = url.replace('amazon.com', 'amazon.co.uk')
                cleaned_urls.append(url)

            self.logger.success(f"Loaded {len(cleaned_urls)} URLs from Excel file")
            return cleaned_urls

        except Exception as e:
            self.logger.error(f"Failed to load Excel file: {e}")
            return []

    async def scrape_all_products(self, urls: List[str]) -> None:
        """
        Scrape all products from the URL list using a SINGLE browser instance.

        Args:
            urls: List of product URLs to scrape
        """
        total = len(urls)
        self.logger.info(f"Starting batch scrape of {total} products")

        # Create output file path with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_file = Path("data") / f"batch_results_{timestamp}.xlsx"
        self.logger.info(f"Results will be saved to: {self.output_file}")

        # Create ONE scraper instance for all products
        scraper = AmazonUKScraper(self.config)

        try:
            # Initialize browser ONCE
            self.logger.info("Initializing browser (will be reused for all products)...")
            await scraper.initialize_browser()
            self.logger.success("Browser initialized - ready to scrape!")

            for index, url in enumerate(urls, 1):
                print("\n" + "=" * 80)
                self.logger.info(f"Processing product {index}/{total}")
                self.logger.info(f"URL: {url}")
                print("=" * 80 + "\n")

                try:
                    # Use fast scraping method (no browser init/close)
                    product_data = await scraper.scrape_product_fast(url)

                    # Add index and success indicator
                    product_data['product_number'] = index
                    product_data['scrape_success'] = 'error' not in product_data

                    # Store result
                    self.results.append(product_data)

                    if product_data.get('scrape_success'):
                        self.logger.success(f"✅ Product {index}/{total} completed successfully")
                    else:
                        self.logger.error(f"❌ Product {index}/{total} failed: {product_data.get('error', 'Unknown error')}")

                    # Save progress after each product
                    self._save_progress()

                except Exception as e:
                    self.logger.error(f"❌ Unexpected error processing product {index}/{total}: {e}")
                    self.results.append({
                        'product_number': index,
                        'url': url,
                        'error': str(e),
                        'scrape_success': False,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })

                # No delay - move to next product immediately!

        finally:
            # Close browser at the end
            self.logger.info("Closing browser...")
            await scraper.close()

        self.logger.success(f"\n🎉 Batch scraping completed! Processed {total} products")
        self._print_summary()
        self.logger.success(f"\n📊 Final results saved to: {self.output_file}")

    def _save_progress(self) -> None:
        """Save current progress to the SAME Excel file (updates with each product)."""
        try:
            # Convert results to DataFrame
            df = pd.DataFrame(self.results)

            # Reorder columns for better readability
            column_order = ['product_number', 'url', 'product_title',
                          'price', 'price_type', 'scrape_success',
                          'timestamp', 'error', 'extraction_status']

            # Only include columns that exist
            column_order = [col for col in column_order if col in df.columns]
            other_columns = [col for col in df.columns if col not in column_order]
            df = df[column_order + other_columns]

            # Save to the SAME Excel file (overwrites with updated data)
            df.to_excel(self.output_file, index=False, engine='openpyxl')

            # Only log every 5 products to reduce console spam
            if len(self.results) % 5 == 0 or len(self.results) == 1:
                self.logger.info(f"Progress saved: {len(self.results)} products completed")

        except Exception as e:
            self.logger.error(f"Failed to save progress: {e}")

    def _print_summary(self) -> None:
        """Print summary of batch scraping results."""
        total = len(self.results)
        successful = sum(1 for r in self.results if r.get('scrape_success'))
        failed = total - successful

        print("\n" + "=" * 80)
        print("BATCH SCRAPING SUMMARY".center(80))
        print("=" * 80)
        print(f"\nTotal Products:     {total}")
        print(f"✅ Successful:       {successful}")
        print(f"❌ Failed:           {failed}")
        print(f"Success Rate:       {(successful/total*100):.1f}%")
        print("\n" + "=" * 80 + "\n")


async def main():
    """Main entry point for batch scraper."""
    print("\n" + "=" * 80)
    print("AMAZON UK BATCH PRODUCT SCRAPER".center(80))
    print("=" * 80 + "\n")

    # Ensure directories exist
    ensure_directories()

    # Load configuration
    config = load_config()
    if not config:
        print("❌ Failed to load configuration. Please check config/config.json")
        return

    # Find Excel file in data folder
    logger = Logger()
    data_folder = Path("data")
    excel_files = list(data_folder.glob("*.xlsx")) + list(data_folder.glob("*.xls"))

    if not excel_files:
        logger.error("No Excel files found in the 'data' folder!")
        logger.info("Please place your Excel file (containing product URLs) in the 'data' folder")
        return

    # If multiple Excel files, use the most recent one
    if len(excel_files) > 1:
        logger.warning(f"Found {len(excel_files)} Excel files. Using the most recent one.")
        excel_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    input_file = excel_files[0]
    logger.info(f"Using Excel file: {input_file.name}")

    # Create batch scraper
    batch_scraper = BatchScraper(config)

    # Load URLs from Excel
    urls = batch_scraper.load_urls_from_excel(str(input_file))

    if not urls:
        logger.error("No URLs found in Excel file!")
        return

    # Display configuration
    print("\n" + "-" * 80)
    logger.info(f"Products to scrape: {len(urls)}")
    logger.info(f"Headless mode: {config.get('headless', False)}")
    logger.info(f"Using cookies: {config.get('use_cookies', True)}")
    print("-" * 80 + "\n")

    # Start batch scraping
    await batch_scraper.scrape_all_products(urls)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n❌ Scraping interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        sys.exit(1)
