# Pillar 1, Sub-pillar 9
# See Bridge.ipynb cell 9 for logic
# ...existing code...
import requests
import json
from urllib.parse import urlparse
from bs4 import BeautifulSoup

# Helper to print colored and formatted text for better readability
def print_header(text):
    print("\n" + "="*70)
    print(f" {text}")
    print("="*70)

def print_subheader(text):
    print("\n" + "-"*70)
    print(f" {text}")
    print("-"*70)

def print_status(message, status):
    padded_message = f"{message:<55}"
    if status == "FAIL" or status == "CRITICAL":
        status_str = f"[\033[91m{status}\033[0m]" # Red
    elif status == "WARN":
        status_str = f"[\033[93m{status}\033[0m]" # Yellow
    elif status == "PASS" or status == "INFO":
        status_str = f"[\033[92m{status}\03g[0m]" # Green
    else:
        status_str = f"[{status}]"

    print(f"{padded_message} {status_str}")

def print_recommendation(rec):
    print(f"  - {rec}")

class DataLicensingAnalyzer:
    """
    Analyzes a page for machine-readable data licensing and provenance information.
    Based on ARI v10.0 Pillar 1, Sub-pillar 9.
    """
    def __init__(self, target_url):
        if not target_url.startswith('http'):
            target_url = 'https://' + target_url
        self.url = target_url
        self.report = {
            "findings": {}, "recommendations": [], "score": 0, "status": "Not Assessed"
        }
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'ARI-DataLicensing-Analyzer/1.0'})

    def _find_and_analyze_schema(self, soup):
        """Finds ld+json schema and analyzes it for licensing information."""
        scripts = soup.find_all('script', type='application/ld+json')
        if not scripts:
            self.report["findings"]["has_ld_json"] = False
            return
        self.report["findings"]["has_ld_json"] = True

        main_content_schema = None
        for script in scripts:
            try:
                data = json.loads(script.string)
                schemas = data if isinstance(data, list) else [data]
                # Prioritize more specific types first
                for schema_type in ['Article', 'BlogPosting', 'NewsArticle', 'WebPage', 'CreativeWork']:
                    for schema in schemas:
                        if schema.get('@type', '') == schema_type:
                            main_content_schema = schema
                            break
                    if main_content_schema: break
                if main_content_schema: break
            except (json.JSONDecodeError, TypeError):
                continue

        if not main_content_schema:
            self.report["findings"]["has_content_schema"] = False
            return
        self.report["findings"]["has_content_schema"] = True

        # Check for license property
        license_prop = main_content_schema.get('license') or main_content_schema.get('usageInfo')
        if not license_prop:
            self.report["findings"]["has_license_prop"] = False
            return
        self.report["findings"]["has_license_prop"] = True

        # Analyze the license value
        if isinstance(license_prop, str):
            parsed_license = urlparse(license_prop)
            if parsed_license.scheme and parsed_license.netloc:
                self.report["findings"]["license_type"] = "URL"
                if "creativecommons.org" in parsed_license.netloc:
                    self.report["findings"]["is_creative_commons"] = True
            else:
                self.report["findings"]["license_type"] = "Text"

    def run_analysis(self):
        print_header("ARI Sub-Pillar 1.9: Data Licensing & Provenance")
        try:
            response = self.session.get(self.url, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print_status(f"Failed to fetch URL: {e}", "CRITICAL")
            return

        print_subheader("Analyzing Schema.org ld+json for license declarations")
        soup = BeautifulSoup(response.text, 'lxml')
        self._find_and_analyze_schema(soup)
        self._generate_final_report()
        self._print_final_report()

    def _generate_final_report(self):
        score = 0
        if self.report["findings"].get("has_ld_json"): score = 10
        if self.report["findings"].get("has_content_schema"): score = 25
        if self.report["findings"].get("has_license_prop"):
            license_type = self.report["findings"].get("license_type")
            if license_type == "Text": score = 75
            if license_type == "URL":
                score = 90
                if self.report["findings"].get("is_creative_commons"):
                    score = 100

        self.report["score"] = score

        if score >= 95: self.report["status"] = "Excellent"
        elif score >= 75: self.report["status"] = "Good"
        elif score >= 25: self.report["status"] = "Needs Improvement"
        else: self.report["status"] = "Poor"

        # Recommendations
        if score < 25:
            self.report["recommendations"].append("Implement Schema.org ld+json data on your pages to declare metadata.")
        if 25 <= score < 100:
            self.report["recommendations"].append("Add a 'license' property to your main content schema (e.g., WebPage, Article).")
        if 75 <= score < 100:
            self.report["recommendations"].append("For maximum clarity, the 'license' property value should be a full URL pointing to the license deed (e.g., https://creativecommons.org/licenses/by/4.0/).")

    def _print_final_report(self):
        print_header("Final Assessment Report")
        print_status("Overall Status", self.report['status'])
        print_status("ARI Score (out of 100)", self.report['score'])

        print_subheader("Findings Checklist")
        if not self.report["findings"]:
            print("  - Could not analyze page.")
            return

        print_status("Found ld+json structured data on page", "PASS" if self.report["findings"].get("has_ld_json") else "FAIL")
        print_status("Found a main content schema (Article, WebPage, etc.)", "PASS" if self.report["findings"].get("has_content_schema") else "FAIL")
        print_status("Schema contains a 'license' or 'usageInfo' property", "PASS" if self.report["findings"].get("has_license_prop") else "FAIL")
        if self.report["findings"].get("has_license_prop"):
            license_type = self.report["findings"].get("license_type", "N/A")
            print_status(f"License is declared as a URL (best practice)", "PASS" if license_type == "URL" else "WARN")
            if license_type == "URL":
                print_status(f"License URL points to Creative Commons", "PASS" if self.report["findings"].get("is_creative_commons") else "INFO")

        if self.report["recommendations"]:
            print_subheader("Recommendations")
            for rec in self.report["recommendations"]:
                print_recommendation(rec)
