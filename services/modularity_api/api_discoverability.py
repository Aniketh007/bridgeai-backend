# Pillar 3, Sub-pillar 1
# See Bridge.ipynb cell 21 for logic
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

class ApiDiscoverabilityAnalyzer:
    """
    Checks for API discoverability and specification quality.
    Based on ARI v10.0 Pillar 3, Sub-pillar 1.
    """
    CONVENTIONAL_PATHS = ["/.well-known/openapi.json", "/openapi.json", "/api/docs.json", "/api.json"]
    INTROSPECTION_QUERY = """ query IntrospectionQuery { __schema { queryType { name } mutationType { name } subscriptionType { name } types { ...FullType } directives { name description locations args { ...InputValue } } } } fragment FullType on __Type { kind name description fields(includeDeprecated: true) { name description args { ...InputValue } type { ...TypeRef } isDeprecated deprecationReason } inputFields { ...InputValue } interfaces { ...TypeRef } enumValues(includeDeprecated: true) { name description isDeprecated deprecationReason } possibleTypes { ...TypeRef } } fragment InputValue on __InputValue { name description type { ...TypeRef } defaultValue } fragment TypeRef on __Type { kind name ofType { kind name ofType { kind name ofType { kind name ofType { kind name ofType { kind name ofType { kind name ofType { kind name } } } } } } } } """

    def __init__(self, target_url):
        if not target_url.startswith('http'):
            target_url = 'https://' + target_url
        parsed_url = urlparse(target_url)
        self.base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        self.report = {"findings": {}, "recommendations": [], "score": 0, "status": "Not Assessed"}
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'ARI-ApiDiscoverability-Analyzer/1.0'})

    def run_analysis(self):
        print_header("ARI Sub-Pillar 3.1: Endpoint Discoverability & Specification")
        # Start with the highest priority discovery methods first
        if not self._check_agents_json():
            if not self._check_common_locations():
                print_status("No OpenAPI spec found in common locations", "FAIL")

        self._check_graphql_introspection()
        self._generate_final_report()
        self._print_final_report()

    def _get_json(self, url):
        try:
            res = self.session.get(url, timeout=7)
            res.raise_for_status()
            return res.json()
        except (requests.exceptions.RequestException, json.JSONDecodeError):
            return None

    def _check_agents_json(self):
        print_subheader("Path 1: Checking agents.json (Ideal Method)")
        agents_url = urljoin(self.base_url, "/.well-known/agents.json")
        agents_data = self._get_json(agents_url)
        if agents_data and agents_data.get("api_spec_url"):
            spec_url = urljoin(self.base_url, agents_data["api_spec_url"])
            print_status(f"Found api_spec_url in agents.json: {spec_url}", "PASS")
            self._validate_openapi_spec(spec_url, "agents.json")
            return True
        print_status("No api_spec_url found in agents.json", "INFO")
        return False

    def _check_common_locations(self):
        print_subheader("Path 2: Checking Conventional OpenAPI Locations")
        for path in self.CONVENTIONAL_PATHS:
            spec_url = urljoin(self.base_url, path)
            print_status(f"Checking for spec at {spec_url}", "IN PROGRESS")
            spec_data = self._get_json(spec_url)
            if spec_data:
                print_status(f"Found potential spec at {spec_url}", "PASS")
                self._validate_openapi_spec(spec_url, "conventional_path")
                return True
        return False

    def _check_graphql_introspection(self):
        print_subheader("Path 3: Checking for GraphQL Introspection")
        graphql_url = urljoin(self.base_url, "/graphql")
        try:
            res = self.session.post(graphql_url, json={'query': self.INTROSPECTION_QUERY}, timeout=7)
            if res.status_code == 200 and "data" in res.json() and "errors" not in res.json():
                self.report["findings"]["graphql_introspection"] = True
                print_status("GraphQL endpoint with introspection is enabled", "PASS")
            else:
                self.report["findings"]["graphql_introspection"] = False
        except requests.exceptions.RequestException:
            self.report["findings"]["graphql_introspection"] = False

        if not self.report["findings"].get("graphql_introspection"):
            print_status("GraphQL introspection is not enabled or not found", "INFO")

    def _validate_openapi_spec(self, url, method):
        spec = self._get_json(url)
        if not spec:
            self.report["findings"]["openapi_spec"] = {"method": method, "valid": False, "error": "FetchError"}
            return

        findings = {"method": method, "url": url, "valid": True}
        if "openapi" in spec and spec["openapi"].startswith("3."):
            findings["version"] = "OpenAPI 3+"
        elif "swagger" in spec:
            findings["version"] = "Swagger 2.0"
        else:
            findings["version"] = "Unknown"

        # Calculate description coverage
        paths = spec.get("paths", {})
        total_endpoints = 0
        endpoints_with_desc = 0
        for path_methods in paths.values():
            for method_details in path_methods.values():
                total_endpoints += 1
                if method_details.get("description"):
                    endpoints_with_desc += 1

        findings["description_coverage"] = (endpoints_with_desc / total_endpoints) * 100 if total_endpoints > 0 else 0
        self.report["findings"]["openapi_spec"] = findings

    def _generate_final_report(self):
        score = 0
        spec_findings = self.report["findings"].get("openapi_spec")
        if spec_findings:
            if spec_findings["version"] == "Swagger 2.0":
                score = 25
            elif spec_findings["version"] == "OpenAPI 3+":
                score = 50 + (spec_findings["description_coverage"] * 0.3) # Up to 30 pts for coverage
                if spec_findings["method"] == "agents.json":
                    score += 20 # Bonus for ideal discovery method

        if self.report["findings"].get("graphql_introspection"):
            score = max(score, 80) # If GraphQL is well-configured, that's a good score

        self.report["score"] = int(score)
        status_map = {90: "Excellent", 70: "Good", 40: "Needs Improvement", 0: "BLOCKER"}
        self.report["status"] = next((v for k, v in status_map.items() if self.report["score"] >= k), "BLOCKER")

        if self.report["score"] < 40: self.report["recommendations"].append("Generate OpenAPI 3.0+ spec and host it at a standard location.")
        if spec_findings and spec_findings["method"] != "agents.json":
            self.report["recommendations"].append("Declare the spec location in an `agents.json` file for explicit discovery.")
        if spec_findings and spec_findings["description_coverage"] < 75:
            self.report["recommendations"].append("Include comprehensive descriptions for all API endpoints and parameters.")
        if not self.report["findings"].get("graphql_introspection"):
             self.report["recommendations"].append("If using GraphQL, enable introspection for discoverability.")

    def _print_final_report(self):
        f = self.report["findings"]
        print_header("Final Assessment Report")
        print_status("Overall Status", self.report['status'])
        print_status("Discoverability Score", f"{self.report['score']}/100")

        print_subheader("Analysis Details")
        spec = f.get("openapi_spec")
        if spec:
            print_status("OpenAPI Specification Found", "PASS")
            print(f"  ├─ Method: {spec['method']}")
            print(f"  ├─ URL: {spec['url']}")
            print(f"  ├─ Version: {spec['version']}")
            print(f"  └─ Description Coverage: {spec['description_coverage']:.1f}%")
        else:
            print_status("OpenAPI Specification Found", "FAIL")

        print_status("GraphQL Introspection Enabled", "PASS" if f.get("graphql_introspection") else "FAIL")

        if self.report["recommendations"]:
            print_subheader("Recommendations")
            for rec in sorted(list(set(self.report["recommendations"]))):
                print_recommendation(rec)
