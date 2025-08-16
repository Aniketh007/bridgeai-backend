# Pillar 3, Sub-pillar 3
# See Bridge.ipynb cell 23 for logic
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

class ApiDocumentationAnalyzer:
    """
    Analyzes the completeness of in-spec documentation within an OpenAPI file.
    Based on ARI v10.0 Pillar 3, Sub-pillar 3.
    """
    CONVENTIONAL_PATHS = ["/.well-known/openapi.json", "/openapi.json", "/api/docs.json", "/api.json"]

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
        # This is a simplified version of the logic from sub-pillar 3.1
        agents_url = urljoin(self.base_url, "/.well-known/agents.json")
        agents_data = self._get_json(agents_url)
        if agents_data and agents_data.get("api_spec_url"):
            self.openapi_spec = self._get_json(urljoin(self.base_url, agents_data["api_spec_url"]))
            return
        for path in self.CONVENTIONAL_PATHS:
            spec_data = self._get_json(urljoin(self.base_url, path))
            if spec_data:
                self.openapi_spec = spec_data
                return

    def _analyze_documentation_coverage(self):
        """Calculates the percentage of endpoints that have good documentation."""
        paths = self.openapi_spec.get("paths", {})
        if not paths:
            return

        total_endpoints = 0
        desc_covered = 0
        params_covered = 0
        responses_covered = 0
        examples_covered = 0

        for path, methods in paths.items():
            for method, details in methods.items():
                total_endpoints += 1

                # Operation description
                if details.get("description") and len(details.get("description", "")) > 10:
                    desc_covered += 1

                # Parameter description
                if all(p.get("description") for p in details.get("parameters", [])):
                    params_covered +=1

                # Response description and examples
                responses = details.get("responses", {})
                if responses and all(r.get("description") for r in responses.values()):
                    responses_covered += 1
                # Check for example in success response
                success_response = responses.get("200", {}) or responses.get("201", {})
                if success_response.get("content", {}).get("application/json", {}).get("example"):
                    examples_covered += 1

        if total_endpoints > 0:
            self.report["findings"] = {
                "total_endpoints": total_endpoints,
                "description_coverage": (desc_covered / total_endpoints) * 100,
                "parameter_coverage": (params_covered / total_endpoints) * 100,
                "response_coverage": (responses_covered / total_endpoints) * 100,
                "example_coverage": (examples_covered / total_endpoints) * 100,
            }

    def run_analysis(self):
        print_header("ARI Sub-Pillar 3.3: Comprehensive In-Spec Documentation")
        self._find_openapi_spec()
        if self.openapi_spec:
            print_status("OpenAPI Specification Found", "PASS")
            self._analyze_documentation_coverage()
        else:
            print_status("OpenAPI Specification Found", "FAIL")

        self._generate_final_report()
        self._print_final_report()

    def _generate_final_report(self):
        if not self.openapi_spec:
            self.report["score"] = 0
            self.report["status"] = "CRITICAL"
            self.report["recommendations"].append("An OpenAPI specification is required to document API functionality.")
            return

        f = self.report["findings"]
        if not f:
             self.report["score"] = 0; self.report["status"] = "CRITICAL"; return

        # Weighted average of coverage scores
        score = (f.get("description_coverage", 0) * 0.30 +
                 f.get("parameter_coverage", 0) * 0.15 +
                 f.get("response_coverage", 0) * 0.35 + # Response descriptions are critical
                 f.get("example_coverage", 0) * 0.20)
        self.report["score"] = int(score)

        status_map = {90: "Excellent", 75: "Good", 50: "Needs Improvement", 0: "CRITICAL"}
        self.report["status"] = next((v for k, v in status_map.items() if self.report["score"] >= k), "CRITICAL")

        if f.get("description_coverage", 100) < 80:
             self.report["recommendations"].append("Add detailed descriptions to all OpenAPI operations.")
        if f.get("response_coverage", 100) < 90:
             self.report["recommendations"].append("Document all possible response codes, including errors, and their meanings.")
        if f.get("example_coverage", 100) < 50:
             self.report["recommendations"].append("Include request/response examples for each endpoint.")


    def _print_final_report(self):
        print_header("Final Assessment Report")
        print_status("Overall Status", self.report['status'])
        print_status("Documentation Score", f"{self.report['score']}/100")

        f = self.report.get("findings", {})
        if f:
            print_subheader("Documentation Coverage Analysis")
            print_status("Total endpoints analyzed", f.get('total_endpoints', 0))
            print_status("Operation Description Coverage", f"{f.get('description_coverage', 0):.1f}%")
            print_status("Parameter Description Coverage", f"{f.get('parameter_coverage', 0):.1f}%")
            print_status("Response Documentation Coverage", f"{f.get('response_coverage', 0):.1f}%")
            print_status("Request/Response Example Coverage", f"{f.get('example_coverage', 0):.1f}%")

        if self.report["recommendations"]:
            print_subheader("Recommendations")
            for rec in sorted(list(set(self.report["recommendations"]))):
                print_recommendation(rec)
