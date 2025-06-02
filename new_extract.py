from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright

def extract_all_homepage_urls(base_url,company_name):
    """
    Extracts all unique URLs from the homepage of the given website.
    """
    unique_urls = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            print(f"Visiting: {base_url}")
            page.goto(base_url, timeout=30000, wait_until='domcontentloaded')
            html_content = page.content()
            soup = BeautifulSoup(html_content, "html.parser")

            for link in soup.find_all("a", href=True):
                href = link["href"].strip()

                # Normalize and resolve relative URLs
                full_url = urljoin(base_url, href)

                # Clean fragment identifiers, javascript links
                if full_url.startswith("javascript:") or full_url.startswith("mailto:"):
                    continue

                # Optional: Restrict to same domain
                if urlparse(full_url).netloc == urlparse(base_url).netloc:
                    unique_urls.add(full_url)
    
            print(f"\nExtracted {len(unique_urls)} URLs from homepage:")
            for u in unique_urls:
                print(u)
            output_file = f"{company_name.replace(' ', '_')}_links.txt"
            with open(output_file, "w") as f:
                for link in unique_urls:
                    f.write(link + "\n")

        except Exception as e:
            print(f"Error while processing {base_url}: {e}")
        finally:
            browser.close()

    return list(unique_urls)
'''
if __name__ == "__main__":
    input_url = input("Enter homepage URL: ").strip()
    company_name = input("Enter company name: ").strip()
    homepage_urls = extract_all_homepage_urls(input_url)
    print(f"\nExtracted {len(homepage_urls)} URLs from homepage:")
    for u in homepage_urls:
        print(u)
    output_file = f"{company_name.replace(' ', '_')}_links.txt"
    with open(output_file, "w") as f:
        for link in homepage_urls:
            f.write(link + "\n")
'''