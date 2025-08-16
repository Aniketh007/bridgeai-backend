import requests
from typing import Tuple, List
from bs4 import BeautifulSoup

# ---------- MFA Handling Check ----------

def check_mfa_handling(url: str, html: str) -> Tuple[int, List[str], List[str]]:
    score = 0
    issues = []
    recommendations = []

    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        mfa_keywords = ['otp', '2fa', 'verification', 'authenticator', 'mfa', 'security code']

        input_tags = soup.find_all("input")
        found_mfa = any(any(k in (i.get("name", "") + i.get("id", "") + i.get("type", "")).lower() for k in mfa_keywords) for i in input_tags)

        if found_mfa:
            score += 1
        else:
            recommendations.append("Add HTML cues or labels for MFA inputs if applicable.")

        if "remember me" in res.text.lower() or "remember this device" in res.text.lower():
            score += 1
        else:
            recommendations.append("Support 'remember this device' or fallback for agents.")

        if "login" in url or "signin" in url:
            if found_mfa:
                score += 2
        else:
            score += 1  # not a protected route — good

        return min(score, 5), issues, recommendations

    except Exception as e:
        issues.append("MFA check failed.")
        recommendations.append(str(e))
        return 0, issues, recommendations