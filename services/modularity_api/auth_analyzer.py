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

class AuthAnalyzer:
    """
    Analyzes an OpenAPI specification for agent-friendly authentication schemes.
    Based on ARI v10.0 Pillar 3, Sub-pillar 2.
    """
    CONVENTIONAL_PATHS = ["/.well-known/openapi.json", "/openapi.json", "/api/docs.json", "/api.json"]

    def __init__(self, target_url):
        if not target_url.startswith('http'):
            target_url = 'https://' + target_url
        parsed_url = urlparse(target_url)
        self.base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        self.report = {"findings": {}, "recommendations": [], "score": 0, "status": "Not Assessed"}
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'ARI-Auth-Analyzer/1.0'})
        self.openapi_spec = None

    def _get_json(self, url):
        try:
            res = self.session.get(url, timeout=7)
            res.raise_for_status()
            return res.json()
        except (requests.exceptions.RequestException, json.JSONDecodeError):
            return None

    def _find_openapi_spec(self):
        """Leverages logic from 3.1 to find the spec. Simplified for this sub-pillar."""
        print_subheader("Step 1: Discovering OpenAPI Specification")
        # Path 1: agents.json
        agents_url = urljoin(self.base_url, "/.well-known/agents.json")
        agents_data = self._get_json(agents_url)
        if agents_data and agents_data.get("api_spec_url"):
            spec_url = urljoin(self.base_url, agents_data["api_spec_url"])
            print_status(f"Found spec via agents.json: {spec_url}", "PASS")
            self.openapi_spec = self._get_json(spec_url)
            return

        # Path 2: Conventional locations
        for path in self.CONVENTIONAL_PATHS:
            spec_url = urljoin(self.base_url, path)
            spec_data = self._get_json(spec_url)
            if spec_data:
                print_status(f"Found spec via conventional path: {spec_url}", "PASS")
                self.openapi_spec = spec_data
                return
        print_status("Could not discover an OpenAPI specification", "FAIL")

    def _analyze_security_schemes(self):
        """Parses the components.securitySchemes object for auth types."""
        print_subheader("Step 2: Analyzing Declared Security Schemes")
        findings = self.report["findings"]
        findings.update({"supports_oauth_client_credentials": False, "supports_apikey": False, "supports_jwt": False})

        schemes = self.openapi_spec.get("components", {}).get("securitySchemes", {})
        if not schemes:
            print_status("No securitySchemes declared in the specification", "FAIL")
            return

        for name, details in schemes.items():
            # OAuth 2.0
            if details.get("type") == "oauth2":
                # Check specifically for the client credentials flow
                if "clientCredentials" in details.get("flows", {}):
                    findings["supports_oauth_client_credentials"] = True

            # API Key
            elif details.get("type") == "apiKey":
                findings["supports_apikey"] = True

            # JWT Bearer Token
            elif details.get("type") == "http" and details.get("scheme") == "bearer":
                findings["supports_jwt"] = True

        print_status("OAuth 2.0 with Client Credentials Flow", "PASS" if findings["supports_oauth_client_credentials"] else "FAIL")
        print_status("API Key Authentication", "PASS" if findings["supports_apikey"] else "FAIL")
        print_status("JWT Bearer Token Authentication", "PASS" if findings["supports_jwt"] else "FAIL")

    def run_analysis(self):
        print_header("ARI Sub-Pillar 3.2: Agent-Friendly Authentication")
        self._find_openapi_spec()
        if self.openapi_spec:
            self._analyze_security_schemes()
        self._generate_final_report()
        self._print_final_report()

    def _generate_final_report(self):
        if not self.openapi_spec:
            self.report["score"] = 0
            self.report["status"] = "BLOCKER"
            self.report["recommendations"].append("An OpenAPI specification is required to declare authentication methods.")
            return

        score = 0
        f = self.report["findings"]
        # Score based on the most robust method found
        if f.get("supports_oauth_client_credentials"):
            score = 100
        elif f.get("supports_jwt"):
            score = 75
        elif f.get("supports_apikey"):
            score = 50

        self.report["score"] = score

        if score == 100: self.report["status"] = "Excellent"
        elif score >= 75: self.report["status"] = "Good"
        elif score >= 50: self.report["status"] = "Acceptable"
        else:
             self.report["status"] = "BLOCKER"
             self.report["recommendations"].append("Implement and declare an agent-friendly auth method (OAuth2 Client Credentials, API Key, or JWT).")

        if score < 100:
             self.report["recommendations"].append("For maximum security and flexibility, support the OAuth 2.0 Client Credentials grant type.")
             self.report["recommendations"].append("Create clear documentation for your authentication flow with code examples.")

    def _print_final_report(self):
        print_header("Final Assessment Report")
        print_status("Overall Status", self.report['status'])
        print_status("Agent Authentication Score", f"{self.report['score']}/100")

        if self.openapi_spec:
            print_subheader("Supported Authentication Schemes")
            print_status("OAuth 2.0 Client Credentials", "SUPPORTED" if self.report["findings"].get("supports_oauth_client_credentials") else "NOT FOUND")
            print_status("API Key", "SUPPORTED" if self.report["findings"].get("supports_apikey") else "NOT FOUND")
            print_status("JWT Bearer Token", "SUPPORTED" if self.report["findings"].get("supports_jwt") else "NOT FOUND")

        if self.report["recommendations"]:
            print_subheader("Recommendations")
            for rec in sorted(list(set(self.report["recommendations"]))):
                print_recommendation(rec)

