from urllib.parse import urlparse, urljoin
from typing import Tuple, List
from bs4 import BeautifulSoup
import re

# ---------- Internal Linking Check ----------

def check_internal_linking(url: str, html: str) -> Tuple[int, List[str], List[str]]:
    issues = []
    recommendations = []
    score = 0

    try:
        soup = BeautifulSoup(html, "html.parser")
        parsed = urlparse(url)
        domain = parsed.netloc

        # 1. Internal anchor tags
        internal_links = []
        descriptive_links = []

        for a in soup.find_all("a", href=True):
            href = a["href"]
            anchor_text = a.get_text(strip=True)
            full_url = urljoin(url, href)
            if domain in urlparse(full_url).netloc:
                internal_links.append(full_url)
                if len(anchor_text.split()) >= 5:
                    descriptive_links.append(anchor_text)

        internal_links = list(set(internal_links))  # remove duplicates

        if len(internal_links) >= 10:
            score += 2
        else:
            issues.append(f"Only {len(internal_links)} internal links found.")
            recommendations.append("Add more internal links for better crawlability and content discovery.")

        if len(descriptive_links) >= 3:
            score += 1
        else:
            issues.append("Anchor text is mostly short or generic.")
            recommendations.append("Use meaningful anchor text (5+ words) for clarity and relevance.")

        # 2. Navigation structure
        if soup.find("nav") or soup.find("ul", class_=re.compile("menu|nav", re.I)):
            score += 1
        else:
            issues.append("No navigation or menu structure detected.")
            recommendations.append("Use <nav> or sidebar menus to organize internal links.")

        # 3. Lateral/hierarchical signals (breadcrumbs, related)
        patterns = ["breadcrumb", "related", "next", "prev", "sidebar", "section"]
        if any(re.search(pat, html, re.I) for pat in patterns):
            score += 1
        else:
            issues.append("No hierarchical or lateral linking patterns found.")
            recommendations.append("Add breadcrumbs, related articles, or hierarchical content links.")

        score = max(0, min(score, 5))
        return score, issues, recommendations

    except Exception as e:
        issues.append("Internal linking check failed.")
        recommendations.append(f"{type(e).__name__}: {str(e)}")
        return 0, issues, recommendations