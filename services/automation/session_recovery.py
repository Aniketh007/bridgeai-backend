import requests
from typing import Tuple, List
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

# ---------- Session State Recovery Check ----------

def check_session_state_recovery(url: str, html: str) -> Tuple[int, List[str], List[str]]:
    score = 0
    issues = []
    recommendations = []

    try:
        # 1. Check for session cookie
        session = requests.Session()
        resp = session.get(url, timeout=10)
        cookies = session.cookies.get_dict()
        if cookies:
            score += 2
        else:
            issues.append("No session cookies detected.")
            recommendations.append("Use session cookies to persist user state.")

        # 2. Use Selenium to detect state persistence visually
        driver = webdriver.Chrome(options=Options().add_argument("--headless"))
        driver.get(url)
        time.sleep(3)
        html_before = driver.page_source

        driver.refresh()
        time.sleep(3)
        html_after = driver.page_source

        if html_before == html_after:
            score += 3
        else:
            issues.append("Content structure changes after reload.")
            recommendations.append("Ensure session-specific content survives page reload.")

        # 3. Check for minimal state in URL
        if "?" in url or "=" in url:
            score += 2
        else:
            issues.append("No user state encoded in URL.")
            recommendations.append("Use minimal query params to allow state preservation.")

        # 4. Bonus: Check for UI components like cart/login/continue
        if any(keyword in html_after.lower() for keyword in ["continue", "resume", "cart", "saved", "back to"]):
            score += 3
        else:
            recommendations.append("Include visual cues for returning users (e.g., Resume, Cart, Saved).")

        driver.quit()
        return min(score, 10), issues, recommendations

    except Exception as e:
        issues.append("Session & state evaluation failed.")
        recommendations.append(f"Error: {str(e)}")
        return 0, issues, recommendations