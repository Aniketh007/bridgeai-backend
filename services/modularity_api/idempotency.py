# Pillar 3, Sub-pillar 9
# See Bridge.ipynb cell 29 for logic
# ...existing code...
import requests
import json
import re
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
    if status == "FAIL" or status == "CRITICAL" or status == "BLOCKER":
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

class IdempotencyAnalyzer:
    """
    Analyzes an OpenAPI spec for correct HTTP method usage and idempotency patterns.
    Based on ARI v10.0 Pillar 3, Sub-pillar 9.
    """
    CONVENTIONAL_PATHS = ["/.well-known/openapi.json", "/openapi.json", "/api/docs.json", "/api.json"]
    IDEMPOTENCY_HEADERS = {'idempotency-key', 'x-request-id', 'x-idempotency-key'}

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
        print_header("ARI Sub-Pillar 3.9: Idempotency & Safe Method Usage")
        if self._find_openapi_spec():
            print_status("OpenAPI Specification Found", "PASS")
            self._analyze_methods()
        else:
            print_status("OpenAPI Specification Found", "FAIL")

        self._generate_final_report()
        self._print_final_report()

    def _analyze_methods(self):
        """Analyzes the usage patterns of HTTP verbs across all paths."""
        paths = self.openapi_spec.get("paths", {})
        findings = {
            "violations": [], "post_uses_idempotency_key": False,
            "total_gets": 0, "total_posts": 0, "total_puts": 0, "total_deletes": 0
        }

        for path, methods in paths.items():
            is_resource_path = bool(re.search(r'\{.*\}', path))

            for method, details in methods.items():
                method_upper = method.upper()

                if method_upper == "GET":
                    findings["total_gets"] += 1
                    if "requestBody" in details:
                        findings["violations"].append(f"Safety Violation: GET on '{path}' has a requestBody.")

                elif method_upper == "POST":
                    findings["total_posts"] += 1
                    params = details.get("parameters", [])
                    header_names = {p.get("name", "").lower() for p in params if p.get("in") == "header"}
                    if self.IDEMPOTENCY_HEADERS.intersection(header_names):
                        findings["post_uses_idempotency_key"] = True

                elif method_upper == "PUT":
                    findings["total_puts"] += 1
                    if not is_resource_path:
                        findings["violations"].append(f"Idempotency Warning: PUT used on collection path '{path}'.")

                elif method_upper == "DELETE":
                    findings["total_deletes"] += 1
                    if not is_resource_path:
                         findings["violations"].append(f"Idempotency Violation: DELETE used on collection path '{path}'.")

        self.report["findings"] = findings

    def _generate_final_report(self):
        if not self.openapi_spec:
            self.report["score"] = 0; self.report["status"] = "Not Assessed"; return

        f = self.report.get("findings", {})
        if not f:
            self.report["score"] = 0; self.report["status"] = "Poor"; return

        # Start with a perfect score and deduct for violations
        score = 100
        score -= len(f.get("violations", [])) * 25 # Each violation is a major issue

        # Add a bonus for the gold standard idempotency key
        if f.get("post_uses_idempotency_key"):
            score += 20

        self.report["score"] = max(0, min(100, int(score)))

        status_map = {95: "Excellent", 80: "Good", 50: "Needs Improvement", 0: "Poor"}
        self.report["status"] = next((v for k, v in status_map.items() if self.report["score"] >= k), "Poor")

        if f.get("violations"):
            self.report["recommendations"].append("Review HTTP verb usage: GET/HEAD must be safe, PUT/DELETE must be idempotent on resource paths.")
        if not f.get("post_uses_idempotency_key"):
             self.report["recommendations"].append("For critical POST operations, support an `Idempotency-Key` header to prevent duplicate actions.")

    def _print_final_report(self):
        f = self.report.get("findings", {})
        print_header("Final Assessment Report")
        print_status("Overall Status", self.report['status'])
        print_status("HTTP Method Usage Score", f"{self.report['score']}/100")

        if f:
            print_subheader("Analysis Details")
            print_status("Found and analyzed HTTP Verbs", f"{f.get('total_gets', 0)} GETs, {f.get('total_posts', 0)} POSTs, {f.get('total_puts', 0)} PUTs, {f.get('total_deletes', 0)} DELETEs")
            print_status("POST operations support an Idempotency-Key Header", "PASS" if f.get("post_uses_idempotency_key") else "WARN")

            if f.get("violations"):
                print_status("Detected HTTP Method Usage Violations", f"{len(f['violations'])} found")
                for v in f["violations"][:3]: # Show first 3
                    print(f"  └─ {v}")
            else:
                 print_status("Detected HTTP Method Usage Violations", "None")

        if self.report["recommendations"]:
            print_subheader("Recommendations")
            for rec in sorted(list(set(self.report["recommendations"]))):
                print_recommendation(rec)
