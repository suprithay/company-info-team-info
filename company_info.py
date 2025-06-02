import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv
import os
from extract_links import crawl_and_save_links

# Load API keys
load_dotenv()
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

async def get_relevant_pages(company_name):
    try:
        input_file = f"{company_name.replace(' ', '_')}_links.txt"
        with open(input_file, "r") as f:
            links = [line.strip() for line in f.readlines()]
            print(f"📄 Loaded {len(links)} links from file.")
    except FileNotFoundError:
        print("❌ Error: links.txt not found. Run firecrawl_links.py first.")
        return []

    relevant_keywords = ["about", "strategy", "portfolio", "criteria", "investment", "blog", "media"]
    relevant_links = [link for link in links if any(kw in link.lower() for kw in relevant_keywords)]
    print(f"✅ Found {len(relevant_links)} relevant links.", relevant_links)
    return relevant_links

async def extract_text_from_url(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=60000)
        content = await page.content()
        soup = BeautifulSoup(content, "html.parser")
        await browser.close()

        for tag in soup(["script", "style", "nav", "footer", "header", "svg"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        return text

def text_truncate(text, max_length):
    return text[:max_length] if len(text) > max_length else text

def generate_prompt(company_name, full_text):
    return f"""
    You are an expert investment analyst at **Dark Alpha Capital**, a private equity firm that specializes in acquiring profitable, growth-stage companies. Your task is to review information extracted from various web pages of a company and provide a detailed investment memo.

    The data below includes website text and any public business details available for the company: **{company_name}**

    ----
    {text_truncate(full_text, 50000)}
    ----

    Please perform the following:

    1. **Company Overview:**
       - Company Name (if identifiable)
       - Industry or Sector
       - Business Model / Description
       - Location or Headquarters (if available)
       - Website content highlights (mission, services, clients, etc.)

    2. **Financial Metrics (Extract or Infer if mentioned or implied):**
       - Annual Revenue
       - EBITDA
       - EBITDA Margin
       - Asking Price or Valuation
       - Any other relevant financial detail

    3. **Investment Criteria Alignment (Based on Dark Alpha Capital’s criteria):**
       - Minimum Revenue: $2M
       - Minimum EBITDA: $1M
       - EBITDA Margin: ≥ 15%
       - Preferred Industries: Technology, SaaS, Healthcare, Fintech, B2B Services
       - Business Characteristics: Founder-led, cash-flow positive, scalable model, private ownership, recurring revenue

    4. **Decision: Should Dark Alpha Capital Invest?**
       - Answer: **"Suitable for Investment"** or **"Not Suitable"**
       - Give **3 to 5 reasons** for your conclusion based on strengths or red flags
       - If data is missing, state what’s missing and how that affects your assessment

    5. **Caveats or Uncertainties:**
       - Mention any limitations in the data or assumptions you made

    Be detailed and reason through your assessment like a professional investor conducting due diligence. Write this as if preparing a summary for the internal investment committee.
    """


def summarize_with_perplexity(company_name, full_text):
    url = "https://api.perplexity.ai/chat/completions"
    prompt = generate_prompt(company_name, full_text)
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "sonar",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        raise Exception(f"Perplexity API error: {response.text}")

def summarize_with_gemini(company_name, full_text):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    prompt = generate_prompt(company_name, full_text)
    headers = {
        "Content-Type": "application/json"
    }
    params = {
        "key": GEMINI_API_KEY
    }
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    response = requests.post(url, headers=headers, params=params, json=data)
    if response.status_code == 200:
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    else:
        raise Exception(f"Gemini API error: {response.text}")

def summarize_with_firecrawl(company_name, full_text):
    url = "https://api.firecrawl.dev/chat/completions"
    prompt = generate_prompt(company_name, full_text)
    headers = {
        "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "messages": [{"role": "user", "content": prompt}],
        "model": "gpt-4",
        "temperature": 0.7
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        raise Exception(f"Firecrawl API error: {response.text}")

async def summarize_company_info(company_url: str, company_name: str):
    output_file = f"{company_name.replace(' ', '_')}_summary.txt"
    print(f"🔍 Crawling {company_url} for relevant pages...")

    relevant_urls = await get_relevant_pages(company_name)
    print(f"Found {len(relevant_urls)} relevant URLs: {relevant_urls}")
    
    all_text = ""
    if not relevant_urls:
        print(f"📄 No relevant links found. Scraping all available links from: {company_name}_links.txt")
        try:
            with open(f"{company_name.replace(' ', '_')}_clean_links.txt", "r") as f:
                fallback_links = [line.strip() for line in f.readlines()]
        except FileNotFoundError:
            print(f"❌ Error: {company_name}_links.txt not found.")
            return None

        for url in fallback_links[:10]:  # Limit to 10 to avoid overloading
            try:
                print(f"📄 Scraping fallback URL: {url}")
                text = await extract_text_from_url(url)
                all_text += "\n\n" + text
            except Exception as e:
                print(f"⚠️ Failed to extract text from {url}: {e}")

    else:
        for url in relevant_urls[:10]:  # Limit to 10 pages
            print(f"📄 Scraping {url} ...")
            text = await extract_text_from_url(url)
            all_text += "\n\n" + text
    
    print("🧠 Summarizing...")
    try:
        summary = summarize_with_perplexity(company_name, all_text)
        print("✅ Used Perplexity for summarization.")
    except Exception as e1:
        print(f"⚠️ Perplexity failed: {e1}")
        try:
            summary = summarize_with_gemini(company_name, all_text)
            print("✅ Used Gemini for summarization.")
        except Exception as e2:
            print(f"⚠️ Gemini failed: {e2}")
            try:
                summary = summarize_with_firecrawl(company_name, all_text)
                print("✅ Used Firecrawl for summarization.")
            except Exception as e3:
                print(f"❌ All summarization attempts failed: {e3}")
                return None

    with open(output_file, "w") as f:
        f.write(summary)

    print("\n✅ Summary:\n")
    print(summary)
    return summary


