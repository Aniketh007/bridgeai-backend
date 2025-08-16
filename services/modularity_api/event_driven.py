# Pillar 3, Sub-pillar 4
# See Bridge.ipynb cell 24 for logic
# ...existing code...
import requests
import json
from urllib.parse import urlparse, urljoin

# Helper to print colored and formatted text for better readability
def print_header(text):
    print("\n" + "="*80)
    print(f" {text}")
    print("="*80)

def print_subheader(text):
    print("\n" + "-"*80)
    print(f" {text}")
    print("-"*80)

def print_status(message, status):
    padded_message = f"{message:<60}"
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

class EventDrivenArchitectureAnalyzer:
    """
    Analyzes API specifications for support of event-driven architectures (Webhooks, AsyncAPI).
    Based on ARI v10.0 Pillar 3, Sub-pillar 4.
    """
    CONVENTIONAL_PATHS = ["/.well-known/openapi.json", "/openapi.json"]
    ASYNCAPI_PATH = "/.well-known/asyncapi.json"

    def __init__(self, target_url):
        if not target_url.startswith('http'):
            target_url = 'https://' + target_url
        parsed_url = urlparse(target_url)
        self.base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        self.report = {"findings": {}, "recommendations": [], "score": 0, "status": "Not Assessed"}
        self.openapi_spec = None

    def _get_json(self, url):
        try:
            res = requests.get(url, timeout=7)
            res.raise_for_status()
            return res.json()
        except (requests.exceptions.RequestException, json.JSONDecodeError):
            return None

    def _find_openapi_spec(self):
        """Finds the OpenAPI spec using standard discovery methods."""
        for path in self.CONVENTIONAL_PATHS:
            spec_data = self._get_json(urljoin(self.base_url, path))
            if spec_data:
                self.openapi_spec = spec_data
                return True
        return False

    def run_analysis(self):
        print_header("ARI Sub-Pillar 3.4: Event-Driven Architecture")
        self._analyze_openapi_for_webhooks()
        self._analyze_for_asyncapi()
        self._generate_final_report()
        self._print_final_report()

    def _analyze_openapi_for_webhooks(self):
        """Checks a discovered OpenAPI spec for a 'webhooks' object."""
        print_subheader("Checking OpenAPI Specification for Webhooks")
        if not self._find_openapi_spec():
            print_status("Could not discover an OpenAPI specification", "FAIL")
            self.report["findings"]["openapi_found"] = False
            return

        self.report["findings"]["openapi_found"] = True
        webhooks = self.openapi_spec.get("webhooks")
        if webhooks and isinstance(webhooks, dict):
            self.report["findings"]["has_webhooks"] = True
            # Check if any webhook is secured
            is_secure = False
            for event, path_item in webhooks.items():
                if "post" in path_item and "security" in path_item["post"]:
                    is_secure = True
                    break
            self.report["findings"]["webhooks_are_secure"] = is_secure
        else:
            self.report["findings"]["has_webhooks"] = False

    def _analyze_for_asyncapi(self):
        """Checks for a dedicated AsyncAPI specification."""
        print_subheader("Checking for AsyncAPI Specification")
        asyncapi_url = urljoin(self.base_url, self.ASYNCAPI_PATH)
        asyncapi_data = self._get_json(asyncapi_url)
        if asyncapi_data and "asyncapi" in asyncapi_data and "channels" in asyncapi_data:
            self.report["findings"]["has_asyncapi"] = True
        else:
            self.report["findings"]["has_asyncapi"] = False

    def _generate_final_report(self):
        score = 0
        f = self.report["findings"]

        if not f.get("openapi_found") and not f.get("has_asyncapi"):
            self.report["score"] = 0
            self.report["status"] = "CRITICAL"
            self.report["recommendations"].append("Publish an OpenAPI or AsyncAPI spec to define event-driven capabilities.")
            return

        if f.get("has_webhooks"):
            score = 75
            if f.get("webhooks_are_secure"):
                score += 15

        # AsyncAPI is the gold standard for this, so it gets max points.
        if f.get("has_asyncapi"):
            score = 100

        self.report["score"] = min(100, score)

        status_map = {95: "Excellent", 70: "Good", 25: "Needs Improvement", 0: "CRITICAL"}
        self.report["status"] = next((v for k, v in status_map.items() if self.report["score"] >= k), "CRITICAL")

        if not f.get("has_webhooks") and not f.get("has_asyncapi"):
            self.report["recommendations"].append("Implement webhook endpoints for key events to enable proactive communication.")
        if f.get("has_webhooks") and not f.get("webhooks_are_secure"):
            self.report["recommendations"].append("Provide webhook signature verification to ensure security and data integrity.")
        if self.report["score"] < 100:
            self.report["recommendations"].append("For advanced use cases, consider publishing a dedicated AsyncAPI specification.")


    def _print_final_report(self):
        f = self.report["findings"]
        print_header("Final Assessment Report")
        print_status("Overall Status", self.report['status'])
        print_status("Event-Driven Score", f"{self.report['score']}/100")

        print_subheader("Analysis Results")
        print_status("OpenAPI spec defines a 'webhooks' object", "PASS" if f.get("has_webhooks") else "FAIL")
        if f.get("has_webhooks"):
            print_status("Webhooks include security definitions", "PASS" if f.get("webhooks_are_secure") else "WARN")

        print_status("Dedicated AsyncAPI spec found and valid", "PASS" if f.get("has_asyncapi") else "FAIL")

        if self.report["recommendations"]:
            print_subheader("Recommendations")
            for rec in sorted(list(set(self.report["recommendations"]))):
                print_recommendation(rec)
