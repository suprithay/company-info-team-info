from firecrawl import FirecrawlApp
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
firecrawl = FirecrawlApp(api_key=FIRECRAWL_API_KEY)

def crawl_and_save_links(base_url: str, company_name: str):
    try:
        print(f"🔍 Crawling {base_url} ...")
        map_result = firecrawl.map_url(base_url)
        links = map_result.links
        print(f"✅ Found {len(links)} links")

        output_file = f"{company_name.replace(' ', '_')}_links.txt"
        with open(output_file, "w") as f:
            for link in links:
                f.write(link + "\n")

        print(f"📁 Links saved to {output_file}")
        return links  # ✅ Return links here
    except Exception as e:
        print(f"❌ Error during crawling: {e}")
        return []
