import httpx
from typing import List, Optional
import re

class WikiService:
    BASE_URL = "https://en.wikipedia.org/w/api.php"
    HEADERS = {
        "User-Agent": "WikiRacerGame/1.0 (Educational Project; contact: wiki-racer@example.com)"
    }
    
    async def get_links(self, page_title: str) -> List[str]:
        params = {
            "action": "query",
            "format": "json",
            "titles": page_title,
            "prop": "links",
            "pllimit": "max",
            "redirects": 1
        }
        
        links = []
        async with httpx.AsyncClient(headers=self.HEADERS) as client:
            while True:
                response = await client.get(self.BASE_URL, params=params)
                if response.status_code != 200:
                    break
                try:
                    data = response.json()
                except Exception:
                    break
                
                pages = data.get("query", {}).get("pages", {})
                for page_id, page_data in pages.items():
                    if "links" in page_data:
                        for link in page_data["links"]:
                            if link.get("ns") == 0:
                                links.append(link.get("title"))
                
                if "continue" in data:
                    params.update(data["continue"])
                else:
                    break
                    
        return links

    async def get_random_pages(self, count: int = 2) -> List[str]:
        params = {
            "action": "query",
            "format": "json",
            "list": "random",
            "rnnamespace": 0,
            "rnlimit": count
        }
        async with httpx.AsyncClient(headers=self.HEADERS) as client:
            try:
                response = await client.get(self.BASE_URL, params=params)
                print(f"WIKI RANDOM RESPONSE STATUS: {response.status_code}")
                if response.status_code != 200:
                    print(f"WIKI ERROR BODY: {response.text}")
                    return []
                data = response.json()
                pages = [item["title"] for item in data.get("query", {}).get("random", [])]
                print(f"WIKI FETCHED RANDOM PAGES: {pages}")
                return pages
            except Exception as e:
                print(f"WIKI FETCH EXCEPTION: {str(e)}")
                return []

    async def get_vital_article_titles(self, level: int = 4) -> List[str]:
        # Using the Action API 'parse' endpoint with prop=links is the most robust method.
        # Level 3 is one page. Level 4 is split into 11 sub-pages.
        
        pages_to_fetch = []
        if level == 3:
            pages_to_fetch = ["Wikipedia:Vital articles/Level/3"]
        elif level == 4:
            pages_to_fetch = [
                "Wikipedia:Vital articles/Level/4/People",
                "Wikipedia:Vital articles/Level/4/History",
                "Wikipedia:Vital articles/Level/4/Geography",
                "Wikipedia:Vital articles/Level/4/Arts",
                "Wikipedia:Vital articles/Level/4/Everyday life",
                "Wikipedia:Vital articles/Level/4/Philosophy and religion",
                "Wikipedia:Vital articles/Level/4/Society and social sciences",
                "Wikipedia:Vital articles/Level/4/Biology and health sciences",
                "Wikipedia:Vital articles/Level/4/Physical sciences",
                "Wikipedia:Vital articles/Level/4/Technology",
                "Wikipedia:Vital articles/Level/4/Mathematics"
            ]

        titles = set()
        async with httpx.AsyncClient(headers=self.HEADERS) as client:
            for page in pages_to_fetch:
                print(f"Fetching sub-page: {page}")
                params = {
                    "action": "parse",
                    "format": "json",
                    "page": page,
                    "prop": "links",
                    "redirects": 1
                }
                try:
                    response = await client.get(self.BASE_URL, params=params)
                    if response.status_code == 200:
                        data = response.json()
                        links = data.get("parse", {}).get("links", [])
                        for link in links:
                            # ns: 0 is the Main/Article namespace
                            if link.get("ns") == 0:
                                titles.add(link.get("*"))
                except Exception as e:
                    print(f"Error fetching sub-page {page}: {e}")
                
        return list(titles)

    async def get_page_html(self, page_title: str) -> Optional[str]:
        # Using Action API 'parse' which is better at handling redirects and normalization
        params = {
            "action": "parse",
            "format": "json",
            "page": page_title,
            "prop": "text",
            "redirects": 1,
            "mobileformat": 1
        }
        async with httpx.AsyncClient(headers=self.HEADERS) as client:
            response = await client.get(self.BASE_URL, params=params)
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    return None
                return data.get("parse", {}).get("text", {}).get("*")
            return None

wiki_service = WikiService()
