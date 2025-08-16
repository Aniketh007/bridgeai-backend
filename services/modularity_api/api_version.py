# Pillar 3, Sub-pillar 7
# See Bridge.ipynb cell 27 for logic
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

class ApiVersioningAnalyzer:
    """
    Analyzes the versioning and deprecation strategy of an API via its OpenAPI spec.
    Based on ARI v10.0 Pillar 3, Sub-pillar 7.
    """
    CONVENTIONAL_PATHS = ["/.well-known/openapi.json", "/openapi.json", "/api/docs.json", "/api.json"]
    SEMVER_REGEX = re.compile(r'^\d+\.\d+\.\d+$')
    VERSION_IN_PATH_REGEX = re.compile(r'/v\d+/')

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
        print_header("ARI Sub-Pillar 3.7: API Versioning & Deprecation Strategy")
        if self._find_openapi_spec():
            print_status("OpenAPI Specification Found", "PASS")
            self._analyze_versioning()
            self._analyze_deprecation()
        else:
            print_status("OpenAPI Specification Found", "FAIL")

        self._generate_final_report()
        self._print_final_report()

    def _analyze_versioning(self):
        """Analyzes the info.version and servers objects for versioning strategy."""
        info = self.openapi_spec.get("info", {})
        version = info.get("version")
        if version:
            self.report["findings"]["has_version_field"] = True
            self.report["findings"]["version_string"] = version
            self.report["findings"]["is_semver"] = bool(self.SEMVER_REGEX.match(version))

        servers = self.openapi_spec.get("servers", [])
        self.report["findings"]["version_in_path"] = any(self.VERSION_IN_PATH_REGEX.search(s.get("url", "")) for s in servers)

    def _analyze_deprecation(self):
        """Analyzes all operations for the 'deprecated: true' flag."""
        paths = self.openapi_spec.get("paths", {})
        total_endpoints = 0
        deprecated_endpoints = 0
        for path, methods in paths.items():
            for method, details in methods.items():
                total_endpoints += 1
                if details.get("deprecated") is True:
                    deprecated_endpoints += 1

        self.report["findings"]["total_endpoints"] = total_endpoints
        self.report["findings"]["deprecated_endpoints_count"] = deprecated_endpoints
        if total_endpoints > 0:
            self.report["findings"]["deprecation_percentage"] = (deprecated_endpoints / total_endpoints) * 100

    def _generate_final_report(self):
        if not self.openapi_spec:
            self.report["score"] = 0; self.report["status"] = "Not Assessed"; return

        score = 0
        f = self.report["findings"]

        # Versioning Score (60%)
        if f.get("has_version_field"):
            score += 20
            if f.get("is_semver"):
                score += 20
            if f.get("version_in_path"):
                score += 20

        # Deprecation Score (40%)
        # The mere presence of a deprecation mechanism is what's important
        if f.get("deprecated_endpoints_count", 0) > 0:
            score += 40

        self.report["score"] = score

        status_map = {90: "Excellent", 70: "Good", 40: "Needs Improvement", 0: "Poor"}
        self.report["status"] = next((v for k, v in status_map.items() if self.report["score"] >= k), "Poor")

        if not f.get("has_version_field"):
            self.report["recommendations"].append("Declare the API version in the `info.version` field of the OpenAPI spec.")
        if not f.get("is_semver"):
            self.report["recommendations"].append("Adopt Semantic Versioning (e.g., '1.2.3') to clearly communicate changes.")
        if f.get("deprecated_endpoints_count", 0) == 0 and f.get("total_endpoints", 0) > 0:
             self.report["recommendations"].append("Utilize the `deprecated: true` flag on old operations to signal upcoming changes.")

    def _print_final_report(self):
        f = self.report.get("findings", {})
        print_header("Final Assessment Report")
        print_status("Overall Status", self.report['status'])
        print_status("Versioning Strategy Score", f"{self.report['score']}/100")

        if f:
            print_subheader("Versioning Analysis")
            version_str = f.get('version_string', 'Not Found')
            print_status("API version is declared in 'info.version'", "PASS" if f.get("has_version_field") else "FAIL")
            print(f"  └─ Version Found: {version_str}")
            print_status("Version string uses Semantic Versioning (SemVer)", "PASS" if f.get("is_semver") else "FAIL")
            print_status("Version is included in the server URL (e.g., /v1/)", "PASS" if f.get("version_in_path") else "FAIL")

            print_subheader("Deprecation Analysis")
            deprecated_count = f.get("deprecated_endpoints_count", 0)
            print_status("Deprecated endpoints are marked with 'deprecated: true'", "PASS" if deprecated_count > 0 else "INFO")
            print(f"  └─ Found {deprecated_count} deprecated endpoints ({f.get('deprecation_percentage', 0):.1f}% of total)")

        if self.report["recommendations"]:
            print_subheader("Recommendations")
            for rec in sorted(list(set(self.report["recommendations"]))):
                print_recommendation(rec)

