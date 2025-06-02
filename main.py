import asyncio
from team_info import extract_team_info
from company_info import summarize_company_info
from clean_links import clean_and_save_links
from extract_links import crawl_and_save_links
from clean_links import clean_and_save_links
from company_info import summarize_company_info
from team_info import extract_team_info
from new_extract import extract_all_homepage_urls

def main():
    print("👋 Welcome to the Team Info Extractor")
    company_name = input("Enter the company name: ").strip()
    company_url = input("Enter the full URL of the company (e.g., https://thefirmadv.com): ").strip()

    if not company_name or not company_url:
        print("❌ Both company name and URL are required.")
        return
    
    # Step 1: Crawl links
    #crawl_and_save_links(company_url, company_name)
    print("crawling for urls")
    extract_all_homepage_urls(company_url,company_name)

    # Step 2: Clean/filter links
    cleaned_links = clean_and_save_links( company_name)
    print(f"🧹 Cleaned to {len(cleaned_links)} relevant links\n")

    # Step 3: Extract company info (async call)
    print("🏢 Extracting company info...")
    company_info = asyncio.run(summarize_company_info(company_url, company_name))
    print("✅ Company info:", company_info, "\n")
    
    # Step 4: Extract team members
    print("👥 Extracting team members...")
    team_members = asyncio.run(extract_team_info(company_name, company_url))
    print(f"✅ Found {len(team_members)} team members\n")

if __name__ == "__main__":
    main()
