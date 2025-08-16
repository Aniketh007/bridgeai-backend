from urllib.parse import urlparse
from typing import Tuple, List
from bs4 import BeautifulSoup

# ---------- URL State & Navigability Check ----------

def check_url_navigability(url: str, html: str) -> Tuple[int, List[str], List[str]]:
    score = 0
    issues = []
    recommendations = []

    try:
        soup = BeautifulSoup(html, "html.parser")

        # ✅ Canonical check
        canonical_link = soup.find("link", rel="canonical")
        if canonical_link and canonical_link.get("href"):
            score += 3
        else:
            issues.append("No canonical URL found.")
            recommendations.append("Add a <link rel='canonical'> tag to clarify the preferred URL.")

        # ✅ Deep-linking via anchor presence
        deep_links = [a.get("href") for a in soup.find_all("a", href=True) if urlparse(a['href']).netloc]
        if len(deep_links) >= 5:
            score += 4
        else:
            issues.append("Few or no deep links to inner content found.")
            recommendations.append("Add proper anchor links to internal, uniquely-addressable pages.")

        # ✅ URL pattern checks
        parsed = urlparse(url)
        if "#" not in parsed.path and len(parsed.query) < 60:
            score += 3
        else:
            issues.append("URL contains fragments or long query strings.")
            recommendations.append("Use clean, RESTful URLs without # or long query parameters.")

        # ✅ State persistence test (only simulated here)
        if "?" in url or "#" in url:
            score -= 1  # potential client-side state
            issues.append("Page may rely on client-side fragments or params.")
        else:
            score += 1  # likely stateless

        # ✅ Bonus if page has breadcrumb or back-link
        breadcrumbs = soup.find_all("nav", {"aria-label": "breadcrumb"})
        if breadcrumbs:
            score += 1

        return min(score, 15), issues, recommendations

    except Exception as e:
        issues.append("Failed to evaluate URL state & navigability.")
        recommendations.append(f"Error: {str(e)}")
        return 0, issues, recommendations