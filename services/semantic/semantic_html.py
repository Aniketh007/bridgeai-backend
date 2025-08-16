from typing import Tuple, List
from bs4 import BeautifulSoup

# ---------- Semantic HTML Fidelity Check ----------

def check_semantic_html_fidelity(url: str, html: str) -> Tuple[int, List[str], List[str]]:
    issues = []
    recommendations = []
    score = 15  # Start with max score

    try:
        soup = BeautifulSoup(html, "html.parser")

        # 1. Semantic tag usage
        semantic_tags = [
            "header", "footer", "main", "nav", "article", "section", "aside", "figure", "figcaption", "time", "address"
        ]
        used_semantics = [tag for tag in semantic_tags if soup.find(tag)]

        if len(set(used_semantics)) >= 4:
            pass  # full points
        else:
            score -= 5
            issues.append("Few or no semantic HTML5 tags used.")
            recommendations.append("Use more semantic elements like <main>, <article>, <section>, etc.")

        # 2. Main content wrapper
        if soup.find("main") or soup.find("article"):
            pass  # +3 points by default
        else:
            score -= 3
            issues.append("No <main> or <article> tag used to wrap main content.")
            recommendations.append("Use <main> or <article> to designate the central content block.")

        # 3. Header/Footer presence
        if not soup.find("header") or not soup.find("footer"):
            score -= 3
            issues.append("Missing <header> or <footer> tags.")
            recommendations.append("Include <header> and <footer> for document structure clarity.")

        # 4. Sectioning structure
        if soup.find("section") or soup.find("aside"):
            score += 2  # bonus

        # 5. Div/Span soup penalty
        divs = len(soup.find_all("div"))
        spans = len(soup.find_all("span"))
        if divs + spans > 300:
            score -= 4
            issues.append("Overuse of <div> and <span> tags.")
            recommendations.append("Replace with semantic HTML5 tags where possible.")

        score = max(0, min(score, 15))
        return score, issues, recommendations

    except Exception as e:
        issues.append("Semantic HTML fidelity check failed.")
        recommendations.append(f"{type(e).__name__}: {str(e)}")
        return 0, issues, recommendations