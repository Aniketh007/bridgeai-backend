from typing import Tuple, List
from bs4 import BeautifulSoup
# ---------- Form Predictability Check ----------

def check_form_predictability(url: str, html: str) -> Tuple[int, List[str], List[str]]:
    score = 0
    issues = []
    recommendations = []

    try:
        soup = BeautifulSoup(html, "html.parser")
        forms = soup.find_all("form")

        if not forms:
            issues.append("No form tags found on the page.")
            recommendations.append("Add <form> tags for user input instead of JavaScript-only forms.")
            return 0, issues, recommendations

        score += 3  # ✅ Form present

        total_inputs = 0
        inputs_with_names = 0
        inputs_with_labels = 0
        semantic_inputs = 0

        for form in forms:
            inputs = form.find_all("input")
            total_inputs += len(inputs)

            for input_tag in inputs:
                if input_tag.get("name"):
                    inputs_with_names += 1
                if input_tag.get("type") in ["email", "password", "number", "date", "search"]:
                    semantic_inputs += 1

        # Check for <label for=""> linking
        labels = soup.find_all("label")
        label_for_ids = {label.get("for") for label in labels if label.get("for")}

        for input_tag in soup.find_all("input"):
            if input_tag.get("id") and input_tag.get("id") in label_for_ids:
                inputs_with_labels += 1

        if total_inputs == 0:
            issues.append("No input elements found inside forms.")
            recommendations.append("Add input fields with proper attributes.")
            return 0, issues, recommendations

        if inputs_with_names / total_inputs >= 0.8:
            score += 4
        else:
            issues.append("Many inputs lack name attributes.")
            recommendations.append("Add unique name attributes to each input.")

        if inputs_with_labels / total_inputs >= 0.5:
            score += 3
        else:
            issues.append("Less than half of inputs are linked with <label>.")
            recommendations.append("Link input fields with <label for='...'> for better accessibility.")

        if semantic_inputs / total_inputs >= 0.3:
            score += 2
        else:
            recommendations.append("Use semantic input types like email, password, search, number.")

    except Exception as e:
        issues.append("Form predictability check failed.")
        recommendations.append(f"Error: {str(e)}")
        score = 0

    return min(score, 15), issues, recommendations