# trustpilot_scraper/scraper.py

import requests
from bs4 import BeautifulSoup
import json
import time
import pandas as pd
from collections import Counter

def get_reviews_from_page(url, verbose=False):
    try:
        req = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        req.raise_for_status()  # Raise an error for bad status codes
        time.sleep(2)  # Add a delay to avoid overwhelming the server
        soup = BeautifulSoup(req.text, 'html.parser')
        script_tag = soup.find("script", id="__NEXT_DATA__")
        
        if not script_tag:
            if verbose:
                print(f"Warning: __NEXT_DATA__ script tag not found on {url}")
            return None, None, None
        
        reviews_raw = json.loads(script_tag.string)
        
        # Try different paths for reviews
        page_props = reviews_raw.get("props", {}).get("pageProps", {})
        
        # Standard path
        reviews = page_props.get("reviews")
        
        # Try alternative paths
        if not reviews:
            reviews = page_props.get("businessUnit", {}).get("reviews", {}).get("reviews")
        
        # Extract pagination information
        pagination = None
        if "businessUnit" in page_props:
            business_unit = page_props["businessUnit"]
            if "reviews" in business_unit and isinstance(business_unit["reviews"], dict):
                pagination = business_unit["reviews"].get("pagination")
        
        # Extract business unit information (only on first page)
        business_unit_info = None
        if "businessUnit" in page_props:
            business_unit = page_props["businessUnit"]
            business_unit_info = {
                "trustScore": business_unit.get("trustScore"),
                "numberOfReviews": business_unit.get("numberOfReviews"),
                "displayName": business_unit.get("displayName"),
                "stars": business_unit.get("stars")
            }
        
        return reviews, pagination, business_unit_info
        
    except requests.RequestException as e:
        # 404 means the page doesn't exist (end of pagination)
        if hasattr(e, 'response') and e.response is not None:
            if e.response.status_code == 404:
                if verbose:
                    print(f"404 - Page not found (end reached)")
                return [], None, None  # Empty list, not None
        if verbose:
            print(f"Request error: {e}")
        return None, None, None
    except json.JSONDecodeError as e:
        if verbose:
            print(f"JSON decode error: {e}")
        return None, None, None
    except AttributeError as e:
        if verbose:
            print(f"Attribute error: {e}")
        return None, None, None
    except Exception as e:
        if verbose:
            print(f"Unexpected error: {e}")
        return None, None, None

def scrape_trustpilot_reviews(base_url: str, verbose: bool = True, filter_5_stars: bool = False):
    """
    Scrapes all Trustpilot reviews from all pages and locations.
    
    Args:
        base_url: The Trustpilot URL (e.g. 'https://www.trustpilot.com/review/example.com')
        verbose: If True, progress will be displayed
        filter_5_stars: If True, only 5-star ratings will be scraped
    
    Returns:
        Dictionary with:
        - 'reviews': List of dictionaries with review data
        - 'business_info': Dictionary with TrustScore, numberOfReviews, etc.
    """
    reviews_data = []
    page_number = 1
    total_reviews_scraped = 0
    business_info = None

    if verbose:
        print(f"Starting scraping from: {base_url}")
        if filter_5_stars:
            print("⚠️  Filter active: Only 5-star ratings will be scraped")
        print("-" * 60)

    max_pages = None
    consecutive_empty_pages = 0
    
    # Use languages=all to get all reviews (not just English)
    # For page 1: use languages=all without page parameter
    # For further pages: use languages=all&page=N
    while True:
        if page_number == 1:
            url = f"{base_url}?languages=all"
        else:
            url = f"{base_url}?languages=all&page={page_number}"
        
        if verbose:
            print(f"Scraping page {page_number}...", end=" ", flush=True)
        
        reviews, pagination, business_unit_info = get_reviews_from_page(url, verbose=verbose)
        
        # Save business info on first page
        if page_number == 1 and business_unit_info:
            business_info = business_unit_info

        # If reviews is None (error loading), skip
        if reviews is None:
            consecutive_empty_pages += 1
            if verbose:
                print(f"Error loading (empty page {consecutive_empty_pages})")
            
            # Stop after 2 consecutive errors
            if consecutive_empty_pages >= 2:
                if verbose:
                    print("Two consecutive errors - scraping stopped.")
                break
            page_number += 1
            continue

        # If empty list (e.g. 404), means end
        if reviews == []:
            if verbose:
                print("End of pagination reached.")
            break

        # If no reviews found (but no errors)
        if not reviews:
            consecutive_empty_pages += 1
            if verbose:
                print(f"No reviews found (empty page {consecutive_empty_pages})")
            
            # Stop after 2 consecutive empty pages
            if consecutive_empty_pages >= 2:
                if verbose:
                    print("Two consecutive empty pages - scraping stopped.")
                break
        else:
            consecutive_empty_pages = 0
            
            # Check pagination information if available
            if pagination:
                total_pages = pagination.get("totalPages")
                current_page = pagination.get("currentPage")
                if total_pages and verbose:
                    print(f"[Page {current_page}/{total_pages}]", end=" ")
                if total_pages and page_number > total_pages:
                    if verbose:
                        print("Maximum page number reached.")
                    break


        page_review_count = 0
        filtered_count = 0
        for review in reviews:
            try:
                rating = review["rating"]
                
                # Filter: Only 5-star ratings if enabled
                if filter_5_stars and rating != 5:
                    filtered_count += 1
                    continue
                
                # Check if review already exists (based on unique fields)
                review_id = review.get("id") or review.get("reviewId")
                
                # Construct review URL
                # Trustpilot review URLs follow the pattern: https://www.trustpilot.com/reviews/{review_id}
                review_url = None
                if review_id:
                    review_url = f"https://www.trustpilot.com/reviews/{review_id}"
                elif review.get("url"):
                    # If URL is already in the data, use it
                    review_url = review.get("url")
                
                data = {
                    'Date': pd.to_datetime(review["dates"]["publishedDate"]).strftime("%Y-%m-%d"),
                    'Author': review["consumer"]["displayName"],
                    'Body': review["text"],
                    'Heading': review["title"],
                    'Rating': rating,
                    'Location': review["consumer"]["countryCode"],
                    'URL': review_url or 'N/A'
                }
                reviews_data.append(data)
                page_review_count += 1
            except (KeyError, TypeError) as e:
                # Skip reviews with missing data
                if verbose:
                    print(f"\n  Warning: Review skipped (missing data: {e})")
                continue
        
        total_reviews_scraped += page_review_count
        
        if verbose:
            if filter_5_stars and filtered_count > 0:
                print(f"{page_review_count} reviews found ({filtered_count} filtered, Total: {total_reviews_scraped})")
            else:
                print(f"{page_review_count} reviews found (Total: {total_reviews_scraped})")
        
        # If no reviews found on this page and we already have reviews
        if page_review_count == 0 and total_reviews_scraped > 0:
            consecutive_empty_pages += 1
            if consecutive_empty_pages >= 2:
                if verbose:
                    print("Two consecutive empty pages - scraping stopped.")
                break
        
        page_number += 1
        
        # Safety limit: Stop after 100 pages (in case something goes wrong)
        if page_number > 100:
            if verbose:
                print(f"\nWarning: Maximum page number (100) reached. Scraping stopped.")
            break

    # Remove duplicates based on all fields (not just Body)
    seen = set()
    unique_reviews = []
    for review in reviews_data:
        # Create a unique key from all relevant fields
        review_key = (
            review['Date'],
            review['Author'],
            review['Body'][:100] if review['Body'] else '',  # First 100 characters for comparison
            review['Rating']
        )
        if review_key not in seen:
            seen.add(review_key)
            unique_reviews.append(review)

    if verbose:
        print("-" * 60)
        print(f"Scraping completed!")
        print(f"Total found: {len(reviews_data)} reviews")
        print(f"After duplicate removal: {len(unique_reviews)} reviews")
        
        # Show business info
        if business_info:
            print(f"\n📊 Business Information:")
            print(f"   Name: {business_info.get('displayName', 'N/A')}")
            print(f"   TrustScore: {business_info.get('trustScore', 'N/A')}/10")
            print(f"   Total Reviews: {business_info.get('numberOfReviews', 'N/A')}")
            print(f"   Average Stars: {business_info.get('stars', 'N/A')}/5")
        
        # Statistics by location
        if unique_reviews:
            locations = Counter([r['Location'] for r in unique_reviews])
            print(f"\n🌍 Reviews by Location:")
            for location, count in sorted(locations.items(), key=lambda x: x[1], reverse=True):
                print(f"  {location}: {count} reviews")
    
    return {
        'reviews': unique_reviews,
        'business_info': business_info or {}
    }