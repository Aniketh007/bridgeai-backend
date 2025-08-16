# Pillar 1, Sub-pillar 5
# See Bridge.ipynb cell 5 for logic
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

class AgentsJsonAnalyzer:
    """
    Analyzes a website for an Agent Capabilities & Tooling Manifest (agents.json)
    based on ARI v10.0 Pillar 1, Sub-pillar 5.
    """
    MANIFEST_PATH = "/.well-known/agents.json"

    def __init__(self, base_url):
        self.base_url = self._normalize_url(base_url)
        self.domain = urlparse(self.base_url).netloc
        self.report = {
            "findings": {}, "recommendations": [], "score": 0, "status": "Not Assessed"
        }
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'ARI-AgentsJson-Analyzer/1.0'})

    def _normalize_url(self, url):
        parsed = urlparse(url)
        if not parsed.scheme:
            url = "https://" + url
        return f"{urlparse(url).scheme}://{urlparse(url).netloc}"

    def find_and_analyze_manifest(self):
        """
        Looks for agents.json in the standardized /.well-known/ path and analyzes it.
        """
        print_subheader(f"Checking for manifest at the standard location: {self.MANIFEST_PATH}")

        # Check both www and non-www versions of the domain
        hosts_to_check = {self.domain}
        if self.domain.startswith('www.'):
            hosts_to_check.add(self.domain[4:])
        else:
            hosts_to_check.add('www.' + self.domain)

        found_url = None
        for host in sorted(list(hosts_to_check)):
            url_to_check = f"https://{host}{self.MANIFEST_PATH}"
            print_status(f"Attempting to fetch {url_to_check}", "IN PROGRESS")
            try:
                response = self.session.get(url_to_check, timeout=7)
                if response.status_code == 200:
                    print_status(f"SUCCESS: Found manifest file at {url_to_check}", "PASS")
                    self.report["findings"]["presence"] = True
                    self.report["findings"]["location"] = url_to_check
                    self._analyze_content(response.text)
                    return
            except requests.exceptions.RequestException:
                print_status(f"Failed to connect to {url_to_check}", "FAIL")
                continue

        print_status("Manifest file not found in standard location", "CRITICAL")
        self.report["findings"]["presence"] = False

    def _analyze_content(self, content):
        """Validates the content of the agents.json file against spec requirements."""
        try:
            data = json.loads(content)
            if not isinstance(data, dict) or not data:
                self.report["findings"]["is_valid_json"] = True
                self.report["findings"]["is_empty"] = True
                return

            self.report["findings"]["is_valid_json"] = True
            self.report["findings"]["is_empty"] = False

            # --- Perform validation checks ---
            self.report["findings"]["has_schema_version"] = "schema_version" in data
            self.report["findings"]["has_api_spec_url"] = "api_spec_url" in data and isinstance(urlparse(data["api_spec_url"]), urlparse) and urlparse(data["api_spec_url"]).scheme != ""
            self.report["findings"]["has_display_name"] = "display_name" in data
            self.report["findings"]["has_description"] = "description" in data
            self.report["findings"]["has_oauth_url"] = "oauth_url" in data
            self.report["findings"]["has_task_examples"] = "task_examples" in data and isinstance(data["task_examples"], list)

        except json.JSONDecodeError:
            self.report["findings"]["is_valid_json"] = False

    def run_analysis(self):
        print_header("ARI Sub-Pillar 1.5: Agent Capabilities & Tooling Manifest")
        self.find_and_analyze_manifest()
        self._generate_final_report()
        self._print_final_report()

    def _generate_final_report(self):
        if not self.report["findings"].get("presence"):
            self.report["status"] = "Not Ready"
            self.report["score"] = 0
            self.report["recommendations"].append(f"Create a manifest file at the standard location: {self.MANIFEST_PATH}")
            self.report["recommendations"].append("This file should declare the tools and capabilities you want to offer to AI agents.")
            return

        if not self.report["findings"].get("is_valid_json"):
            self.report["status"] = "Critical Failure"
            self.report["score"] = 10
            self.report["recommendations"].append("The agents.json file is not valid JSON. Correct the syntax errors.")
            return

        # Scoring based on maturity of the manifest
        score = 25 # Base for a valid, non-empty JSON
        if self.report["findings"]["has_schema_version"]: score += 15
        if self.report["findings"]["has_api_spec_url"]: score += 30 # Most important field
        if self.report["findings"]["has_display_name"] and self.report["findings"]["has_description"]: score += 15
        if self.report["findings"]["has_oauth_url"]: score += 10 # Sign of security readiness
        if self.report["findings"]["has_task_examples"]: score += 5  # Sign of developer experience
        self.report["score"] = min(score, 100)

        if self.report["score"] >= 90: self.report["status"] = "Future-Proof"
        elif self.report["score"] >= 70: self.report["status"] = "Good Progress"
        else: self.report["status"] = "Needs Improvement"

        if not self.report["findings"]["has_api_spec_url"]:
            self.report["recommendations"].append("CRITICAL: Add the 'api_spec_url' field pointing to an OpenAPI specification of your tools.")
        if not self.report["findings"]["has_oauth_url"]:
            self.report["recommendations"].append("Define authentication and rate-limiting information, preferably via an 'oauth_url'.")
        if not self.report["findings"]["has_task_examples"]:
            self.report["recommendations"].append("Define supported task types and workflows in 'task_examples' to improve agent usability.")

    def _print_final_report(self):
        print_header("Final Assessment Report")
        print_status("Overall Status", self.report['status'])
        print_status("ARI Score (out of 100)", self.report['score'])

        print_subheader("Findings Checklist")
        if not self.report["findings"].get("presence"):
            print("  - [FAIL] Manifest file not found.")
            return

        print_status("Manifest is valid JSON", "PASS" if self.report["findings"].get("is_valid_json") else "FAIL")
        if self.report["findings"].get("is_valid_json"):
            print_status("Contains 'schema_version'", "PASS" if self.report["findings"].get("has_schema_version") else "WARN")
            print_status("Contains valid 'api_spec_url' (most critical)", "PASS" if self.report["findings"].get("has_api_spec_url") else "FAIL")
            print_status("Contains 'display_name' and 'description'", "PASS" if self.report["findings"].get("has_display_name") else "INFO")
            print_status("Contains 'oauth_url' for authentication", "PASS" if self.report["findings"].get("has_oauth_url") else "INFO")
            print_status("Contains 'task_examples'", "PASS" if self.report["findings"].get("has_task_examples") else "INFO")

        if self.report["recommendations"]:
            print_subheader("Recommendations (Based on ARI v10.0)")
            for rec in self.report["recommendations"]:
                print_recommendation(rec)
