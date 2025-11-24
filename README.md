# Trustpilot Scraper

A Python library for scraping Trustpilot reviews. This enhanced version includes features like 5-star filtering, business information extraction, and review URL collection.

## Installation

### Option 1: Install from local repository

Clone or download this repository, then install the dependencies:

```bash
# Clone the repository
git clone <your-repo-url>
cd trustpilot_scraper

# Install dependencies
pip install -r requirements.txt
```

### Option 2: Install as a package

```bash
# From the repository directory
pip install -e .
```

### Option 3: Use directly without installation

You can also use the scraper directly without installation:

```bash
# Just install dependencies
pip install requests beautifulsoup4 pandas
```

## Usage

### Basic Usage (Python)

```python
from scraper import scrape_trustpilot_reviews

base_url = 'https://www.trustpilot.com/review/example.com'

result = scrape_trustpilot_reviews(base_url)
reviews = result['reviews']
business_info = result['business_info']

for review in reviews:
    print(review)
```

**Note:** If installed as a package, use:
```python
from trustpilot_scraper.scraper import scrape_trustpilot_reviews
```

### Filter 5-Star Reviews Only

```python
result = scrape_trustpilot_reviews(base_url, filter_5_stars=True)
reviews = result['reviews']
```

### Command Line Usage

```bash
# Scrape all reviews
python3 example_usage.py --url example.com

# Scrape only 5-star reviews
python3 example_usage.py --url example.com --filter-5-stars

# Scrape all reviews (explicit)
python3 example_usage.py --url example.com --no-filter
```
## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the example script:**
   ```bash
   python3 example_usage.py --url example.com
   ```

3. **Check the output files:**
   - `reviews.json` - All reviews with business info
   - `reviews.csv` - Reviews in CSV format
   - `reviews_by_location.csv` - Reviews sorted by location

## Output Example

```python
{
    'Date': '2022-07-07',
    'Author': 'Marlie Anderson',
    'Body': 'Fast response times and excellent client service...',
    'Heading': 'Fast response times and excellent…',
    'Rating': 5,
    'Location': 'US',
    'URL': 'https://www.trustpilot.com/reviews/62c702ea0c20b4453c32d733'
}
```

The scraper returns a dictionary with:
- `reviews`: List of review dictionaries
- `business_info`: Dictionary containing TrustScore, total reviews, average rating, etc.

## Features

- ✅ Scrapes Trustpilot reviews from the provided base URL
- ✅ Retrieves review data including date, author, body, heading, rating, location, and **URL**
- ✅ Handles pagination automatically to scrape all available reviews
- ✅ Supports filtering for 5-star ratings only
- ✅ Extracts business information (TrustScore, total reviews, average rating)
- ✅ Scrapes reviews from all languages and locations
- ✅ Removes duplicate reviews automatically
- ✅ Exports data to JSON and CSV formats

## Dependencies

Install the required dependencies:

```bash
pip install requests beautifulsoup4 pandas
```

Or use the requirements file:

```bash
pip install -r requirements.txt
```

## Review Data Structure

Each review contains the following fields:

- `Date`: Publication date (YYYY-MM-DD format)
- `Author`: Reviewer's display name
- `Body`: Full review text
- `Heading`: Review title/heading
- `Rating`: Star rating (1-5)
- `Location`: Reviewer's country code
- `URL`: Direct link to the review on Trustpilot
