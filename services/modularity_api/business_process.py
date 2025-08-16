# Pillar 3, Sub-pillar 10
# See Bridge.ipynb cell 30 for logic
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

class BusinessProcessApiAnalyzer:
    """
    Analyzes an OpenAPI spec for high-level, business process-oriented endpoints.
    Based on ARI v10.0 Pillar 3, Sub-pillar 10.
    """
    CONVENTIONAL_PATHS = ["/.well-known/openapi.json", "/openapi.json", "/api/docs.json", "/api.json"]
    # Keywords indicating a business process or action
    ACTION_VERBS = [
        'approve', 'archive', 'cancel', 'capture', 'charge', 'complete', 'confirm',
        'create', 'decline', 'dispute', 'execute', 'finalize', 'generate', 'invoice',
        'issue', 'launch', 'pay', 'process', 'publish', 'refund', 'register', 'reject',
        'release', 'renew', 'report', 'resend', 'resume', 'return', 'reverse', 'revoke',
        'schedule', 'send', 'start', 'submit', 'subscribe', 'suspend', 'transfer', 'verify'
    ]

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
        print_header("ARI Sub-Pillar 3.10: Business Process as an API")
        if self._find_openapi_spec():
            print_status("OpenAPI Specification Found", "PASS")
            self._analyze_endpoints()
        else:
            print_status("OpenAPI Specification Found", "FAIL")

        self._generate_final_report()
        self._print_final_report()

    def _analyze_endpoints(self):
        """Analyzes all endpoints for signs of being a business process."""
        paths = self.openapi_spec.get("paths", {})
        total_endpoints = 0
        process_endpoints = 0
        examples = []

        for path, methods in paths.items():
            for method, details in methods.items():
                total_endpoints += 1
                is_process = False

                # Heuristic 1: Action verb in the path
                path_last_segment = path.strip('/').split('/')[-1]
                if path_last_segment in self.ACTION_VERBS:
                    is_process = True

                # Heuristic 2: Action verb in the summary or description
                summary = details.get("summary", "").lower()
                description = details.get("description", "").lower()
                operation_id = details.get("operationId", "").lower()

                for verb in self.ACTION_VERBS:
                    if verb in summary or verb in description or verb in operation_id:
                        is_process = True
                        break

                if is_process:
                    process_endpoints += 1
                    if len(examples) < 3:
                        examples.append(f"{method.upper()} {path}")

        self.report["findings"] = {
            "total_endpoints": total_endpoints,
            "process_endpoints_found": process_endpoints,
            "examples": examples
        }

    def _generate_final_report(self):
        if not self.openapi_spec:
            self.report["score"] = 0; self.report["status"] = "Not Assessed"; return

        f = self.report.get("findings", {})
        if not f or f.get("total_endpoints", 0) == 0:
            self.report["score"] = 0; self.report["status"] = "Poor"; return

        # Score is the percentage of endpoints that are business processes
        percentage = (f.get("process_endpoints_found", 0) / f.get("total_endpoints", 1)) * 100
        # Scale the score, as even a small percentage is good.
        # A site with 20% process-oriented endpoints is excellent.
        score = min(percentage * 5, 100)

        self.report["score"] = int(score)

        status_map = {90: "Excellent", 70: "Good", 40: "Needs Improvement", 0: "Poor"}
        self.report["status"] = next((v for k, v in status_map.items() if self.report["score"] >= k), "Poor")

        if self.report["score"] < 50:
            self.report["recommendations"].append("Expose high-level business processes as single API endpoints (e.g., /process-order).")
            self.report["recommendations"].append("Design endpoints that encapsulate complex, multi-step actions.")

    def _print_final_report(self):
        f = self.report.get("findings", {})
        print_header("Final Assessment Report")
        print_status("Overall Status", self.report['status'])
        print_status("Business Process Score", f"{self.report['score']}/100")

        if f:
            print_subheader("Analysis Details")
            total = f.get('total_endpoints', 0)
            found = f.get('process_endpoints_found', 0)
            percent = (found/total * 100) if total > 0 else 0

            print_status("Total endpoints analyzed", total)
            print_status("Endpoints identified as business processes", f"{found} ({percent:.1f}%)")

            if f.get("examples"):
                print("  └─ Examples found:")
                for ex in f["examples"]:
                    print(f"     - {ex}")

        if self.report["recommendations"]:
            print_subheader("Recommendations")
            for rec in sorted(list(set(self.report["recommendations"]))):
                print_recommendation(rec)
