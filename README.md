# Amazon UK Product Scraper

A robust, production-ready web scraper for extracting product information from Amazon UK, including regular prices and Subscribe & Save prices. Built with Playwright for reliable automation and anti-detection measures.

## Features

- **Automatic Location Change**: Reliably sets delivery location to UK postcode before scraping
- **Comprehensive Data Extraction**: Extracts product title, regular price, and Subscribe & Save price
- **Anti-Detection**: Implements multiple strategies to avoid bot detection
- **Visual Browser Mode**: Runs with visible browser by default for easy debugging
- **Screenshot Capture**: Saves screenshots at each critical step for troubleshooting
- **Cookie Management**: Saves and loads cookies for faster subsequent runs
- **Error Handling**: Robust error handling with detailed logging
- **Configurable**: Flexible configuration via command line or config file
- **Production Ready**: Well-documented, typed, and follows Python best practices

## Project Structure

```
amazon-uk-scraper/
├── src/
│   ├── __init__.py          # Package initialization
│   ├── scraper.py           # Main scraping logic
│   ├── extractor.py         # Data extraction module
│   └── utils.py             # Utility functions
├── config/
│   └── config.json          # Configuration file
├── screenshots/             # Screenshots saved here
├── data/                    # Scraped data saved here
├── main.py                  # Entry point
├── requirements.txt         # Python dependencies
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Step 1: Clone or Download

```bash
git clone <repository-url>
cd amazon-uk-scraper
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Install Playwright Browsers

```bash
playwright install chromium
```

That's it! You're ready to start scraping.

## Usage

### Single Product Scraping

#### Basic Usage

```bash
python main.py --url "https://www.amazon.co.uk/dp/B0EXAMPLE"
```

#### Advanced Usage

##### Custom Postcode

```bash
python main.py --url "https://www.amazon.co.uk/dp/B0EXAMPLE" --postcode "SW1A 1AA"
```

##### Headless Mode (No visible browser)

```bash
python main.py --url "https://www.amazon.co.uk/dp/B0EXAMPLE" --headless
```

##### Disable Cookie Management

```bash
python main.py --url "https://www.amazon.co.uk/dp/B0EXAMPLE" --no-cookies
```

##### Custom Output Filename

```bash
python main.py --url "https://www.amazon.co.uk/dp/B0EXAMPLE" --output my_product.json
```

##### Custom Config File

```bash
python main.py --url "https://www.amazon.co.uk/dp/B0EXAMPLE" --config my_config.json
```

### Batch Product Scraping (Multiple Products)

For scraping multiple products from an Excel file:

#### Step 1: Prepare Your Excel File

Create an Excel file (`.xlsx` or `.xls`) with product URLs in one of these formats:

**Option 1: URLs in a column**
```
| URL                                        |
|--------------------------------------------|
| https://www.amazon.co.uk/dp/B088W5HWVX    |
| https://www.amazon.co.uk/dp/B07XYZ1234    |
| https://www.amazon.co.uk/dp/B08ABC5678    |
```

**Option 2: ASINs only**
```
| ASIN         |
|--------------|
| B088W5HWVX   |
| B07XYZ1234   |
| B08ABC5678   |
```

The column name can be "URL", "Link", "ASIN", or any variation. The scraper will automatically detect it.

#### Step 2: Place Excel File

Place your Excel file in the `data/` folder.

#### Step 3: Run Batch Scraper

```bash
python batch_scraper.py
```

That's it! The scraper will:
- Automatically find your Excel file in the `data/` folder
- Extract all URLs from the file
- Scrape each product one by one
- Save progress after each product
- Generate a consolidated Excel report with all results

#### Batch Scraping Features

- **Automatic Progress Saving**: Results are saved after each product, so if interrupted, you don't lose progress
- **Detailed Logging**: See real-time progress for each product
- **Error Handling**: If one product fails, the scraper continues with the next
- **Summary Report**: Get a complete summary at the end showing success/failure rates
- **Excel Output**: Results saved to `data/batch_results_YYYYMMDD_HHMMSS.xlsx`

#### Output Format

The batch scraper generates an Excel file with these columns:
- `product_number`: Sequential number (1, 2, 3...)
- `url`: Product URL
- `product_title`: Extracted product title
- `subscribe_save_price`: Subscribe & Save price
- `scrape_success`: TRUE/FALSE indicator
- `timestamp`: When the product was scraped
- `error`: Error message if scraping failed

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--url` | Amazon UK product URL (required) | - |
| `--postcode` | UK postcode for delivery location | SE1 1 |
| `--headless` | Run browser in headless mode | False (visible) |
| `--no-cookies` | Disable cookie loading/saving | False (enabled) |
| `--output` | Custom output filename | Auto-generated |
| `--config` | Path to config file | config/config.json |

## Configuration

Edit `config/config.json` to customize default behavior:

```json
{
  "postcode": "SE1 1",
  "headless": false,
  "use_cookies": true,
  "save_cookies": true,
  "timeout": 60000,
  "random_delay_min": 2.0,
  "random_delay_max": 4.0
}
```

### Configuration Options

- **postcode**: UK postcode for delivery location
- **headless**: Run browser without visible window
- **use_cookies**: Load saved cookies to speed up runs
- **save_cookies**: Save cookies after successful scraping
- **timeout**: Page load timeout in milliseconds
- **random_delay_min/max**: Random delay range (seconds) between actions

## Output

### JSON Output

Results are saved to `data/amazon_product_YYYYMMDD_HHMMSS.json`:

```json
{
  "url": "https://www.amazon.co.uk/dp/B0EXAMPLE",
  "product_title": "Example Product Name",
  "regular_price": "£29.99",
  "subscribe_save_price": "£26.99",
  "timestamp": "2024-01-15 14:30:00",
  "extraction_status": "success"
}
```

### Console Output

Results are displayed in a formatted table:

```
================================================================================
                           SCRAPING RESULTS
================================================================================

┌─────────────────────────┬────────────────────────────────────┐
│ Field                   │ Value                              │
├─────────────────────────┼────────────────────────────────────┤
│ Product Title           │ Example Product Name               │
│ Regular Price           │ £29.99                            │
│ Subscribe Save Price    │ £26.99                            │
│ Extraction Status       │ success                            │
└─────────────────────────┴────────────────────────────────────┘

Scraped at: 2024-01-15 14:30:00
Product URL: https://www.amazon.co.uk/dp/B0EXAMPLE
```

### Screenshots

Screenshots are automatically saved to the `screenshots/` folder:

- `01_before_location_change.png` - Amazon homepage before location change
- `02_popup_appeared.png` - Location popup
- `03_postcode_entered.png` - After entering postcode
- `04_after_apply.png` - After clicking Apply
- `05_location_verified.png` - Location change verified
- `06_product_page.png` - Product page loaded
- `error_*.png` - Screenshots on errors

## How It Works

### 1. Location Change (Critical Step)

The scraper performs these steps to set UK location:

1. Navigate to Amazon.co.uk homepage
2. Click "Deliver to" button
3. Wait for location popup
4. Enter UK postcode (default: SE1 1)
5. Click Apply button
6. Click Continue/Done if prompted
7. Verify location change success

This is THE MOST CRITICAL PART as Subscribe & Save prices only appear for UK locations.

### 2. Product Navigation

Navigate to the provided product URL and wait for page load.

### 3. Data Extraction

Extract data using multiple selector strategies:

- **Product Title**: Multiple fallback selectors
- **Regular Price**: Checks various price containers
- **Subscribe & Save**: Attempts to expand accordion, tries multiple containers

### 4. Results & Cleanup

Save results to JSON, display in console, save cookies, and close browser.

## Troubleshooting

### Issue: Location change fails

**Symptoms**: Subscribe & Save price not found, wrong delivery location

**Solutions**:
1. Check screenshots in `screenshots/` folder to see where it failed
2. Run with visible browser (without `--headless`) to watch the process
3. Try a different postcode
4. Check your internet connection
5. Amazon may have changed their page structure - check selectors in `src/scraper.py`

### Issue: Product title not found

**Symptoms**: Error "Could not extract product title"

**Solutions**:
1. Verify the URL is a valid Amazon UK product page
2. Check if the product page loaded correctly in screenshots
3. The page structure may have changed - update selectors in `src/extractor.py`

### Issue: Subscribe & Save not found

**Symptoms**: `subscribe_save_price` is null in results

**Possible causes**:
1. Product doesn't have Subscribe & Save option (this is normal)
2. Location wasn't set correctly (check screenshot `05_location_verified.png`)
3. Need to expand accordion section (scraper tries this automatically)

**Solutions**:
1. Verify location change succeeded in logs
2. Check if product actually has Subscribe & Save on Amazon.co.uk manually
3. Run with visible browser to see if Subscribe & Save appears

### Issue: Browser doesn't open

**Symptoms**: Error about Playwright browsers not installed

**Solution**:
```bash
playwright install chromium
```

### Issue: Import errors

**Symptoms**: ModuleNotFoundError

**Solution**:
```bash
pip install -r requirements.txt
```

### Issue: Permission errors on Linux

**Symptoms**: Permission denied errors

**Solution**:
```bash
chmod +x main.py
```

## Debug Mode

For maximum debugging visibility:

```bash
python main.py --url "https://www.amazon.co.uk/dp/B0EXAMPLE" --postcode "SE1 1"
```

This will:
- Show browser window (not headless)
- Print detailed step-by-step logs
- Save screenshots at each step
- Show all errors with context

Check the screenshots folder to see exactly what happened at each step.

## Anti-Detection Features

The scraper implements several anti-detection measures:

1. **Disabled WebDriver Flag**: Removes navigator.webdriver property
2. **Realistic User Agent**: Uses current Chrome user agent
3. **Random Delays**: 2-4 second delays between actions
4. **UK Locale & Timezone**: Sets locale to en-GB and timezone to Europe/London
5. **Natural Viewport**: 1920x1080 resolution
6. **Cookie Persistence**: Maintains session cookies

## Best Practices

1. **Don't Abuse**: Add delays between requests, respect robots.txt
2. **Check Screenshots**: Always check screenshots when debugging
3. **Use Cookies**: Enable cookie saving for faster subsequent runs
4. **Verify Location**: Always check that location change succeeded
5. **Handle Errors**: The scraper continues even if Subscribe & Save isn't found
6. **Rate Limiting**: Don't scrape too frequently from the same IP

## Legal & Ethical Considerations

- Review Amazon's Terms of Service before scraping
- Use responsibly and respect rate limits
- This tool is for educational and personal use
- Don't use for commercial purposes without permission
- Respect website resources and don't overload servers

## Dependencies

- **playwright**: Browser automation framework
- **python-dateutil**: Date utilities
- **tabulate**: Table formatting for console output
- **mypy** (optional): Type checking for development

## Development

### Running Type Checks

```bash
mypy src/
```

### Code Style

The project follows PEP 8 style guidelines. All functions include:
- Type hints
- Docstrings
- Error handling

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is provided as-is for educational purposes.

## Support

If you encounter issues:

1. Check the Troubleshooting section
2. Review screenshots in the `screenshots/` folder
3. Run with visible browser to debug
4. Check logs for error messages

## Changelog

### Version 1.0.0
- Initial release
- Location change functionality
- Product data extraction
- Subscribe & Save support
- Screenshot capture
- Cookie management
- Comprehensive error handling

---

**Made with ❤️ for Amazon UK product scraping**
