from typing import Tuple, List
from bs4 import BeautifulSoup

# ---------- Data Payload Cleanliness Check ----------

def check_data_payload_cleanliness(url: str, html: str) -> Tuple[int, List[str], List[str]]:
    issues = []
    recommendations = []
    score = 20  # Start with max, subtract penalties

    try:
        soup = BeautifulSoup(html, "html.parser")

        # --- 1. Text-to-HTML ratio ---
        text = soup.get_text(separator=' ', strip=True)
        text_length = len(text)
        html_length = len(html)
        ratio = text_length / html_length if html_length else 0

        if ratio < 0.1:
            score -= 5
            issues.append("Low text-to-HTML ratio (<10%).")
            recommendations.append("Reduce clutter and increase visible, extractable text.")

        # --- 2. Script & Style Tag Noise ---
        script_tags = soup.find_all("script")
        style_tags = soup.find_all("style")
        iframe_tags = soup.find_all("iframe")

        if len(script_tags) > 30:
            score -= 4
            issues.append("Too many <script> tags (>30).")
            recommendations.append("Remove or defer unnecessary scripts.")

        if len(style_tags) > 10:
            score -= 2
            issues.append("Excessive <style> tags.")
            recommendations.append("Consolidate CSS files or move inline styles.")

        if len(iframe_tags) > 5:
            score -= 2
            issues.append("Too many <iframe> elements.")
            recommendations.append("Avoid embedding multiple third-party resources.")

        # --- 3. Clutter Signatures ---
        clutter_patterns = [
            "googletagmanager", "doubleclick", "facebook", "fb:", "analytics", "adsbygoogle",
            "cookieconsent", "optanon", "gpt-ad"
        ]
        clutter_matches = sum(1 for pat in clutter_patterns if pat in html.lower())

        if clutter_matches > 3:
            score -= 3
            issues.append("Page contains many known tracker/ad components.")
            recommendations.append("Minimize 3rd-party scripts and tracking overhead.")

        # --- 4. Div Soup & Inline CSS ---
        div_count = len(soup.find_all("div"))
        span_count = len(soup.find_all("span"))
        inline_styles = len(soup.select("[style]"))

        if div_count > 150 or span_count > 100:
            score -= 3
            issues.append("Page uses excessive <div>/<span> tags.")
            recommendations.append("Use semantic HTML elements instead of generic containers.")

        if inline_styles > 50:
            score -= 2
            issues.append("Too many inline styles found.")
            recommendations.append("Move styles to CSS files for better clarity and maintainability.")

        # Clamp score between 0 and 20
        score = max(0, min(score, 20))
        return score, issues, recommendations

    except Exception as e:
        issues.append("Cleanliness evaluation failed.")
        recommendations.append(f"{type(e).__name__}: {str(e)}")
        return 0, issues, recommendations