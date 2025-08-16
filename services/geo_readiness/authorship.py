# Pillar 1, Sub-pillar 7
# See Bridge.ipynb cell 7 for logic
# ...existing code...
import requests
import json
from urllib.parse import urlparse
from bs4 import BeautifulSoup

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
    elif status == "PASS" or status == "INFO":
        status_str = f"[\033[92m{status}\033[0m]" # Green
    else:
        status_str = f"[{status}]"
    print(f"{padded_message} {status_str}")

def print_recommendation(rec):
    print(f"  - {rec}")

class AuthorshipAnalyzer:
    """
    Analyzes a page for authorship and human accountability signals via Schema.org data.
    Based on ARI v10.0 Pillar 1, Sub-pillar 7.
    """
    def __init__(self, target_url):
        if not target_url.startswith('http'):
            target_url = 'https://' + target_url
        self.url = target_url
        self.report = {
            "findings": {}, "recommendations": [], "score": 0, "status": "Not Assessed"
        }
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'ARI-Authorship-Analyzer/1.0'})

    def _find_and_analyze_schema(self, soup):
        """Finds ld+json schema and analyzes it for authorship information."""
        scripts = soup.find_all('script', type='application/ld+json')
        if not scripts:
            self.report["findings"]["has_ld_json"] = False
            return

        self.report["findings"]["has_ld_json"] = True
        article_schema = None
        for script in scripts:
            try:
                data = json.loads(script.string)
                # Data can be a single dict or a list of dicts
                schemas = data if isinstance(data, list) else [data]
                for schema in schemas:
                    schema_type = schema.get('@type', '')
                    if schema_type in ['Article', 'BlogPosting', 'NewsArticle']:
                        article_schema = schema
                        break
            except (json.JSONDecodeError, TypeError):
                continue
            if article_schema:
                break

        if not article_schema:
            self.report["findings"]["has_article_schema"] = False
            return

        self.report["findings"]["has_article_schema"] = True
        author_data = article_schema.get('author')
        if not author_data:
            self.report["findings"]["has_author_prop"] = False
            return

        self.report["findings"]["has_author_prop"] = True
        # Author can be a list or a single object
        authors = author_data if isinstance(author_data, list) else [author_data]

        # We only need to analyze the first, most prominent author for this audit
        author = authors[0]

        if isinstance(author, str):
            self.report["findings"]["author_type"] = "String"
        elif isinstance(author, dict):
            author_type = author.get('@type', '')
            self.report["findings"]["author_type"] = author_type
            if author_type == 'Person':
                self.report["findings"]["person_has_name"] = 'name' in author
                self.report["findings"]["person_has_verifiable_link"] = 'url' in author or 'sameAs' in author

    def run_analysis(self):
        print_header("ARI Sub-Pillar 1.7: Authorship & Human Accountability")
        try:
            response = self.session.get(self.url, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print_status(f"Failed to fetch URL: {e}", "CRITICAL")
            return

        print_subheader("Analyzing Schema.org data for author information")
        soup = BeautifulSoup(response.text, 'lxml')
        self._find_and_analyze_schema(soup)
        self._generate_final_report()
        self._print_final_report()

    def _generate_final_report(self):
        score = 0
        if self.report["findings"].get("has_ld_json"): score = 10
        if self.report["findings"].get("has_article_schema"): score = 20
        if self.report["findings"].get("has_author_prop"):
            author_type = self.report["findings"].get("author_type")
            if author_type == "String": score = 40
            if author_type == "Organization": score = 60
            if author_type == "Person":
                score = 80
                if self.report["findings"].get("person_has_verifiable_link"):
                    score = 100

        self.report["score"] = score

        if score >= 90: self.report["status"] = "Excellent"
        elif score >= 70: self.report["status"] = "Good"
        elif score >= 40: self.report["status"] = "Needs Improvement"
        else: self.report["status"] = "Poor"

        # Recommendations
        if score < 100:
            self.report["recommendations"].append("Use Google's Rich Result Test to validate your structured data.")
        if score < 80:
             self.report["recommendations"].append("For all articles, specify an 'author' using the 'Person' schema type.")
        if score < 20:
             self.report["recommendations"].append("Implement Schema.org ld+json data on your pages, especially for articles.")
        if 80 <= score < 100:
             self.report["recommendations"].append("Add a 'url' or 'sameAs' property to your 'Person' schema linking to an author bio page or social profile to make the author verifiable.")

    def _print_final_report(self):
        print_header("Final Assessment Report")
        print_status("Overall Status", self.report['status'])
        print_status("ARI Score (out of 100)", self.report['score'])

        print_subheader("Findings Checklist")
        if not self.report["findings"]:
            print("  - Could not analyze page.")
            return

        print_status("Found ld+json structured data on page", "PASS" if self.report["findings"].get("has_ld_json") else "FAIL")
        print_status("Found Article/BlogPosting schema", "PASS" if self.report["findings"].get("has_article_schema") else "FAIL")
        print_status("Article schema contains an 'author' property", "PASS" if self.report["findings"].get("has_author_prop") else "FAIL")
        if self.report["findings"].get("has_author_prop"):
            author_type = self.report["findings"].get("author_type", "N/A")
            print_status(f"Author type is '{author_type}'", "PASS" if author_type == "Person" else "WARN")
            if author_type == "Person":
                print_status("Person schema includes a verifiable link ('url'/'sameAs')", "PASS" if self.report["findings"].get("person_has_verifiable_link") else "FAIL")

        if self.report["recommendations"]:
            print_subheader("Recommendations")
            for rec in self.report["recommendations"]:
                print_recommendation(rec)
