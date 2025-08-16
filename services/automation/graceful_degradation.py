from typing import Tuple, List
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

# ---------- Graceful Degradation Check ----------

def check_graceful_degradation(url: str, html: str) -> Tuple[int, List[str], List[str]]:
    score = 0
    issues = []
    recommendations = []

    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-javascript")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")

        driver = webdriver.Chrome(options=options)
        driver.get(url)
        time.sleep(4)

        # 1. Content visibility
        body_text = driver.find_element(By.TAG_NAME, "body").text.strip()
        if body_text:
            score += 1
        else:
            issues.append("Page appears blank without JavaScript.")
            recommendations.append("Ensure meaningful fallback content without JS.")

        # 2. Forms fallback check
        forms = driver.find_elements(By.TAG_NAME, "form")
        if forms:
            score += 2
        else:
            issues.append("No forms found or forms rely entirely on JS.")
            recommendations.append("Ensure forms can POST even with JS disabled.")

        # 3. Link navigation
        links = driver.find_elements(By.TAG_NAME, "a")
        if links:
            score += 1
        else:
            issues.append("No anchor tags available for navigation.")
            recommendations.append("Use basic anchor tags as fallback navigation.")

        # 4. JS-free CTA/buttons
        buttons = driver.find_elements(By.TAG_NAME, "button")
        if buttons:
            score += 1
        else:
            recommendations.append("Provide non-JS alternatives for call-to-action buttons.")

        driver.quit()
        return min(score, 5), issues, recommendations

    except Exception as e:
        issues.append("Degradation check failed.")
        recommendations.append(str(e))
        return 0, issues, recommendations