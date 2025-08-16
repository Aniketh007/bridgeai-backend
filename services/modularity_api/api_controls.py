# Pillar 3, Sub-pillar 8
# See Bridge.ipynb cell 28 for logic
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

class ApiControlsAnalyzer:
    """
    Analyzes an OpenAPI spec for pagination, filtering, and sorting controls.
    Based on ARI v10.0 Pillar 3, Sub-pillar 8.
    """
    CONVENTIONAL_PATHS = ["/.well-known/openapi.json", "/openapi.json", "/api/docs.json", "/api.json"]
    PAGINATION_KEYS = {'cursor', 'after', 'next_token', 'limit', 'page_size', 'offset', 'page'}
    SORTING_KEYS = {'sort', 'sort_by', 'order', 'order_by'}

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
        print_header("ARI Sub-Pillar 3.8: Pagination, Filtering & Sorting Controls")
        if self._find_openapi_spec():
            print_status("OpenAPI Specification Found", "PASS")
            self._analyze_controls()
        else:
            print_status("OpenAPI Specification Found", "FAIL")

        self._generate_final_report()
        self._print_final_report()

    def _analyze_controls(self):
        """Analyzes GET operations on collections for control parameters."""
        paths = self.openapi_spec.get("paths", {})
        collection_endpoints = 0
        pagination_supported = 0
        filtering_supported = 0
        sorting_supported = 0

        for path, methods in paths.items():
            # Heuristic: A collection endpoint doesn't end with a path parameter like /{id}
            if 'get' in methods and not path.endswith('}'):
                collection_endpoints += 1
                op_details = methods['get']
                params = op_details.get("parameters", [])
                param_names = {p.get("name") for p in params if p.get("in") == "query"}

                # Check for pagination
                if self.PAGINATION_KEYS.intersection(param_names):
                    pagination_supported += 1

                # Check for sorting
                if self.SORTING_KEYS.intersection(param_names):
                    sorting_supported += 1

                # Check for filtering (heuristic: any other optional query params)
                filter_params = param_names - self.PAGINATION_KEYS - self.SORTING_KEYS
                if filter_params:
                    filtering_supported += 1

        self.report["findings"] = {
            "collection_endpoints": collection_endpoints,
            "pagination_coverage": (pagination_supported / collection_endpoints) * 100 if collection_endpoints > 0 else 0,
            "filtering_coverage": (filtering_supported / collection_endpoints) * 100 if collection_endpoints > 0 else 0,
            "sorting_coverage": (sorting_supported / collection_endpoints) * 100 if collection_endpoints > 0 else 0
        }

    def _generate_final_report(self):
        if not self.openapi_spec:
            self.report["score"] = 0; self.report["status"] = "Not Assessed"; return

        f = self.report.get("findings", {})
        if not f or f.get("collection_endpoints", 0) == 0:
            self.report["score"] = 100; self.report["status"] = "Not Applicable"; return # No collections, no penalty

        # Weighted average of coverage scores
        score = (f.get("pagination_coverage", 0) * 0.50 +
                 f.get("filtering_coverage", 0) * 0.30 +
                 f.get("sorting_coverage", 0) * 0.20)
        self.report["score"] = int(score)

        status_map = {95: "Excellent", 80: "Good", 50: "Needs Improvement", 0: "Poor"}
        self.report["status"] = next((v for k, v in status_map.items() if self.report["score"] >= k), "Poor")

        if f.get("pagination_coverage", 100) < 100:
            self.report["recommendations"].append("Implement pagination controls (e.g., cursor, limit/offset) on all list endpoints.")
        if f.get("filtering_coverage", 100) < 50:
             self.report["recommendations"].append("Provide query parameters for server-side filtering of results.")
        if f.get("sorting_coverage", 100) < 50:
             self.report["recommendations"].append("Provide `sort` or `order_by` parameters for controlling result order.")

    def _print_final_report(self):
        f = self.report.get("findings", {})
        print_header("Final Assessment Report")
        print_status("Overall Status", self.report['status'])
        print_status("Data Controls Score", f"{self.report['score']}/100")

        if f and f.get("collection_endpoints", 0) > 0:
            print_subheader("Control Coverage Across Collection Endpoints")
            print_status("Collection (list) endpoints found", f.get('collection_endpoints', 0))
            print_status("Pagination Controls Coverage", f"{f.get('pagination_coverage', 0):.1f}%")
            print_status("Filtering Controls Coverage", f"{f.get('filtering_coverage', 0):.1f}%")
            print_status("Sorting Controls Coverage", f"{f.get('sorting_coverage', 0):.1f}%")
        else:
            print_subheader("No collection endpoints found to analyze.")

        if self.report["recommendations"]:
            print_subheader("Recommendations")
            for rec in sorted(list(set(self.report["recommendations"]))):
                print_recommendation(rec)
