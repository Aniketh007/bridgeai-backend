from typing import Tuple, List
from bs4 import BeautifulSoup
# ---------- Content Formatting Check ----------

def check_content_formatting(url: str, html: str) -> Tuple[int, List[str], List[str]]:
    issues = []
    recommendations = []
    score = 0

    try:
        soup = BeautifulSoup(html, "html.parser")

        # 1. Paragraphs
        paragraphs = soup.find_all("p")
        if len(paragraphs) >= 3:
            score += 3
        else:
            score += 1
            issues.append("Page contains few or no <p> tags.")
            recommendations.append("Use <p> elements to mark up readable text blocks.")

        # 2. Lists
        ul = soup.find_all("ul")
        ol = soup.find_all("ol")
        dl = soup.find_all("dl")
        if len(ul) + len(ol) + len(dl) > 0:
            score += 2
        else:
            issues.append("No semantic list tags (<ul>, <ol>, <dl>) found.")
            recommendations.append("Use semantic HTML list tags for structured information.")

        # 3. Tables
        tables = soup.find_all("table")
        good_tables = 0
        for table in tables:
            if table.find("th") and table.find("tr") and table.find("td"):
                good_tables += 1
        if good_tables > 0:
            score += 2
        else:
            issues.append("Tables found, but without proper semantic structure.")
            recommendations.append("Use <th>, <td>, <thead>, and <tbody> inside tables.")

        # 4. Avoids text-in-image misuse
        images_with_text = [img for img in soup.find_all("img") if img.get("alt") and len(img["alt"].split()) >= 5]
        buttons_with_text = [btn for btn in soup.find_all("button") if btn.text and len(btn.text.split()) >= 5]
        if len(images_with_text) > 5 or len(buttons_with_text) > 10:
            issues.append("Too much descriptive text inside <img> alt or <button>.")
            recommendations.append("Avoid encoding full content in alt tags or button labels.")
        else:
            score += 2

        # 5. Quote/code formatting
        if soup.find("pre") or soup.find("code") or soup.find("blockquote"):
            score += 1
        else:
            issues.append("No semantic formatting for quotes or code.")
            recommendations.append("Use <pre>, <code>, or <blockquote> for formatted content.")

        score = max(0, min(score, 10))
        return score, issues, recommendations

    except Exception as e:
        issues.append("Content formatting check failed.")
        recommendations.append(f"{type(e).__name__}: {str(e)}")
        return 0, issues, recommendations