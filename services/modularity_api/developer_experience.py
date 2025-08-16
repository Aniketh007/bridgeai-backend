# Pillar 3, Sub-pillar 5
# See Bridge.ipynb cell 25 for logic
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

class DeveloperExperienceAnalyzer:
    """
    Analyzes a website's developer experience and onboarding infrastructure.
    Based on ARI v10.0 Pillar 3, Sub-pillar 5.
    """
    DEV_SUBDOMAINS = ["developers", "developer", "docs", "api", "dev"]

    def __init__(self, target_url):
        if not target_url.startswith('http'):
            target_url = 'https://' + target_url
        parsed_url = urlparse(target_url)
        self.domain = parsed_url.netloc.replace("www.", "")
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
        """Finds the OpenAPI spec using a simplified discovery method."""
        spec_url = urljoin(self.base_url, "/.well-known/openapi.json")
        self.openapi_spec = self._get_json(spec_url)
        if not self.openapi_spec:
             self.openapi_spec = self._get_json(urljoin(self.base_url, "/openapi.json"))
        self.report["findings"]["openapi_spec_found"] = self.openapi_spec is not None

    def run_analysis(self):
        print_header("ARI Sub-Pillar 3.5: Developer Experience & Onboarding")
        self._find_openapi_spec()
        self._check_for_dev_portal()
        if self.openapi_spec:
            self._analyze_spec_for_dx()
        self._generate_final_report()
        self._print_final_report()

    def _check_for_dev_portal(self):
        """Probes common URLs for a developer portal."""
        print_subheader("Checking for Developer Portal")
        for sub in self.DEV_SUBDOMAINS:
            portal_url = f"https://{sub}.{self.domain}"
            try:
                res = requests.head(portal_url, timeout=5, allow_redirects=True)
                if res.status_code == 200:
                    self.report["findings"]["dev_portal_found"] = True
                    self.report["findings"]["dev_portal_url"] = portal_url
                    return
            except requests.exceptions.RequestException:
                continue
        self.report["findings"]["dev_portal_found"] = False

    def _analyze_spec_for_dx(self):
        """Analyzes the found OpenAPI spec for sandbox and SDK information."""
        print_subheader("Analyzing OpenAPI Spec for DX Signals")
        # Check for Sandbox Environment
        servers = self.openapi_spec.get("servers", [])
        has_sandbox = False
        for server in servers:
            desc = server.get("description", "").lower()
            if "sandbox" in desc or "test" in desc or "staging" in desc:
                has_sandbox = True
                break
        self.report["findings"]["sandbox_found"] = has_sandbox

        # Check for SDKs
        # This is a heuristic - looking for a custom extension
        has_sdks = "x-sdk-supported-languages" in self.openapi_spec or \
                   "x-sdks" in self.openapi_spec
        self.report["findings"]["sdk_evidence_found"] = has_sdks

    def _generate_final_report(self):
        score = 0
        f = self.report["findings"]

        if f.get("sandbox_found"): score += 40
        if f.get("dev_portal_found"): score += 30
        if f.get("openapi_spec_found"): score += 20 # Proxy for interactive explorer
        if f.get("sdk_evidence_found"): score += 10

        self.report["score"] = score

        status_map = {90: "Excellent", 70: "Good", 40: "Needs Improvement", 0: "CRITICAL"}
        self.report["status"] = next((v for k, v in status_map.items() if self.report["score"] >= k), "CRITICAL")

        if not f.get("sandbox_found"):
            self.report["recommendations"].append("Provide a sandbox environment for safe development and testing.")
        if not f.get("dev_portal_found"):
            self.report["recommendations"].append("Create a comprehensive developer portal at a common URL (e.g., developers.yourdomain.com).")
        if not f.get("openapi_spec_found"):
            self.report["recommendations"].append("Publish an OpenAPI spec to enable interactive API explorers.")
        if not f.get("sdk_evidence_found"):
            self.report["recommendations"].append("Consider generating and providing SDKs in popular programming languages.")

    def _print_final_report(self):
        f = self.report["findings"]
        print_header("Final Assessment Report")
        print_status("Overall Status", self.report['status'])
        print_status("Developer Experience Score", f"{self.report['score']}/100")

        print_subheader("DX Checklist")
        portal_status = f"PASS (at {f['dev_portal_url']})" if f.get("dev_portal_found") else "FAIL"
        print_status("Developer Portal discoverable", portal_status)

        print_status("Sandbox environment declared in API spec", "PASS" if f.get("sandbox_found") else "FAIL")

        print_status("Interactive explorer is possible (OpenAPI spec found)", "PASS" if f.get("openapi_spec_found") else "FAIL")

        print_status("Evidence of SDKs found in API spec", "PASS" if f.get("sdk_evidence_found") else "FAIL")

        if self.report["recommendations"]:
            print_subheader("Recommendations")
            for rec in sorted(list(set(self.report["recommendations"]))):
                print_recommendation(rec)
