from typing import Tuple, List
from bs4 import BeautifulSoup

# ---------- CAPTCHA Presence Check ----------

def check_captcha_presence(url: str, html: str) -> Tuple[int, List[str], List[str]]:
    score = 30
    issues = []
    recommendations = []

    try:
        soup = BeautifulSoup(html, "html.parser")

        captcha_signatures = [
            'g-recaptcha',
            'h-captcha',
            'cf-challenge',
            'cf-captcha-container',
            'Please verify you are a human',
            'captcha',
            'are you a robot'
        ]

        html_lower = html.lower()
        found = False

        for sig in captcha_signatures:
            if sig.lower() in html_lower:
                found = True
                break

        if found:
            score = 0
            issues.append("CAPTCHA or bot-blocker detected.")
            recommendations.append("Consider removing CAPTCHA for agent flows or use alternate bot-friendly authentication.")
        else:
            recommendations.append("No CAPTCHA detected — agent flow looks clean.")

    except Exception as e:
        issues.append("CAPTCHA scan failed.")
        recommendations.append(f"Error: {str(e)}")
        score = 0

    return score, issues, recommendations