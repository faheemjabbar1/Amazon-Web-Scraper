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
        # Try multiple selectors for regular price - ORDER MATTERS!
        # More specific selectors first, AVOID .a-text-price as it often matches unit prices
        selectors = [
            # Primary price display (most reliable)
            "span.a-price.reinventPricePriceToPayMargin span.a-offscreen",
            ".a-price.reinventPricePriceToPayMargin .a-offscreen",
            # Sized price elements (usually main prices, not unit prices)
            ".a-price[data-a-size='xl'] .a-offscreen",
            ".a-price[data-a-size='l'] .a-offscreen",
            ".a-price[data-a-size='medium'] .a-offscreen",
            ".a-price[data-a-size='large'] .a-offscreen",
            # Buy box and core price areas (avoid .a-text-price!)
            "#corePriceDisplay_desktop_feature_div .a-price .a-offscreen",
            "#corePrice_feature_div .a-price:not(.a-text-price) .a-offscreen",
            # Legacy selectors
            "#price_inside_buybox",
            "#priceblock_ourprice",
            "#priceblock_dealprice",
            # Last resort: a-text-price (often unit prices, so check carefully)
            "#corePrice_feature_div .a-price.a-text-price .a-offscreen",
            ".a-price.a-text-price .a-offscreen",
        ]

        for selector in selectors:
            try:
                element = await self.page.query_selector(selector)
                if element:
                    price = await element.inner_text()
                    price = format_price(price)

                    # Validate: must have £ and must NOT be a unit price
                    # Also check ancestor elements for unit price indicators
                    if price and "£" in price:
                        # Get the .a-price container and its parent
                        price_container = await element.evaluate_handle("el => el.closest('.a-price')")
                        if price_container:
                            parent_class = await price_container.evaluate("el => el.parentElement?.className || ''")

                            # Skip if parent or price text indicates this is a unit price
                            if not self._is_unit_price(price) and not self._is_unit_price_element(parent_class):
                                self.logger.success(f"Regular price extracted from {selector}: {price}")
                                return price
                            else:
                                self.logger.warning(f"Skipping unit price from {selector}: {price} (parent: {parent_class[:50]})")
            except Exception as e:
                self.logger.warning(f"Error with selector {selector}: {e}")
                continue

        # Try alternative approach - collect all prices and filter intelligently
        try:
            price_divs = await self.page.query_selector_all(".a-price")
            valid_prices = []

            for price_div in price_divs:
                try:
                    # Get the offscreen price (accessible version)
                    offscreen = await price_div.query_selector(".a-offscreen")
                    if offscreen:
                        price_text = await offscreen.inner_text()
                        price_text = format_price(price_text)

                        # Get parent class to check for unit price indicators
                        parent_class = await price_div.evaluate("el => el.parentElement?.className || ''")

                        # Filter out unit prices and invalid prices
                        if (price_text and "£" in price_text and
                            not self._is_unit_price(price_text) and
                            not self._is_unit_price_element(parent_class)):

                            # Extract numeric value for comparison
                            import re
                            match = re.search(r'£(\d+\.?\d*)', price_text)
                            if match:
                                numeric_value = float(match.group(1))
                                # Only consider prices > £1 (most products cost more than £1)
                                if numeric_value > 1.0:
                                    valid_prices.append((numeric_value, price_text))
                except Exception:
                    continue

            # If we found valid prices, return the highest one (main product price)
            # Main prices are usually higher than unit prices or promotional snippets
            if valid_prices:
                valid_prices.sort(reverse=True)  # Sort by numeric value, descending
                best_price = valid_prices[0][1]
                self.logger.success(f"Regular price extracted (best match): {best_price}")
                return best_price

        except Exception as e:
            self.logger.warning(f"Error in alternative price extraction: {e}")

        self.logger.warning("Could not extract regular price")
        return None

    def _is_unit_price_element(self, parent_class: str) -> bool:
        """
        Check if a parent element class indicates this is a unit price element.

        Args:
            parent_class: The parent element's className

        Returns:
            True if it's a unit price element, False otherwise
        """
        if not parent_class:
            return False

        # Class names that indicate unit prices
        unit_class_indicators = [
            'pricePerUnit',
            'price-per-unit',
            'apex-price-to-pay-ppu',  # PPU = Price Per Unit
            'unit-price',
            'unitPrice'
        ]

        parent_lower = parent_class.lower()
        return any(indicator.lower() in parent_lower for indicator in unit_class_indicators)

    def _is_unit_price(self, price_text: str) -> bool:
        """
        Check if a price string is a unit price (per 100g, per kg, etc.)

        Args:
            price_text: The price string to check

        Returns:
            True if it's a unit price, False otherwise
        """
        if not price_text:
            return False

        # Common unit price indicators
        unit_indicators = [
            '/100g', '/100 g', '/ 100g', '/ 100 g',
            '/kg', '/g', '/ kg', '/ g',
            '/l', '/ml', '/ l', '/ ml',
            'per 100g', 'per kg', 'per g',
            '/count', '/item', '/piece'
        ]

        price_lower = price_text.lower()
        return any(indicator in price_lower for indicator in unit_indicators)

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

        # Wait for any animations/price updates
        await self.page.wait_for_timeout(500)

        # Try multiple selectors for Subscribe & Save price
        # IMPORTANT: Order matters - more specific selectors first
        selectors = [
            # Hidden tiered price (needs to be made visible first)
            "#sns-tiered-price .a-price .a-offscreen",
            "#sns-tiered-price .a-offscreen",
            # Main S&S price display area
            "#rcxsubsync_dealPrice_feature_div .a-price .a-offscreen",
            "#snsAccordionRowMiddle .a-price .a-offscreen",
            "#snsAccordionRowMiddle span.a-offscreen",
            # Base price containers
            "#sns-base .a-price .a-offscreen",
            "#sns-base-price",
            # Accordion sections
            "#subscriptionAccordion .a-price .a-offscreen",
            "#rcxsubsToggle .a-price .a-offscreen",
            # General S&S containers
            "div[data-feature-name='subscribeAndSave'] .a-price .a-offscreen",
            "#sns_d_off_pct_label",
            ".sns-price .a-offscreen",
        ]

        for selector in selectors:
            try:
                element = await self.page.query_selector(selector)
                if element:
                    # Check if element is visible or has content
                    is_visible = await element.is_visible()
                    price = await element.inner_text()
                    price = format_price(price)

                    # Even if hidden, extract if it has a valid price
                    # BUT: Filter out unit prices!
                    if price and "£" in price and not self._is_unit_price(price):
                        self.logger.success(f"Subscribe & Save price extracted from {selector}: {price}")
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
                        # Filter out unit prices here too
                        if price and "£" in price and not self._is_unit_price(price):
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
        subscribe_save_price = await self.extract_subscribe_save_price()

        # If Subscribe & Save price not found, get one-time purchase price
        if not subscribe_save_price:
            self.logger.info("Subscribe & Save price not found, extracting one-time purchase price...")
            regular_price = await self.extract_regular_price()
            final_price = regular_price
            price_type = "One-Time Purchase"
        else:
            final_price = subscribe_save_price
            price_type = "Subscribe & Save"

        # Compile results
        data = {
            "url": url,
            "product_title": title,
            "price": final_price,
            "price_type": price_type,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "extraction_status": "success" if title else "partial"
        }

        self.logger.success(f"Product data extraction completed - Price Type: {price_type}")
        return data
