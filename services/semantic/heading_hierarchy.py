from typing import Tuple, List
from bs4 import BeautifulSoup

# ---------- Heading Hierarchy Check ----------

def check_heading_hierarchy(url: str, html: str) -> Tuple[int, List[str], List[str]]:
    issues = []
    recommendations = []
    score = 0

    try:
        soup = BeautifulSoup(html, "html.parser")

        headings = []
        for level in range(1, 7):
            tags = soup.find_all(f"h{level}")
            for tag in tags:
                headings.append((level, tag.text.strip()))

        if not headings:
            issues.append("No heading tags found on the page.")
            recommendations.append("Add <h1> to <h6> elements to structure content for both users and agents.")
            return 0, issues, recommendations

        heading_levels = [lvl for lvl, _ in headings]

        # Check for at least one <h1>
        h1_count = heading_levels.count(1)
        if h1_count == 1:
            score += 2
        elif h1_count > 1:
            score += 1
            issues.append(f"Multiple <h1> tags found ({h1_count}).")
            recommendations.append("Use only one <h1> to represent the main topic of the page.")
        else:
            issues.append("No <h1> tag found.")
            recommendations.append("Add a <h1> tag for the main page title.")

        # Check diversity of heading levels
        unique_levels = set(heading_levels)
        if len(unique_levels) >= 3:
            score += 3
        else:
            score += 1
            issues.append("Limited heading level usage.")
            recommendations.append("Use a broader heading structure (e.g., <h2> and <h3> under <h1>).")

        # Check for skipped hierarchy (e.g., h2 → h4)
        for i in range(len(heading_levels) - 1):
            current = heading_levels[i]
            nxt = heading_levels[i + 1]
            if nxt > current + 1:
                issues.append(f"Heading structure skips from <h{current}> to <h{nxt}>.")
                recommendations.append("Avoid skipping heading levels — use consistent nesting (e.g., h2 → h3 → h4).")
                score -= 1
                break
        else:
            score += 2

        return max(0, min(score, 10)), issues, recommendations

    except Exception as e:
        issues.append("Heading hierarchy check failed.")
        recommendations.append(f"{type(e).__name__}: {str(e)}")
        return 0, issues, recommendations