import requests
from urllib.parse import urljoin
from typing import Tuple, List
from bs4 import BeautifulSoup
import re


# ---------- Data Feed Availability Check ----------

def check_data_feed_availability(url: str, html: str) -> Tuple[int, List[str], List[str]]:
    issues = []
    recommendations = []
    score = 0

    try:
        soup = BeautifulSoup(html, "html.parser")

        base_url = re.match(r"https?://[^/]+", url)
        base_url = base_url.group(0) if base_url else url

        # 1. Look for RSS or Atom feeds
        feed_links = soup.find_all("link", type=re.compile("application/(rss|atom)\\+xml"))
        if feed_links:
            score += 2
        else:
            issues.append("No RSS or Atom feed detected.")
            recommendations.append("Add <link rel='alternate' type='application/rss+xml'> in <head>.")

        # 2. Structured data presence (proxy for validity)
        if soup.find("script", type="application/ld+json"):
            score += 1
        else:
            issues.append("No embedded structured data found.")
            recommendations.append("Use JSON-LD or Microdata to publish content in machine-readable form.")

        # 3. robots.txt contains sitemap or feed URLs
        try:
            robots_url = urljoin(base_url, "/robots.txt")
            robots_txt = requests.get(robots_url, timeout=5).text.lower()
            if "sitemap:" in robots_txt or "rss" in robots_txt or "atom" in robots_txt:
                score += 1
        except Exception:
            issues.append("robots.txt could not be retrieved.")
            recommendations.append("Ensure robots.txt exists and includes sitemap or feed references.")

        # 4. Public API endpoint check (common patterns)
        api_keywords = ["/api", "/feeds", "/openapi", "/wp-json", "/graphql"]
        if any(keyword in html.lower() for keyword in api_keywords):
            score += 1
        else:
            issues.append("No API or feed endpoint references found.")
            recommendations.append("Expose an API or open data endpoint (e.g., /api, /feeds, /openapi.json).")

        score = max(0, min(score, 5))
        return score, issues, recommendations

    except Exception as e:
        issues.append("Data feed availability check failed.")
        recommendations.append(f"{type(e).__name__}: {str(e)}")
        return 0, issues, recommendations