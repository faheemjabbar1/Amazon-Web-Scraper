"""
Data extraction module for Amazon UK product pages.
Handles extracting product information from parsed HTML.
"""

from typing import Dict, Optional, Any
from playwright.async_api import Page
from src.utils import Logger, format_price


class ProductExtractor:
    """Extracts product information from Amazon UK product pages."""

    def __init__(self, page: Page):
        """
        Initialize the product extractor.

        Args:
            page: Playwright page object
        """
        self.page = page
        self.logger = Logger()

    async def extract_product_title(self) -> Optional[str]:
        """
        Extract the product title from the page.

        Returns:
            Product title string or None if not found
        """
        selectors = [
            "#productTitle",
            "h1#title",
            "h1.product-title",
            "span#productTitle"
        ]

        for selector in selectors:
            try:
                element = await self.page.query_selector(selector)
                if element:
                    title = await element.inner_text()
                    title = title.strip()
                    if title:
                        self.logger.success(f"Product title extracted: {title[:50]}...")
                        return title
            except Exception as e:
                self.logger.warning(f"Error extracting title with selector {selector}: {e}")
                continue

        self.logger.error("Could not extract product title")
        return None

    async def extract_regular_price(self) -> Optional[str]:
        """
        Extract the regular price from the page.

        Returns:
            Price string or None if not found
        """
        # Try multiple selectors for regular price
        selectors = [
            ".a-price.a-text-price .a-offscreen",
            "span.a-price.reinventPricePriceToPayMargin span.a-offscreen",
            ".a-price[data-a-size='xl'] .a-offscreen",
            ".a-price[data-a-size='l'] .a-offscreen",
            "span.a-price span.a-offscreen",
            "#corePrice_feature_div .a-price .a-offscreen",
            "#corePriceDisplay_desktop_feature_div .a-price .a-offscreen",
            "#price_inside_buybox",
            "#priceblock_ourprice",
            "#priceblock_dealprice"
        ]

        for selector in selectors:
            try:
                element = await self.page.query_selector(selector)
                if element:
                    price = await element.inner_text()
                    price = format_price(price)
                    if price and "£" in price:
                        self.logger.success(f"Regular price extracted: {price}")
                        return price
            except Exception as e:
                self.logger.warning(f"Error with selector {selector}: {e}")
                continue

        # Try alternative approach - look for price in the main price div
        try:
            price_divs = await self.page.query_selector_all(".a-price")
            for price_div in price_divs:
                price_text = await price_div.inner_text()
                if price_text and "£" in price_text:
                    price = format_price(price_text)
                    self.logger.success(f"Regular price extracted: {price}")
                    return price
        except Exception as e:
            self.logger.warning(f"Error in alternative price extraction: {e}")

        self.logger.warning("Could not extract regular price")
        return None

    async def extract_subscribe_save_price(self) -> Optional[str]:
        """
        Extract the Subscribe & Save price from the page.
        Attempts to expand accordion if necessary.

        Returns:
            Subscribe & Save price string or None if not found
        """
        self.logger.info("Attempting to extract Subscribe & Save price...")

        # First, try to click accordion/expandable sections
        await self._try_expand_subscribe_save_section()

        # Wait a bit for any animations
        await self.page.wait_for_timeout(1000)

        # Try multiple selectors for Subscribe & Save price
        selectors = [
            "#sns-base .a-price .a-offscreen",
            "#subscriptionAccordion .a-price .a-offscreen",
            "#rcxsubsToggle .a-price .a-offscreen",
            "div[data-feature-name='subscribeAndSave'] .a-price .a-offscreen",
            "#sns_d_off_pct_label",
            ".sns-price .a-offscreen",
            "#sns-base-price",
        ]

        for selector in selectors:
            try:
                element = await self.page.query_selector(selector)
                if element:
                    price = await element.inner_text()
                    price = format_price(price)
                    if price and "£" in price:
                        self.logger.success(f"Subscribe & Save price extracted: {price}")
                        return price
            except Exception as e:
                self.logger.warning(f"Error with selector {selector}: {e}")
                continue

        # Try to find Subscribe & Save text and nearby price
        try:
            # Look for "Subscribe & Save" text
            sns_elements = await self.page.query_selector_all("text=Subscribe & Save")
            for element in sns_elements:
                # Try to find price near this element
                parent = await element.evaluate_handle("el => el.closest('.a-section, .a-box, div')")
                if parent:
                    price_element = await parent.query_selector(".a-price .a-offscreen")
                    if price_element:
                        price = await price_element.inner_text()
                        price = format_price(price)
                        if price and "£" in price:
                            self.logger.success(f"Subscribe & Save price extracted: {price}")
                            return price
        except Exception as e:
            self.logger.warning(f"Error in Subscribe & Save text search: {e}")

        self.logger.warning("Subscribe & Save price not found (may not be available for this product)")
        return None

    async def _try_expand_subscribe_save_section(self) -> None:
        """
        Try to expand Subscribe & Save accordion sections if they exist.
        """
        # Possible accordion selectors
        accordion_selectors = [
            "a[href='#subscriptionAccordion']",
            "#rcxsubsToggle",
            "a.a-link-expander",
            "button[aria-controls='subscriptionAccordion']"
        ]

        for selector in accordion_selectors:
            try:
                element = await self.page.query_selector(selector)
                if element:
                    # Check if it's related to Subscribe & Save
                    text = await element.inner_text()
                    if "subscribe" in text.lower() or "save" in text.lower():
                        self.logger.info(f"Clicking accordion: {selector}")
                        await element.click()
                        await self.page.wait_for_timeout(500)
                        return
            except Exception as e:
                self.logger.warning(f"Could not click accordion {selector}: {e}")
                continue

    async def extract_all_product_data(self, url: str) -> Dict[str, Any]:
        """
        Extract all product data from the current page.

        Args:
            url: The product URL being scraped

        Returns:
            Dictionary containing all extracted product data
        """
        from datetime import datetime

        self.logger.info("Starting product data extraction...")

        # Extract all data
        title = await self.extract_product_title()
        regular_price = await self.extract_regular_price()
        subscribe_save_price = await self.extract_subscribe_save_price()

        # Compile results
        data = {
            "url": url,
            "product_title": title,
            "regular_price": regular_price,
            "subscribe_save_price": subscribe_save_price,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "extraction_status": "success" if title else "partial"
        }

        self.logger.success("Product data extraction completed")
        return data
