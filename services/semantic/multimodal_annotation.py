from typing import Tuple, List
from bs4 import BeautifulSoup

# ---------- Multimodal Annotation Check ----------

def check_multimodal_annotation(url: str, html: str) -> Tuple[int, List[str], List[str]]:
    issues = []
    recommendations = []
    score = 0

    try:
        soup = BeautifulSoup(html, "html.parser")

        # 1. Alt text on images
        img_tags = soup.find_all("img")
        well_annotated = [img for img in img_tags if img.get("alt") and len(img["alt"].split()) >= 5]
        if len(well_annotated) >= 3:
            score += 2
        else:
            issues.append("Images lack descriptive alt text.")
            recommendations.append("Add meaningful alt text to images (≥5 words).")

        # 2. <track> in <video>/<audio>
        has_tracks = any(tag.find("track") for tag in soup.find_all(["video", "audio"]))
        if has_tracks:
            score += 1
        else:
            issues.append("Multimedia content lacks subtitles or captions.")
            recommendations.append("Use <track> for subtitles/captions in <video> and <audio> tags.")

        # 3. <figure> + <figcaption>
        figures = soup.find_all("figure")
        with_caption = [fig for fig in figures if fig.find("figcaption")]
        if with_caption:
            score += 1
        else:
            issues.append("Figures are missing captions.")
            recommendations.append("Use <figcaption> inside <figure> for better content clarity.")

        # 4. Custom UI labels
        canvas_or_icon = soup.select("canvas, svg, i, span[role], [aria-label], [title]")
        if any(canvas_or_icon):
            score += 1

        score = max(0, min(score, 5))
        return score, issues, recommendations

    except Exception as e:
        issues.append("Multimodal content annotation check failed.")
        recommendations.append(f"{type(e).__name__}: {str(e)}")
        return 0, issues, recommendations