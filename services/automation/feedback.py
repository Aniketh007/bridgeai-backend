from typing import Tuple, List
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

# ---------- Action Feedback Check ----------

def check_clear_action_feedback(url: str, html: str) -> Tuple[int, List[str], List[str]]:
    score = 0
    issues = []
    recommendations = []

    try:
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        time.sleep(4)

        html = driver.page_source.lower()

        feedback_keywords = [
            "success", "error", "submitted", "invalid", "failed",
            "required", "added to cart", "welcome", "try again"
        ]

        aria_feedback = [
            '[role="alert"]', '[role="status"]', '[aria-live]'
        ]

        found_feedback = any(k in html for k in feedback_keywords)

        if found_feedback:
            score += 7
        else:
            issues.append("No visible success/error feedback detected.")
            recommendations.append("Show meaningful confirmation/error messages after actions.")

        # Check ARIA-based alerts
        for selector in aria_feedback:
            try:
                el = driver.find_element(By.CSS_SELECTOR, selector)
                if el and el.text.strip():
                    score += 3
                    break
            except:
                continue

        if score < 10:
            recommendations.append("Use ARIA roles or aria-live for screen-reader/agent-readable feedback.")

        driver.quit()
        return min(score, 10), issues, recommendations

    except Exception as e:
        issues.append("Action feedback check failed.")
        recommendations.append(str(e))
        return 0, issues, recommendations