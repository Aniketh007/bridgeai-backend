# Pillar 1, Sub-pillar 2
# See Bridge.ipynb cell 2 for logic
# ...existing code...
import requests
import urllib.robotparser
from urllib.parse import urlparse, urljoin

# Helper to print colored and formatted text for better readability
def print_header(text):
    print("\n" + "="*60)
    print(f" {text}")
    print("="*60)

def print_subheader(text):
    print("\n" + "-"*60)
    print(f" {text}")
    print("-"*60)

def print_status(message, status):
    # Pad message for alignment
    padded_message = f"{message:<45}"
    # Add color based on status
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

class RobotsTxtAnalyzer:
    """
    Analyzes a website's robots.txt for crawlability and integrity based on ARI v10.0 Pillar 1, Sub-pillar 2.
    """
    def __init__(self, base_url):
        self.base_url = self._format_base_url(base_url)
        self.robots_url = urljoin(self.base_url, 'robots.txt')
        self.report = {
            "recommendations": [],
            "findings": [],
            "score": 0,
            "status": "Not Assessed"
        }
        self.robots_content = None
        self.parser = urllib.robotparser.RobotFileParser()

        # User agents to test against, including web, general AI, and specific AI crawlers
        self.USER_AGENTS = {
            "Wildcard": "*",
            "Google Search": "Googlebot",
            "Google AI": "Google-Extended",
            "OpenAI AI": "GPTBot",
            "Anthropic AI": "anthropic-ai"
        }

        # Common paths for critical resources
        self.CRITICAL_PATHS = ["/static/", "/assets/", "/css/", "/js/", "/images/", "/media/"]

    def _format_base_url(self, url):
        """Ensures the URL has a scheme and is just the base domain."""
        parsed = urlparse(url)
        if not parsed.scheme:
            url = "https://" + url
            parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def fetch_robots_txt(self):
        """Fetches the robots.txt file from the target domain."""
        print_status(f"Fetching {self.robots_url}", "IN PROGRESS")
        try:
            response = requests.get(self.robots_url, timeout=10, headers={'User-Agent': 'ARI-Robots-Analyzer/1.0'})
            if response.status_code == 200:
                self.robots_content = response.text
                self.parser.parse(self.robots_content.splitlines())
                print_status(f"Successfully fetched robots.txt", "PASS")
                return True
            else:
                self.report["findings"].append(f"robots.txt is missing or inaccessible (Status: {response.status_code}).")
                print_status(f"robots.txt inaccessible (HTTP {response.status_code})", "WARN")
                return False
        except requests.exceptions.RequestException as e:
            self.report["findings"].append(f"Could not fetch robots.txt due to a network error: {e}")
            print_status("Failed to fetch robots.txt (Network Error)", "FAIL")
            return False

    def check_sitemap_directive(self):
        """Checks for the presence of a Sitemap directive."""
        if self.robots_content and 'sitemap:' in self.robots_content.lower():
            self.report["findings"].append("Sitemap directive is present in robots.txt.")
            print_status("Sitemap directive check", "PASS")
            return True
        else:
            self.report["findings"].append("Sitemap directive is missing from robots.txt.")
            print_status("Sitemap directive check", "WARN")
            return False

    def check_crawlability(self):
        """Checks if key user agents are blocked from the root or critical paths."""
        is_globally_blocked = False

        print_subheader("Agent Crawlability Analysis")

        for name, agent in self.USER_AGENTS.items():
            # Check for root access
            can_fetch_root = self.parser.can_fetch(agent, self.base_url + "/")
            status = "PASS" if can_fetch_root else "FAIL"
            print_status(f"Root access for '{name}' ({agent})", status)

            if not can_fetch_root:
                 self.report["findings"].append(f"Agent '{name}' is blocked from crawling the site root.")
                 if agent == '*':
                    is_globally_blocked = True

            # Check critical resource paths
            blocked_resources = []
            for path in self.CRITICAL_PATHS:
                if not self.parser.can_fetch(agent, self.base_url + path):
                    blocked_resources.append(path)

            if blocked_resources:
                status = "FAIL"
                self.report["findings"].append(f"Agent '{name}' is blocked from critical resource paths: {', '.join(blocked_resources)}")
            else:
                status = "PASS"
            print_status(f"Critical resource access for '{name}'", status)

        return is_globally_blocked

    def run_analysis(self):
        """Main execution logic."""
        print_header("ARI Sub-Pillar 1.2: Crawlability & Directive Integrity")

        if not self.fetch_robots_txt():
            self.report["status"] = "Poor"
            self.report["score"] = 40  # Not a blocker, but a significant issue
            self.report["recommendations"].append("Create a properly formatted robots.txt file to provide clear instructions to crawlers.")
            self.report["recommendations"].append("Include a sitemap reference in the new robots.txt file.")
            self._print_final_report()
            return

        has_sitemap = self.check_sitemap_directive()
        is_blocked = self.check_crawlability()

        # Scoring Logic
        if is_blocked:
            self.report["status"] = "Critical Failure"
            self.report["score"] = 0 # BLOCKER
            self.report["recommendations"].append("Major Issue: The site is globally blocked (Disallow: / for User-agent: *). This is a critical barrier for all agents.")
        else:
            # Start with a base score for a valid, non-blocking file
            score = 70
            status = "Good"

            # Bonus for having a sitemap
            if has_sitemap:
                score += 20
            else:
                self.report["recommendations"].append("Include a sitemap reference in robots.txt for better crawl efficiency.")

            # Penalty for any blocked critical resources
            if any("blocked from critical resource" in f for f in self.report["findings"]):
                score -= 30
                self.report["recommendations"].append("Allow access to critical resources (CSS, JS, images) for AI agents to ensure proper page rendering and understanding.")

            # Penalty for blocking specific (non-*) AI agents
            if any("is blocked from crawling" in f and "Wildcard" not in f for f in self.report["findings"]):
                score -= 15
                self.report["recommendations"].append("Review agent-specific directives to ensure key AI crawlers (e.g., Google-Extended, GPTBot) are not unintentionally blocked.")

            self.report["score"] = max(0, score) # Ensure score doesn't go below 0

            if self.report["score"] >= 90:
                self.report["status"] = "Excellent"
            elif self.report["score"] >= 65:
                 self.report["status"] = "Good"
            else:
                 self.report["status"] = "Needs Improvement"

        # Final recommendation if the file is empty or lacks directives
        if not self.robots_content.strip() or ("user-agent" not in self.robots_content.lower()):
            self.report["recommendations"].append("The robots.txt file is empty or malformed. Add appropriate User-agent and Disallow/Allow directives.")
            self.report["score"] = min(self.report["score"], 30) # Cap score for malformed file
            self.report["status"] = "Poor"

        self._print_final_report()

    def _print_final_report(self):
        """Prints the final formatted report."""
        print_header("Final Assessment Report")
        print_status("Overall Status", self.report['status'])
        print_status("ARI Score (out of 100)", self.report['score'])

        print_subheader("Findings")
        if self.report["findings"]:
            for finding in self.report["findings"]:
                print(f"  - {finding}")
        else:
            print("  - No significant issues found.")

        if self.report["recommendations"]:
            print_subheader("Recommendations (Based on ARI v10.0)")
            for rec in self.report["recommendations"]:
                print_recommendation(rec)

