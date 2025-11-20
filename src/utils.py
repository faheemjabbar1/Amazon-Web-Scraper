"""
Utility functions for Amazon UK scraper.
Provides helper functions for logging, file operations, and data formatting.
"""

import json
import random
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from tabulate import tabulate


class Logger:
    """Simple logger for tracking scraper progress."""

    @staticmethod
    def info(message: str) -> None:
        """
        Log an informational message.

        Args:
            message: The message to log
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] ℹ️  INFO: {message}")

    @staticmethod
    def success(message: str) -> None:
        """
        Log a success message.

        Args:
            message: The message to log
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] ✅ SUCCESS: {message}")

    @staticmethod
    def error(message: str) -> None:
        """
        Log an error message.

        Args:
            message: The message to log
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] ❌ ERROR: {message}")

    @staticmethod
    def warning(message: str) -> None:
        """
        Log a warning message.

        Args:
            message: The message to log
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] ⚠️  WARNING: {message}")


async def random_delay(min_seconds: float = 2.0, max_seconds: float = 4.0) -> None:
    """
    Add a random delay to simulate human behavior.

    Args:
        min_seconds: Minimum delay in seconds
        max_seconds: Maximum delay in seconds
    """
    delay = random.uniform(min_seconds, max_seconds)
    await asyncio.sleep(delay)


def save_to_json(data: Dict[str, Any], filename: Optional[str] = None) -> str:
    """
    Save data to a JSON file with timestamp.

    Args:
        data: Dictionary containing the data to save
        filename: Optional custom filename

    Returns:
        Path to the saved file
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"amazon_product_{timestamp}.json"

    # Ensure data directory exists
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    filepath = data_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return str(filepath)


def load_config(config_path: str = "config/config.json") -> Dict[str, Any]:
    """
    Load configuration from JSON file.

    Args:
        config_path: Path to the configuration file

    Returns:
        Dictionary containing configuration data
    """
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        Logger.error(f"Configuration file not found: {config_path}")
        return {}
    except json.JSONDecodeError as e:
        Logger.error(f"Invalid JSON in configuration file: {e}")
        return {}


def save_cookies(cookies: list, filepath: str = "config/cookies.json") -> None:
    """
    Save browser cookies to a file.

    Args:
        cookies: List of cookie dictionaries
        filepath: Path to save cookies
    """
    Path(filepath).parent.mkdir(exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(cookies, f, indent=2)
    Logger.info(f"Cookies saved to {filepath}")


def load_cookies(filepath: str = "config/cookies.json") -> Optional[list]:
    """
    Load browser cookies from a file.

    Args:
        filepath: Path to the cookies file

    Returns:
        List of cookie dictionaries or None if file doesn't exist
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            cookies = json.load(f)
        Logger.info(f"Cookies loaded from {filepath}")
        return cookies
    except FileNotFoundError:
        Logger.warning(f"Cookie file not found: {filepath}")
        return None
    except json.JSONDecodeError as e:
        Logger.error(f"Corrupted cookie file detected: {e}. Deleting and starting fresh.")
        # Delete the corrupted file
        try:
            Path(filepath).unlink()
            Logger.info(f"Deleted corrupted cookie file: {filepath}")
        except Exception:
            pass
        return None


def display_results_table(data: Dict[str, Any]) -> None:
    """
    Display scraped data in a formatted table.

    Args:
        data: Dictionary containing product data
    """
    print("\n" + "=" * 80)
    print("SCRAPING RESULTS".center(80))
    print("=" * 80 + "\n")

    table_data = []
    for key, value in data.items():
        if key != "timestamp" and key != "url":
            # Format the key for display
            display_key = key.replace("_", " ").title()
            table_data.append([display_key, value if value else "N/A"])

    print(tabulate(table_data, headers=["Field", "Value"], tablefmt="grid"))

    # Display additional info
    if "timestamp" in data:
        print(f"\nScraped at: {data['timestamp']}")
    if "url" in data:
        print(f"Product URL: {data['url']}")

    print("\n" + "=" * 80 + "\n")


def ensure_directories() -> None:
    """Create necessary directories if they don't exist."""
    directories = ["data", "screenshots", "config"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    Logger.info("Directory structure verified")


def format_price(price_text: Optional[str]) -> Optional[str]:
    """
    Format price text by removing extra whitespace and standardizing format.

    Args:
        price_text: Raw price text from webpage

    Returns:
        Formatted price string or None
    """
    if not price_text:
        return None

    # Remove extra whitespace and newlines
    price_text = " ".join(price_text.split())
    return price_text.strip()
