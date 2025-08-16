from typing import Tuple, List
from bs4 import BeautifulSoup
import re

# ---------- Logical Content Flow Check ----------

def check_logical_content_flow(url: str, html: str) -> Tuple[int, List[str], List[str]]:
    issues = []
    recommendations = []
    score = 0

    try:
        soup = BeautifulSoup(html, "html.parser")

        # 1. Heading followed by paragraph sequence
        content_blocks = soup.find_all(["h1", "h2", "h3", "p"])
        has_good_flow = False
        for i in range(len(content_blocks) - 1):
            if content_blocks[i].name.startswith("h") and content_blocks[i + 1].name == "p":
                has_good_flow = True
                break
        if has_good_flow:
            score += 2
        else:
            issues.append("Heading and paragraph content appears disjointed.")
            recommendations.append("Ensure each section begins with a heading followed by content.")

        # 2. Top-loaded content
        body = soup.find("body")
        early_text = body.get_text(strip=True)[:500] if body else ""
        if len(early_text.split()) >= 30:
            score += 1
        else:
            issues.append("Content is not top-loaded.")
            recommendations.append("Place primary text content closer to the top of the page.")

        # 3. Disruptive interjections (ads, overlays)
        disruptive_keywords = ["popup", "subscribe", "ad-", "cookie", "banner"]
        if any(re.search(k, html, re.I) for k in disruptive_keywords):
            issues.append("Potential interruptions found (ads, popups, modals).")
            recommendations.append("Avoid disrupting the main content flow with overlays or interstitials.")
        else:
            score += 1

        # 4. Visual/semantic grouping
        if soup.find("section") or soup.find("hr") or soup.find("article"):
            score += 1
        else:
            issues.append("No semantic grouping or content segmentation.")
            recommendations.append("Use <section>, <article>, or <hr> for logical content separation.")

        score = max(0, min(score, 5))
        return score, issues, recommendations

    except Exception as e:
        issues.append("Content flow check failed.")
        recommendations.append(f"{type(e).__name__}: {str(e)}")
        return 0, issues, recommendations