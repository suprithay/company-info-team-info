# clean_links.py
import re
from urllib.parse import urlparse

def normalize_url(url):
    # Convert to lowercase
    url = url.lower()
    # Remove protocol (http/https)
    url = re.sub(r'^https?://', '', url)
    # Remove 'www.' prefix
    url = re.sub(r'^www\.', '', url)
    # Parse URL
    parsed = urlparse('http://' + url)  # Add dummy protocol for parsing
    # Normalize path: replace spaces with hyphens
    path = parsed.path.replace(' ', '-')
    # Remove trailing slash
    path = path.rstrip('/')
    # Rebuild normalized URL (without protocol)
    normalized = parsed.netloc + path
    return normalized

def deduplicate_urls(url_list):
    seen = set()
    deduped = []
    for url in url_list:
        norm = normalize_url(url)
        if norm not in seen and ' ' not in url:
            seen.add(norm)
            deduped.append(url)
    return deduped

def clean_and_save_links(company_name):
    """
    Reads raw links from file, deduplicates and cleans them, then saves to a new file.
    """
    try:
        filename = f"{company_name.replace(' ', '_')}_links.txt"
        with open(filename, "r") as f:
            urls = [line.strip() for line in f.readlines()]

        unique_urls = deduplicate_urls(urls)
        cleaned_urls = [url for url in unique_urls if ' ' not in url]

        output_file = f"{company_name.replace(' ', '_')}_clean_links.txt"
        with open(output_file, 'w') as f:
            for url in cleaned_urls:
                f.write(url + '\n')

        print(f"✅ Cleaned and deduplicated links saved to: {output_file}")
        return cleaned_urls

    except FileNotFoundError:
        print(f"❌ File not found for {company_name}. Make sure the crawling step succeeded.")
        return []

    except Exception as e:
        print(f"❌ Error cleaning links: {e}")
        return []

# Example usage from another script:
# from clean_links import clean_and_save_links
# cleaned = clean_and_save_links("TheFirm")
