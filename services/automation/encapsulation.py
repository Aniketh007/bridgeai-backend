import requests
from typing import Tuple, List
from bs4 import BeautifulSoup

# ---------- Encapsulation Analysis Check ----------

def check_encapsulation_analysis(url: str, html: str) -> Tuple[float, List[str], List[str]]:
    score = 0.0
    issues = []
    recommendations = []

    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        # Check for iframes
        iframes = soup.find_all("iframe")
        if len(iframes) == 0:
            score += 1
        else:
            issues.append(f"{len(iframes)} <iframe> elements found.")
            recommendations.append("Avoid excessive iframe usage for core content.")

        # Shadow DOM can't be parsed directly via static HTML
        if "shadowRoot" in res.text or "attachShadow" in res.text:
            issues.append("Shadow DOM usage detected via JavaScript.")
            recommendations.append("Avoid Shadow DOM for critical UI or provide semantic fallback.")
        else:
            score += 1

        # Check for semantic containers
        if soup.find("main") or soup.find("section"):
            score += 0.5
        else:
            recommendations.append("Use semantic HTML containers like <main>, <section>, etc.")

        # Check for div soup
        body = soup.find("body")
        if body:
            divs = body.find_all("div", recursive=True)
            tags = body.find_all(True, recursive=True)
            if divs and len(divs) / len(tags) > 0.7:
                issues.append("Main content is overly encapsulated in <div> soup.")
                recommendations.append("Replace div blocks with semantic HTML structure.")
            else:
                score += 0.5

        return round(min(score, 2.5), 2), issues, recommendations

    except Exception as e:
        issues.append("Encapsulation analysis failed.")
        recommendations.append(str(e))
        return 0.0, issues, recommendations