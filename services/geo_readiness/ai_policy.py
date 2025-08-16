# Pillar 1, Sub-pillar 4
# See Bridge.ipynb cell 4 for logic
# ...existing code...
import requests
from urllib.parse import urlparse, urljoin
import re

# Helper to print colored and formatted text for better readability
def print_header(text):
    print("\n" + "="*70)
    print(f" {text}")
    print("="*70)

def print_subheader(text):
    print("\n" + "-"*70)
    print(f" {text}")
    print("-"*70)

def print_status(message, status):
    padded_message = f"{message:<55}"
    if status == "FAIL" or status == "CRITICAL":
        status_str = f"[\033[91m{status}\033[0m]" # Red
    elif status == "WARN":
        status_str = f"[\033[93m{status}\033[0m]" # Yellow
    elif status == "PASS" or status == "INFO" or "FOUND":
        status_str = f"[\033[92m{status}\033[0m]" # Green
    else:
        status_str = f"[{status}]"
    print(f"{padded_message} {status_str}")

def print_recommendation(rec):
    print(f"  - {rec}")

class Advanced_AI_Policy_Analyzer:
    """
    Performs a dynamic, multi-location search for AI usage policy files (llms.txt and variations)
    based on ARI v10.0 Pillar 1, Sub-pillar 4.
    """
    # Define search parameters - from most to least likely
    PRIMARY_FILENAMES = ["/llms.txt", "/llm.txt", "/llms-full.txt"]
    COMMON_SUBDOMAINS = ["docs", "developers", "legal", "api"]
    COMMON_SUBDIRECTORIES = ["/docs", "/legal", "/.well-known"]

    def __init__(self, target_url):
        self.base_url = self._normalize_url(target_url)
        self.domain = urlparse(self.base_url).netloc
        self.report = {
            "findings": {}, "recommendations": [], "score": 0, "status": "Not Assessed",
            "search_log": []
        }
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'ARI-Advanced-Policy-Analyzer/2.0'})

    def _normalize_url(self, url):
        parsed = urlparse(url)
        if not parsed.scheme:
            url = "https://" + url
            parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def find_policy_file(self):
        """
        Executes a prioritized search across domains, subdomains, and directories.
        Returns the URL of the first valid policy file found, or None.
        """
        # --- Tier 1: Check Root Domain (www and non-www) ---
        print_subheader("Tier 1: Searching Root Domain")
        hosts_to_check = {self.domain}
        if self.domain.startswith('www.'):
            hosts_to_check.add(self.domain[4:])
        else:
            hosts_to_check.add('www.' + self.domain)

        for host in sorted(list(hosts_to_check)):
            for filename in self.PRIMARY_FILENAMES:
                url_to_check = f"https://{host}{filename}"
                if self._check_url_existence(url_to_check):
                    return url_to_check

        # --- Tier 2: Check Common Subdomains ---
        print_subheader("Tier 2: Searching Common Subdomains")
        base_domain = re.sub(r'^www\.', '', self.domain)
        for subdomain in self.COMMON_SUBDOMAINS:
            host = f"{subdomain}.{base_domain}"
            for filename in self.PRIMARY_FILENAMES:
                url_to_check = f"https://{host}{filename}"
                if self._check_url_existence(url_to_check):
                    return url_to_check

        # --- Tier 3: Check Common Subdirectories ---
        print_subheader("Tier 3: Searching Common Subdirectories")
        for host in sorted(list(hosts_to_check)):
            for directory in self.COMMON_SUBDIRECTORIES:
                # Only check llms.txt in subdirs to be efficient
                url_to_check = f"https://{host}{directory}/llms.txt"
                if self._check_url_existence(url_to_check):
                    return url_to_check

        return None

    def _check_url_existence(self, url):
        """Uses a HEAD request to efficiently check if a URL exists."""
        self.report["search_log"].append(f"Checking: {url}")
        try:
            response = self.session.head(url, timeout=5, allow_redirects=True)
            if response.status_code == 200:
                print_status(f"FOUND: Policy file candidate at {url}", "FOUND")
                return True
        except requests.exceptions.RequestException:
            # This is expected for non-existent domains/URLs, so we just pass
            pass
        return False

    def analyze_found_file(self, policy_url):
        """Fetches and parses the content of the confirmed policy file."""
        try:
            response = self.session.get(policy_url, timeout=10)
            content = response.text
            self.report["findings"]["presence"] = True
            self.report["findings"]["location"] = policy_url
            if not content.strip():
                self.report["findings"]["is_empty"] = True
                return

            self.report["findings"]["is_empty"] = False
            # Parsing logic
            lines = content.strip().splitlines()
            self.report["findings"].update({"has_user_agent": False, "has_notrain": False, "has_permissions": False})
            for line in lines:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip().lower()
                    if key == 'user-agent': self.report["findings"]["has_user_agent"] = True
                    elif key == 'notrain': self.report["findings"]["has_notrain"] = True; self.report["findings"]["has_permissions"] = True
                    elif key in ['allow', 'disallow', 'noindex']: self.report["findings"]["has_permissions"] = True
        except requests.exceptions.RequestException as e:
            self.report["findings"]["presence"] = False
            self.report["findings"]["error"] = f"Failed to fetch content from {policy_url}: {e}"

    def run_analysis(self):
        print_header("ARI Sub-Pillar 1.4: AI Usage & Training Policy (Advanced Search)")
        found_url = self.find_policy_file()

        if found_url:
            self.analyze_found_file(found_url)
        else:
            self.report["findings"]["presence"] = False

        self._generate_final_report()
        self._print_final_report()

    def _generate_final_report(self):
        if not self.report["findings"].get("presence"):
            self.report["status"] = "Critical Failure"
            self.report["score"] = 0
            self.report["recommendations"].append("Create an AI policy file. The emerging standard is '/llms.txt' at the root of your domain.")
            self.report["recommendations"].append("Specify clear usage policies, such as 'User-agent: *' and 'NoTrain: True'.")
            return

        score = 50 # Base score for just having the file
        if self.report["findings"].get("has_user_agent"): score += 20
        if self.report["findings"].get("has_permissions"): score += 15
        if self.report["findings"].get("has_notrain"): score += 15
        self.report["score"] = min(score, 100)

        if self.report["score"] >= 90: self.report["status"] = "Excellent"
        elif self.report["score"] >= 70: self.report["status"] = "Good"
        else: self.report["status"] = "Needs Improvement"

        if not self.report["findings"].get("has_user_agent"):
            self.report["recommendations"].append("Add 'User-agent:' directives to specify which agents the rules apply to.")
        if not self.report["findings"].get("has_permissions"):
            self.report["recommendations"].append("Add permission directives (e.g., 'NoTrain', 'NoIndex', 'Allow', 'Disallow').")

    def _print_final_report(self):
        print_header("Final Assessment Report")
        print_status("Overall Status", self.report['status'])
        print_status("ARI Score (out of 100)", self.report['score'])

        print_subheader("Findings")
        if not self.report["findings"].get("presence"):
            print(f"  - No AI policy file found after {len(self.report['search_log'])} checks across common locations.")
        else:
            print(f"  - [+] Found AI policy file at: {self.report['findings']['location']}")
            if self.report["findings"].get("is_empty"):
                print("  - [!] The file is present but empty.")
            else:
                print(f"  - Contains 'User-agent' directives: {'Yes' if self.report['findings'].get('has_user_agent') else 'No'}")
                print(f"  - Contains explicit permission directives: {'Yes' if self.report['findings'].get('has_permissions') else 'No'}")

        if self.report["recommendations"]:
            print_subheader("Recommendations (Based on ARI v10.0)")
            for rec in self.report["recommendations"]:
                print_recommendation(rec)

