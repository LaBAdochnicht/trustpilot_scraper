#!/usr/bin/env python3
"""
Example script for using the Trustpilot Scraper
Scrapes ALL reviews from ALL locations

Usage:
    python3 example_usage.py                    # All reviews
    python3 example_usage.py --filter-5-stars    # Only 5-star reviews
    python3 example_usage.py --no-filter          # All reviews (explicit)
    python3 example_usage.py --url example.com    # Different domain
"""

from scraper import scrape_trustpilot_reviews
import json
import pandas as pd
import argparse
from collections import Counter

# Parse command line arguments
parser = argparse.ArgumentParser(
    description='Trustpilot Review Scraper',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
  python3 example_usage.py --url example.com           # Scrape all reviews
  python3 example_usage.py --url example.com --filter-5-stars    # Only 5-star reviews
  python3 example_usage.py --url example.com --no-filter         # All reviews (explicit)
    """
)
parser.add_argument(
    '--filter-5-stars',
    action='store_true',
    help='Only scrape 5-star ratings (default: False)'
)
parser.add_argument(
    '--no-filter',
    action='store_true',
    help='Scrape all ratings (overrides --filter-5-stars)'
)
parser.add_argument(
    '--url',
    type=str,
    required=True,
    help='Domain for Trustpilot (e.g. example.com)'
)

args = parser.parse_args()

# Filter logic: --no-filter has priority
if args.no_filter:
    FILTER_5_STARS = False
else:
    FILTER_5_STARS = args.filter_5_stars

# Build Trustpilot URL
base_url = f'https://www.trustpilot.com/review/{args.url}'

print("=" * 60)
print("TRUSTPILOT REVIEW SCRAPER")
if FILTER_5_STARS:
    print("⚠️  MODE: Only 5-star ratings")
else:
    print("📊 MODE: All ratings")
print(f"🌐 URL: {base_url}")
print("=" * 60)
print()

# Scrape all reviews (with progress display)
result = scrape_trustpilot_reviews(base_url, verbose=True, filter_5_stars=FILTER_5_STARS)

reviews = result['reviews']
business_info = result['business_info']

if not reviews:
    print("No reviews found!")
    exit(1)

# Detailed statistics
print("\n" + "=" * 60)
print("DETAILED STATISTICS")
print("=" * 60)

# Display business information
if business_info:
    print(f"\n🏢 Business Information:")
    print(f"   Name: {business_info.get('displayName', 'N/A')}")
    print(f"   TrustScore: {business_info.get('trustScore', 'N/A')}/10")
    print(f"   Total Reviews: {business_info.get('numberOfReviews', 'N/A')}")
    print(f"   Average Stars: {business_info.get('stars', 'N/A')}/5")

df = pd.DataFrame(reviews)

# Overall statistics
print(f"\n📊 Overall Statistics (scraped reviews):")
print(f"   Number of Reviews: {len(reviews)}")
if len(reviews) > 0:
    print(f"   Average Rating: {df['Rating'].mean():.2f}/5")
    print(f"   Highest Rating: {df['Rating'].max()}/5")
    print(f"   Lowest Rating: {df['Rating'].min()}/5")
    
    if FILTER_5_STARS:
        total_reviews = business_info.get('numberOfReviews', 0)
        if total_reviews:
            percentage = (len(reviews) / total_reviews) * 100
            print(f"   5-Star Reviews Percentage: {percentage:.1f}% ({len(reviews)}/{total_reviews})")

# Statistics by location
print(f"\n🌍 Reviews by Location:")
locations = Counter(df['Location'])
for location, count in sorted(locations.items(), key=lambda x: x[1], reverse=True):
    location_reviews = df[df['Location'] == location]
    avg_rating = location_reviews['Rating'].mean()
    print(f"   {location}: {count:3d} reviews (Ø {avg_rating:.2f}/5)")

# Statistics by rating
print(f"\n⭐ Rating Distribution:")
ratings = Counter(df['Rating'])
for rating in sorted(ratings.keys(), reverse=True):
    count = ratings[rating]
    percentage = (count / len(reviews)) * 100
    print(f"   {rating} stars: {count:3d} reviews ({percentage:5.1f}%)")

# Date range
print(f"\n📅 Date Range:")
print(f"   Oldest Review: {df['Date'].min()}")
print(f"   Newest Review: {df['Date'].max()}")

# Example reviews
print(f"\n" + "=" * 60)
print("EXAMPLE REVIEWS (first 3)")
print("=" * 60)
for i, review in enumerate(reviews[:3], 1):
    print(f"\nReview {i}:")
    print(f"  📅 Date: {review['Date']}")
    print(f"  👤 Author: {review['Author']}")
    print(f"  🌍 Location: {review['Location']}")
    print(f"  ⭐ Rating: {review['Rating']}/5")
    print(f"  📝 Heading: {review['Heading']}")
    print(f"  🔗 URL: {review.get('URL', 'N/A')}")
    print(f"  💬 Text: {review['Body'][:150]}...")

# Save as JSON (including business info)
print(f"\n" + "=" * 60)
print("SAVING DATA")
print("=" * 60)

# Save reviews + business info together
output_data = {
    'business_info': business_info,
    'reviews': reviews,
    'statistics': {
        'total_reviews_scraped': len(reviews),
        'filter_5_stars_active': FILTER_5_STARS
    }
}

with open('reviews.json', 'w', encoding='utf-8') as f:
    json.dump(output_data, f, ensure_ascii=False, indent=2)
print("✅ Reviews saved to 'reviews.json' (including business info)!")

# Save as CSV
df.to_csv('reviews.csv', index=False, encoding='utf-8')
print("✅ Reviews saved to 'reviews.csv'!")

# Additionally: CSV grouped by location
df_sorted = df.sort_values(['Location', 'Date'], ascending=[True, False])
df_sorted.to_csv('reviews_by_location.csv', index=False, encoding='utf-8')
print("✅ Reviews saved to 'reviews_by_location.csv' (sorted by location)!")

print(f"\n🎉 Done! All {len(reviews)} reviews have been successfully scraped and saved.")

