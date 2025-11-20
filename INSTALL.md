# Amazon UK Product Scraper - Quick Start Guide

## Installation Steps

Follow these steps in order:

### Step 1: Install Python Dependencies

Open a terminal/command prompt in the project directory and run:

```bash
pip install -r requirements.txt
```

Or if you're using Python 3 specifically:

```bash
pip3 install -r requirements.txt
```

### Step 2: Install Playwright Browsers

After installing the Python packages, install the Playwright browser:

```bash
playwright install chromium
```

Or with Python 3:

```bash
python -m playwright install chromium
```

### Step 3: Verify Installation

Check if Playwright is installed correctly:

```bash
python -c "import playwright; print('Playwright installed successfully!')"
```

### Step 4: Run the Scraper

Now you can run the scraper:

```bash
python main.py --url "https://www.amazon.co.uk/dp/YOUR_PRODUCT_ID"
```

Replace `YOUR_PRODUCT_ID` with an actual Amazon UK product ID.

## Common Issues

### Issue: "pip is not recognized"
**Solution**: Install pip or use `python -m pip` instead:
```bash
python -m pip install -r requirements.txt
```

### Issue: "Permission denied" on Linux/Mac
**Solution**: Use sudo or install in user space:
```bash
pip install --user -r requirements.txt
```

### Issue: Multiple Python versions
**Solution**: Use the specific Python version:
```bash
python3 -m pip install -r requirements.txt
python3 main.py --url "URL"
```

## Quick Test

After installation, test with a real product:

```bash
python main.py --url "https://www.amazon.co.uk/dp/B0CX23V923"
```

This will:
- Open a visible browser window
- Change location to UK (SE1 1)
- Scrape the product
- Save results to data/ folder
- Save screenshots to screenshots/ folder

## Need Help?

Check the full README.md for complete documentation.
