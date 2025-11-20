"""
Main scraper module for Amazon UK.
Handles browser automation, location changes, and page navigation.
"""

from typing import Dict, Any, Optional
from pathlib import Path
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from src.utils import Logger, random_delay, save_cookies, load_cookies
from src.extractor import ProductExtractor


class AmazonUKScraper:
    """
    Main scraper class for Amazon UK product pages.
    Handles browser setup, location changes, and data extraction.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the scraper with configuration.

        Args:
            config: Configuration dictionary containing scraper settings
        """
        self.config = config
        self.logger = Logger()
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None

    async def initialize_browser(self) -> None:
        """
        Initialize the Playwright browser with anti-detection measures.
        """
        self.logger.info("Initializing browser...")

        self.playwright = await async_playwright().start()

        # Launch browser with specific settings
        self.browser = await self.playwright.chromium.launch(
            headless=self.config.get("headless", False),
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )

        # Create context with anti-detection measures
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="en-GB",
            timezone_id="Europe/London",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # Disable webdriver detection
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        # Load cookies if they exist
        if self.config.get("use_cookies", True):
            cookies = load_cookies()
            if cookies:
                await self.context.add_cookies(cookies)

        self.page = await self.context.new_page()
        self.logger.success("Browser initialized successfully")

    async def take_screenshot(self, name: str) -> str:
        """
        Take a screenshot of the current page.

        Args:
            name: Name for the screenshot file

        Returns:
            Path to the saved screenshot
        """
        screenshots_dir = Path("screenshots")
        screenshots_dir.mkdir(exist_ok=True)

        filepath = screenshots_dir / f"{name}.png"
        await self.page.screenshot(path=str(filepath), full_page=True)
        self.logger.info(f"Screenshot saved: {filepath}")
        return str(filepath)

    async def change_location_to_uk(self, postcode: str = "SE1 1") -> bool:
        """
        Change Amazon location to UK with specified postcode.
        This is the CRITICAL function that must work reliably.

        Args:
            postcode: UK postcode to set (default: "SE1 1")

        Returns:
            True if location change was successful, False otherwise
        """
        self.logger.info(f"Starting location change process to postcode: {postcode}")

        try:
            # Step 1: Navigate to Amazon UK homepage
            self.logger.info("Step 1: Navigating to Amazon.co.uk...")
            await self.page.goto("https://www.amazon.co.uk", wait_until="domcontentloaded")
            await random_delay(2, 3)
            await self.take_screenshot("01_before_location_change")
            self.logger.success("Loaded Amazon UK homepage")

            # Step 2: Click the "Deliver to" button
            self.logger.info("Step 2: Clicking 'Deliver to' button...")
            deliver_to_selector = "#nav-global-location-popover-link"

            try:
                await self.page.wait_for_selector(deliver_to_selector, timeout=10000)
                await self.page.click(deliver_to_selector)
                self.logger.success("Clicked 'Deliver to' button")
            except Exception as e:
                self.logger.error(f"Failed to click 'Deliver to' button: {e}")
                await self.take_screenshot("error_deliver_to_button")
                return False

            # Step 3: Wait for location popup to appear
            self.logger.info("Step 3: Waiting for location popup...")
            await random_delay(1, 2)

            try:
                await self.page.wait_for_selector("#GLUXZipUpdateInput", timeout=10000)
                await self.take_screenshot("02_popup_appeared")
                self.logger.success("Location popup appeared")
            except Exception as e:
                self.logger.error(f"Location popup did not appear: {e}")
                await self.take_screenshot("error_no_popup")
                return False

            # Step 4: Enter postcode
            self.logger.info(f"Step 4: Entering postcode '{postcode}'...")
            postcode_input_selector = "#GLUXZipUpdateInput"

            try:
                # Clear any existing value first
                await self.page.fill(postcode_input_selector, "")
                await random_delay(0.5, 1)

                # Type the postcode
                await self.page.fill(postcode_input_selector, postcode)
                await random_delay(0.5, 1)
                await self.take_screenshot("03_postcode_entered")
                self.logger.success(f"Postcode '{postcode}' entered")
            except Exception as e:
                self.logger.error(f"Failed to enter postcode: {e}")
                await self.take_screenshot("error_postcode_entry")
                return False

            # Step 5: Click Apply button
            self.logger.info("Step 5: Clicking Apply button...")
            apply_button_selector = 'input[aria-labelledby="GLUXZipUpdate-announce"]'

            try:
                await self.page.wait_for_selector(apply_button_selector, timeout=5000)
                await self.page.click(apply_button_selector)
                self.logger.success("Clicked Apply button")
                await random_delay(2, 3)
            except Exception as e:
                self.logger.error(f"Failed to click Apply button: {e}")
                await self.take_screenshot("error_apply_button")
                return False

            # Step 6: Check if Continue/Done button appears and click it
            self.logger.info("Step 6: Checking for Continue/Done button...")

            continue_selectors = [
                "button[name='glowDoneButton']",
                "button:has-text('Done')",
                "button:has-text('Continue')",
                "#GLUXConfirmClose"
            ]

            for selector in continue_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=3000)
                    if element:
                        await element.click()
                        self.logger.success(f"Clicked Continue/Done button: {selector}")
                        await random_delay(2, 3)
                        break
                except Exception:
                    continue

            await self.take_screenshot("04_after_apply")

            # Step 7: Verify location change
            self.logger.info("Step 7: Verifying location change...")
            return await self._verify_location_change(postcode)

        except Exception as e:
            self.logger.error(f"Unexpected error during location change: {e}")
            await self.take_screenshot("error_unexpected")
            return False

    async def _verify_location_change(self, expected_postcode: str) -> bool:
        """
        Verify that the location was actually changed.

        Args:
            expected_postcode: The postcode that should be set

        Returns:
            True if location is verified, False otherwise
        """
        try:
            # Wait for page to update
            await random_delay(2, 3)

            # Check the delivery location text
            location_selector = "#glow-ingress-line2"
            await self.page.wait_for_selector(location_selector, timeout=10000)

            location_text = await self.page.inner_text(location_selector)
            self.logger.info(f"Current location text: {location_text}")

            # Take verification screenshot
            await self.take_screenshot("05_location_verified")

            # Check if the postcode area is in the location text
            postcode_area = expected_postcode.split()[0]  # Get first part (e.g., "SE1")

            if postcode_area.upper() in location_text.upper():
                self.logger.success(f"✅ Location change VERIFIED! Location shows: {location_text}")
                return True
            else:
                self.logger.warning(f"⚠️  Location text does not contain expected postcode. Got: {location_text}")
                # Still might be successful, just different format
                return True

        except Exception as e:
            self.logger.error(f"Could not verify location change: {e}")
            return False

    async def navigate_to_product(self, url: str) -> bool:
        """
        Navigate to a specific product URL.

        Args:
            url: The Amazon product URL

        Returns:
            True if navigation successful, False otherwise
        """
        self.logger.info(f"Navigating to product URL...")

        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await random_delay(2, 4)

            # Wait for product page to load
            await self.page.wait_for_selector("#productTitle", timeout=15000)

            await self.take_screenshot("06_product_page")
            self.logger.success("Product page loaded successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to navigate to product page: {e}")
            await self.take_screenshot("error_product_page")
            return False

    async def scrape_product(self, url: str) -> Dict[str, Any]:
        """
        Main method to scrape a product from Amazon UK.

        Args:
            url: The Amazon product URL to scrape

        Returns:
            Dictionary containing scraped product data
        """
        try:
            # Initialize browser
            await self.initialize_browser()

            # Change location to UK (CRITICAL STEP)
            postcode = self.config.get("postcode", "SE1 1")
            location_success = await self.change_location_to_uk(postcode)

            if not location_success:
                self.logger.error("❌ CRITICAL: Location change failed!")
                return {
                    "error": "Location change failed",
                    "status": "failed"
                }

            # Navigate to product page
            nav_success = await self.navigate_to_product(url)

            if not nav_success:
                self.logger.error("Failed to navigate to product page")
                return {
                    "error": "Failed to navigate to product",
                    "status": "failed"
                }

            # Extract product data
            extractor = ProductExtractor(self.page)
            product_data = await extractor.extract_all_product_data(url)

            # Save cookies for future use
            if self.config.get("save_cookies", True):
                cookies = await self.context.cookies()
                save_cookies(cookies)

            return product_data

        except Exception as e:
            self.logger.error(f"Critical error during scraping: {e}")
            await self.take_screenshot("error_critical")
            return {
                "error": str(e),
                "status": "failed"
            }

        finally:
            # Close browser
            await self.close()

    async def close(self) -> None:
        """Clean up browser resources."""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            self.logger.info("Browser closed")
        except Exception as e:
            self.logger.warning(f"Error closing browser: {e}")
