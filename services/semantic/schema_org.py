from typing import Tuple, List
import json
from bs4 import BeautifulSoup

def check_schema_org_depth(url: str, html: str) -> Tuple[int, List[str], List[str]]:
    issues, recommendations = [], []
    score = 0

    try:
        soup = BeautifulSoup(html, "html.parser")
        scripts = soup.find_all("script", type="application/ld+json")

        jsonld_data = []
        for tag in scripts:
            try:
                parsed = json.loads(tag.string)
                if isinstance(parsed, list):
                    jsonld_data.extend(parsed)
                else:
                    jsonld_data.append(parsed)
            except Exception:
                continue

        if not jsonld_data:
            issues.append("No JSON-LD structured data found.")
            recommendations.append("Add schema.org JSON-LD to your pages.")
            return 0, issues, recommendations

        score += 5  # ✅ JSON-LD present

        found_types = set()
        nested_count = 0

        def traverse(entity, depth=1):
            nonlocal nested_count
            if isinstance(entity, dict):
                if "@type" in entity:
                    found_types.add(entity["@type"] if isinstance(entity["@type"], str) else tuple(entity["@type"]))
                for val in entity.values():
                    if isinstance(val, dict) and "@type" in val:
                        nested_count += 1
                        traverse(val, depth + 1)
                    elif isinstance(val, list):
                        for v in val:
                            if isinstance(v, dict) and "@type" in v:
                                nested_count += 1
                                traverse(v, depth + 1)

        for item in jsonld_data:
            traverse(item)

        # 🎯 Scoring based on entity richness
        if "Product" in found_types:
            score += 4
        else:
            recommendations.append("Add Product schema for relevant pages.")

        if "Offer" in found_types or "Review" in found_types:
            score += 4
        else:
            recommendations.append("Nest Offer or Review under Product.")

        if "Article" in found_types:
            score += 3
        else:
            recommendations.append("Use Article schema.")

        if "Organization" in found_types or "Person" in found_types:
            score += 3
        else:
            recommendations.append("Include Organization or Person schema.")

        if nested_count >= 3:
            score += 4
        else:
            recommendations.append("Improve nesting (e.g., Product → Offer → Review).")

        if score < 25:
            issues.append("Structured data is present but lacks full depth or coverage.")

        return min(score, 25), issues, recommendations

    except Exception as e:
        issues.append("Schema extraction failed.")
        try:
            error_message = f"{e.__class__.__name__}: {str(e)}"
            print("⚠️ ERROR STRING:", error_message)
            recommendations.append(error_message)
        except Exception as ee:
            recommendations.append("Error could not be stringified")
            print("⚠️ Nested Error:", repr(ee))

        return 0, issues, recommendations
