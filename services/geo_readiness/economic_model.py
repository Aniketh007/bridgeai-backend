# Pillar 1, Sub-pillar 8
# See Bridge.ipynb cell 8 for logic
# ...existing code...
import requests
import json
from urllib.parse import urlparse, urljoin

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
        status_str = f"[\033[92m{status}\033[0m]" # Green
    else:
        status_str = f"[{status}]"
    print(f"{padded_message} {status_str}")

def print_recommendation(rec):
    print(f"  - {rec}")

class EconomicModelAnalyzer:
    """
    Analyzes for programmatic cost declarations by following the agents.json -> OpenAPI spec chain.
    Based on ARI v10.0 Pillar 1, Sub-pillar 8.
    """
    AGENTS_JSON_PATH = "/.well-known/agents.json"

    def __init__(self, target_url):
        if not target_url.startswith('http'):
            target_url = 'https://' + target_url
        self.base_url = f"{urlparse(target_url).scheme}://{urlparse(target_url).netloc}"
        self.report = {
            "findings": {}, "recommendations": [], "score": 0, "status": "Not Assessed"
        }
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'ARI-EconomicModel-Analyzer/1.0'})

    def _get_json_from_url(self, url):
        """Fetches and parses JSON content from a URL."""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            self.report["findings"]["error"] = f"Could not fetch or parse JSON from {url}: {e}"
            return None

    def find_and_analyze(self):
        """Follows the discovery chain from agents.json to OpenAPI cost extensions."""
        # Step 1: Find agents.json
        agents_json_url = urljoin(self.base_url, self.AGENTS_JSON_PATH)
        print_status(f"Searching for manifest at {agents_json_url}", "IN PROGRESS")
        agents_data = self._get_json_from_url(agents_json_url)
        if not agents_data:
            self.report["findings"]["agents_json_found"] = False
            print_status("agents.json manifest not found or invalid", "CRITICAL")
            return
        self.report["findings"]["agents_json_found"] = True
        print_status("Found agents.json manifest", "PASS")

        # Step 2: Get the OpenAPI spec URL
        api_spec_url = agents_data.get("api_spec_url")
        if not api_spec_url:
            self.report["findings"]["api_spec_url_found"] = False
            print_status("api_spec_url not found within agents.json", "CRITICAL")
            return
        self.report["findings"]["api_spec_url_found"] = True
        print_status(f"Found api_spec_url: {api_spec_url}", "PASS")

        # Step 3: Fetch the OpenAPI spec and analyze it
        print_status("Fetching OpenAPI specification", "IN PROGRESS")
        openapi_data = self._get_json_from_url(api_spec_url)
        if not openapi_data:
            self.report["findings"]["openapi_spec_found"] = False
            print_status("Could not fetch or parse OpenAPI spec", "FAIL")
            return
        self.report["findings"]["openapi_spec_found"] = True
        print_status("Successfully fetched OpenAPI specification", "PASS")

        # Step 4: Look for 'x-cost' extensions
        self.report["findings"]["has_cost_extension"] = False
        self.report["findings"]["has_structured_cost"] = False
        for path, methods in openapi_data.get("paths", {}).items():
            for method, details in methods.items():
                if "x-cost" in details:
                    self.report["findings"]["has_cost_extension"] = True
                    cost_data = details["x-cost"]
                    if isinstance(cost_data, dict) and "model" in cost_data and "amount" in cost_data:
                        self.report["findings"]["has_structured_cost"] = True
                        # Found a great example, no need to keep searching
                        return

    def run_analysis(self):
        print_header("ARI Sub-Pillar 1.8: Economic Model & Cost Declaration")
        self.find_and_analyze()
        self._generate_final_report()
        self._print_final_report()

    def _generate_final_report(self):
        score = 0
        if self.report["findings"].get("agents_json_found") and self.report["findings"].get("api_spec_url_found") and self.report["findings"].get("openapi_spec_found"):
            score = 25 # Found the spec, but no cost info yet
            if self.report["findings"].get("has_cost_extension"):
                score = 75 # Found at least one cost extension
            if self.report["findings"].get("has_structured_cost"):
                score = 100 # Found a well-structured cost extension

        self.report["score"] = score

        if score >= 90: self.report["status"] = "Excellent"
        elif score >= 70: self.report["status"] = "Good"
        elif score >= 25: self.report["status"] = "Needs Improvement"
        else: self.report["status"] = "Not Ready"

        # Recommendations
        if score == 0:
            self.report["recommendations"].append("Implement agents.json with a valid 'api_spec_url' as a prerequisite for declaring costs.")
        if 25 <= score < 100:
            self.report["recommendations"].append("Add 'x-cost' objects to your OpenAPI specification endpoints to programmatically declare usage fees.")
        if 75 <= score < 100:
            self.report["recommendations"].append("Structure your 'x-cost' objects with fields like 'model', 'amount', and 'currency' for clarity.")

    def _print_final_report(self):
        print_header("Final Assessment Report")
        print_status("Overall Status", self.report['status'])
        print_status("ARI Score (out of 100)", self.report['score'])

        print_subheader("Findings Checklist")
        print_status("Found agents.json manifest", "PASS" if self.report["findings"].get("agents_json_found") else "FAIL")
        if self.report["findings"].get("agents_json_found"):
            print_status("Found 'api_spec_url' in manifest", "PASS" if self.report["findings"].get("api_spec_url_found") else "FAIL")
        if self.report["findings"].get("api_spec_url_found"):
            print_status("Fetched and parsed OpenAPI specification", "PASS" if self.report["findings"].get("openapi_spec_found") else "FAIL")
        if self.report["findings"].get("openapi_spec_found"):
            print_status("Found 'x-cost' extension in any endpoint", "PASS" if self.report["findings"].get("has_cost_extension") else "FAIL")
            print_status("Found well-structured 'x-cost' object", "PASS" if self.report["findings"].get("has_structured_cost") else "WARN")

        if self.report["recommendations"]:
            print_subheader("Recommendations")
            for rec in self.report["recommendations"]:
                print_recommendation(rec)

