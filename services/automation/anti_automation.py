import requests
from typing import Tuple, List

# ---------- Anti-Automation Absence Check ----------

def check_anti_automation_absence(url: str, html: str) -> Tuple[int, List[str], List[str]]:
    score = 0
    issues = []
    recommendations = []

    try:
        # 1. Check for bot-blocking headers
        response = requests.get(url, timeout=10)
        headers = response.headers

        if "x-robots-tag" not in headers or "noindex" not in headers.get("x-robots-tag", "").lower():
            score += 1
        else:
            issues.append("Site blocks bots via X-Robots-Tag header.")
            recommendations.append("Remove aggressive noindex/nofollow unless essential.")

        # 2. Check for CAPTCHAs on homepage
        if "captcha" in response.text.lower():
            issues.append("Potential CAPTCHA challenge found on homepage.")
            recommendations.append("Use CAPTCHAs only on sensitive actions like signups or payments.")
        else:
            score += 2

        # 3. robots.txt check
        parsed = requests.utils.urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        try:
            r_txt = requests.get(robots_url, timeout=5)
            if "disallow: /" not in r_txt.text.lower():
                score += 1
            else:
                issues.append("robots.txt blocks general crawling.")
                recommendations.append("Update robots.txt to allow general crawling.")
        except:
            issues.append("robots.txt not found or unreachable.")
            recommendations.append("Ensure robots.txt is accessible and well-configured.")

        # 4. Check for fingerprinting scripts (basic heuristic)
        if any(s in response.text.lower() for s in ["fingerprintjs", "navigator.plugins", "navigator.hardwareconcurrency"]):
            issues.append("Potential fingerprinting scripts detected.")
            recommendations.append("Avoid aggressive fingerprinting that blocks automation.")
        else:
            score += 1

        return min(score, 5), issues, recommendations

    except Exception as e:
        issues.append("Anti-automation check failed.")
        recommendations.append(str(e))
        return 0, issues, recommendations