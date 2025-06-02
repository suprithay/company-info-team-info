import re
import json
import asyncio
from firecrawl import FirecrawlApp
from dotenv import load_dotenv
from urllib.parse import urlparse
import os

load_dotenv()
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
firecrawl = FirecrawlApp(api_key=FIRECRAWL_API_KEY)

def get_team_links(company_name):
    input_file = f"{company_name.replace(' ', '_')}_links.txt"
    with open(input_file, "r") as f:
        links = [line.strip() for line in f.readlines()]
    
        team_keywords = [
            "team-members", "our-team", "leadership", "people", 
            "partners", "who-we-are", "about-us", "management", "meet-the-team", "team"
        ]

        def is_team_link(url):
            path = urlparse(url).path.lower()
            return any(kw in path for kw in team_keywords)

        team_links = [link for link in links if is_team_link(link)]
        if not team_links:
            print("⚠️ No specific team links found. Will default to homepage if needed.")
        return team_links
    

def extract_team_details(url: str) -> dict:
    prompt = """
    Extract the following structured information about the firm team members from this webpage:

    - teamMembers: For each key team member (especially founders, managing director, director and partners), include:
        - firstName
        - lastName
        - description (role or title)
        - linkedInUrl (if available)
        - pastDeals: A list of notable past deals, with name and a short description.
        - bio (short background)

    Return all fields in a single JSON object. If a field is not available, return an empty string or empty list.
    """

    schema = {
        "type": "object",
        "properties": {
            "teamMembers": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "firstName": {"type": "string"},
                        "lastName": {"type": "string"},
                        "description": {"type": "string"},
                        "linkedInUrl": {"type": "string"},
                        "bio": {"type": "string"},
                        "pastDeals": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "description": {"type": "string"}
                                },
                                "required": ["name", "description"]
                            }
                        }
                    },
                    "required": ["firstName", "lastName", "description", "bio", "pastDeals", "linkedInUrl"]
                }
            }
        },
        "required": ["teamMembers"]
    }

    try:
        resp = firecrawl.extract(
            urls=[url],
            prompt=prompt,
            schema=schema
        )
        data = resp.data
        return {
            "url": url,
            "teamMembers": data.get("teamMembers", [])
        }
    except Exception as e:
        print(f"❌ Error extracting from {url}: {e}")
        return {"url": url, "teamMembers": []}


def extract_directors_only(team_members: list) -> list:
    directors = []
    for member in team_members:
        role = member.get("description", "").lower()
        if "managing director" in role or role == "director":
            summary = (
                f"{member.get('firstName', '')} {member.get('lastName', '')} serves as {member.get('description', '')}. "
                f"With a background in {member.get('bio', '').lower()}, they bring extensive expertise to the firm."
            )
            directors.append({
                "firstName": member.get("firstName", ""),
                "lastName": member.get("lastName", ""),
                "description": member.get("description", ""),
                "linkedInUrl": member.get("linkedInUrl", ""),
                "bio": member.get("bio", ""),
                "summary": summary.strip()
            })
    return directors

async def extract_team_info(company_name: str, company_url: str):
    team_links = get_team_links(company_name)
    print("🔗 Found team links:", team_links)

    all_team_members = []
    if not team_links:
        print(f"🧑‍💼 Scraping team page: {company_url}")
        team_data = extract_team_details(company_url)
        all_team_members.extend(team_data["teamMembers"])
    else:
        for url in team_links[:10]:
            print(f"🧑‍💼 Scraping team page: {url}")
            team_data = extract_team_details(url)
            all_team_members.extend(team_data["teamMembers"])

    output_file = f"{company_name.replace(' ', '_')}_team_info.json"
    with open(output_file, "w") as f:
        json.dump(all_team_members, f, indent=2)
    print("✅ Saved all team members to", output_file)

    directors = extract_directors_only(all_team_members)
    output_file_leaders = f"{company_name.replace(' ', '_')}_leaders_info.json"
    with open(output_file_leaders, "w") as f:
        json.dump(directors, f, indent=2)
    print("⭐ Saved directors to", output_file_leaders)

    return {
        "team_members_file": output_file,
        "directors_file": output_file_leaders,
        "team_members": all_team_members,
        "directors": directors
    }
