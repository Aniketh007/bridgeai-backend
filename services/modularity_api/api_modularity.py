# Pillar 3, Sub-pillar 6
# See Bridge.ipynb cell 26 for logic
# ...existing code...
import requests
import json
import numpy as np
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

class ApiModularityAnalyzer:
    """
    Analyzes the modularity and granularity of an API via its OpenAPI specification.
    Based on ARI v10.0 Pillar 3, Sub-pillar 6.
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
        for path in self.CONVENTIONAL_PATHS:
            spec_data = self._get_json(urljoin(self.base_url, path))
            if spec_data:
                self.openapi_spec = spec_data
                return True
        return False

    def run_analysis(self):
        print_header("ARI Sub-Pillar 3.6: API Functional Modularity & Granularity")
        if self._find_openapi_spec():
            print_status("OpenAPI Specification Found", "PASS")
            self._analyze_modularity()
        else:
            print_status("OpenAPI Specification Found", "FAIL")

        self._generate_final_report()
        self._print_final_report()

    def _analyze_modularity(self):
        """Analyzes tags and path structure to assess modularity."""
        paths = self.openapi_spec.get("paths", {})
        if not paths: return

        # Tag Analysis
        tag_counts = {}
        tagged_endpoints = 0
        total_endpoints = 0
        top_level_resources = set()

        for path, methods in paths.items():
            # Resource Analysis
            resource = path.strip('/').split('/')[0]
            if resource: top_level_resources.add(resource)

            for method, details in methods.items():
                total_endpoints += 1
                tags = details.get("tags", ["untagged"])
                tagged_endpoints += 1 if "untagged" not in tags else 0
                for tag in tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

        self.report["findings"]["total_endpoints"] = total_endpoints
        self.report["findings"]["tag_coverage"] = (tagged_endpoints / total_endpoints) * 100 if total_endpoints > 0 else 0
        self.report["findings"]["unique_tags"] = len(tag_counts) if "untagged" not in tag_counts else len(tag_counts) -1
        self.report["findings"]["unique_resources"] = len(top_level_resources)

        if len(tag_counts) > 1:
            self.report["findings"]["endpoint_distribution_stddev"] = np.std(list(tag_counts.values()))
        else:
            self.report["findings"]["endpoint_distribution_stddev"] = 0


    def _generate_final_report(self):
        if not self.openapi_spec:
            self.report["score"] = 0; self.report["status"] = "Not Assessed"; return

        f = self.report.get("findings", {})
        if not f:
            self.report["score"] = 0; self.report["status"] = "Poor"; return

        score = 0
        # Score from Tagging Quality (60%)
        tag_score = 0
        if f.get("unique_tags", 0) > 1:
            tag_score += 20 # Bonus for using tags
            # Penalize for low coverage
            tag_score += (f.get("tag_coverage", 0) / 100) * 20
            # Penalize for high std dev (uneven distribution)
            std_dev = f.get("endpoint_distribution_stddev", 10)
            tag_score += max(0, 20 - (std_dev * 2)) # Lower std dev is better
        score += tag_score

        # Score from Resource Granularity (40%)
        resource_count = f.get("unique_resources", 0)
        score += min(resource_count * 5, 40)

        self.report["score"] = int(score)

        status_map = {90: "Excellent", 70: "Good", 40: "Needs Improvement", 0: "Poor"}
        self.report["status"] = next((v for k, v in status_map.items() if self.report["score"] >= k), "Poor")

        if f.get("tag_coverage", 100) < 90:
            self.report["recommendations"].append("Use 'tags' on all operations to group them into logical modules.")
        if f.get("endpoint_distribution_stddev", 0) > 5 and f.get("unique_tags", 0) > 1:
            self.report["recommendations"].append("Balance endpoints across tags to avoid large, monolithic modules.")
        if f.get("unique_resources", 0) < 3 and f.get("total_endpoints", 0) > 5:
            self.report["recommendations"].append("Structure API paths around clear noun-based resources (e.g., /users).")

    def _print_final_report(self):
        f = self.report.get("findings", {})
        print_header("Final Assessment Report")
        print_status("Overall Status", self.report['status'])
        print_status("API Modularity Score", f"{self.report['score']}/100")

        if f:
            print_subheader("Modularity & Granularity Metrics")
            print_status("Endpoint Tagging Coverage", f"{f.get('tag_coverage', 0):.1f}%")
            print_status("Number of Unique Tags", f.get('unique_tags', 0))
            std_dev = f.get('endpoint_distribution_stddev')
            dist_status = "Even" if std_dev is not None and std_dev < 3 else "Uneven"
            print_status(f"Endpoint Distribution (StdDev: {std_dev:.2f})", dist_status)
            print_status("Number of Unique Top-Level Resources", f.get('unique_resources', 0))

        if self.report["recommendations"]:
            print_subheader("Recommendations")
            for rec in sorted(list(set(self.report["recommendations"]))):
                print_recommendation(rec)

