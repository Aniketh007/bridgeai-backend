from typing import Tuple, List
from bs4 import BeautifulSoup
import re

# ---------- Intrusive Elements Check ----------

def check_intrusive_elements(html: str) -> Tuple[int, List[str], List[str]]:
    """
    Evaluates the presence of intrusive UI elements like popups, modals, interstitials, etc.
    Returns a score out of 2.5, a list of issues, and recommendations.
    """
    issues = []
    recommendations = []
    score = 2.5  # start at full score and deduct for violations

    soup = BeautifulSoup(html, "html.parser")

    # Heuristics to detect common intrusive elements
    intrusive_keywords = ['popup', 'modal', 'interstitial', 'overlay', 'subscribe', 'cookie-consent']
    intrusive_classes = '|'.join(intrusive_keywords)

    # Detect elements with known intrusive classes/ids
    intrusive_elements = soup.find_all(
        lambda tag: any(
            re.search(intrusive_classes, str(tag.get(attr)), re.IGNORECASE)
            for attr in ['id', 'class']
        )
    )

    # Check for fixed full-screen overlays (e.g., modals)
    full_screen_overlays = soup.find_all(
        lambda tag: tag.has_attr('style') and 'position:fixed' in tag['style'].lower() and
                    ('width:100%' in tag['style'].lower() or 'height:100%' in tag['style'].lower())
    )

    # Aggregate intrusive detections
    intrusive_detected = intrusive_elements + full_screen_overlays

    if intrusive_detected:
        score = 0.5
        issues.append("Detected intrusive elements such as modals, popups, or overlays.")
        recommendations.append("Remove or delay intrusive UI elements to avoid interrupting agents.")
    else:
        recommendations.append("No intrusive UI elements detected. ✅")

    return score, issues, recommendations