# Pillar 1, Sub-pillar 3
# See Bridge.ipynb cell 3 for logic
# ...existing code...
import requests
import xml.etree.ElementTree as ET
import gzip
from io import BytesIO
from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup
import time
import collections

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
    padded_message = f"{message:<45}"
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

class CanonicalizationAnalyzer:
    """
    Analyzes a website's canonicalization and source singularity based on ARI v10.0 Pillar 1, Sub-pillar 3.
    """
    def __init__(self, base_url, max_pages_to_check=25):
        self.base_url = self._format_base_url(base_url)
        self.max_pages_to_check = max_pages_to_check
        self.urls_to_check = collections.deque()
        self.checked_urls = set()
        self.report = {
            "pages_checked": 0,
            "pages_with_canonical": 0,
            "pages_with_absolute_canonical": 0,
            "pages_with_valid_canonical_target": 0,
            "issues": [],
            "recommendations": [],
            "score": 0,
            "status": "Not Assessed"
        }
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ARI-Canonical-Analyzer/1.0',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        })

    def _format_base_url(self, url):
        parsed = urlparse(url)
        if not parsed.scheme:
            url = "https://" + url
            parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def _fetch_url(self, url, method='GET'):
        try:
            if method == 'GET':
                response = self.session.get(url, timeout=10, allow_redirects=True)
            elif method == 'HEAD':
                response = self.session.head(url, timeout=10, allow_redirects=True)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            self.report["issues"].append(f"Network error for {url}: {e}")
            return None

    def get_urls_from_sitemap(self):
        """Tries to get a list of URLs from the sitemap."""
        print_status("Attempting to fetch URLs from sitemap", "INFO")
        sitemap_url = urljoin(self.base_url, 'sitemap.xml')
        response = self._fetch_url(sitemap_url)
        if not response:
            print_status("Could not find or fetch sitemap.xml", "WARN")
            return

        try:
            content = response.content
            if response.url.endswith('.gz') or 'gzip' in response.headers.get('Content-Type', ''):
                content = gzip.decompress(content)

            root = ET.fromstring(content)
            namespace = root.tag.split('}')[0][1:] if '}' in root.tag else ''

            # Simple parser for urlset, not handling sitemap indexes for this focused check
            for url_node in root.findall(f'.//{{{namespace}}}loc'):
                if len(self.urls_to_check) < self.max_pages_to_check:
                    self.urls_to_check.append(url_node.text.strip())
            print_status(f"Found {len(self.urls_to_check)} URLs in sitemap", "PASS")
        except Exception as e:
            self.report["issues"].append(f"Failed to parse sitemap.xml: {e}")
            print_status("Sitemap parsing failed", "WARN")

    def analyze_page(self, url):
        """Analyzes a single page for its canonical tag."""
        print(f"\n-> Checking: {url}")
        self.report["pages_checked"] += 1

        response = self._fetch_url(url, 'GET')
        if not response or 'text/html' not in response.headers.get('Content-Type', ''):
            print_status("Page is not valid HTML or is unreachable", "FAIL")
            return

        soup = BeautifulSoup(response.text, 'lxml')
        canonical_tag = soup.find('link', {'rel': 'canonical'})

        if not canonical_tag:
            self.report["issues"].append(f"Missing canonical tag on: {url}")
            print_status("Canonical tag presence", "FAIL")
            return

        self.report["pages_with_canonical"] += 1
        print_status("Canonical tag presence", "PASS")

        href = canonical_tag.get('href')
        if not href:
            self.report["issues"].append(f"Canonical tag has empty href on: {url}")
            print_status("Canonical href validity", "FAIL")
            return

        # *** THIS IS THE CORRECTED LINE ***
        parsed_href = urlparse(href)
        if not (parsed_href.scheme and parsed_href.netloc):
            self.report["issues"].append(f"Relative canonical URL '{href}' found on: {url}")
            print_status("Canonical URL is absolute", "FAIL")
            return

        self.report["pages_with_absolute_canonical"] += 1
        print_status("Canonical URL is absolute", "PASS")

        # Check if the canonical target is accessible
        clean_href = urldefrag(href).url # Remove fragments
        head_response = self._fetch_url(clean_href, 'HEAD')
        if head_response and head_response.status_code == 200:
            self.report["pages_with_valid_canonical_target"] += 1
            print_status("Canonical target accessibility", "PASS")
        else:
            status = head_response.status_code if head_response else 'Unreachable'
            self.report["issues"].append(f"Canonical URL '{href}' is not accessible (Status: {status}) on page: {url}")
            print_status("Canonical target accessibility", "FAIL")

    def run_analysis(self):
        """Main execution logic."""
        print_header("ARI Sub-Pillar 1.3: Canonicalization & Source Singularity")

        self.get_urls_from_sitemap()
        if not self.urls_to_check:
            self.urls_to_check.append(self.base_url)

        print_subheader(f"Analyzing up to {self.max_pages_to_check} pages")
        while self.urls_to_check and len(self.checked_urls) < self.max_pages_to_check:
            url = self.urls_to_check.popleft()
            if url in self.checked_urls:
                continue

            self.checked_urls.add(url)
            self.analyze_page(url)
            time.sleep(0.1)

        self._generate_final_report()
        self._print_final_report()

    def _generate_final_report(self):
        """Calculate final score and populate recommendations."""
        if self.report["pages_checked"] == 0:
            self.report["status"] = "Critical Failure"
            self.report["score"] = 0
            self.report["recommendations"].append("Could not fetch or analyze any pages from the target URL.")
            return

        # Calculate percentages
        p_canonical = self.report["pages_with_canonical"] / self.report["pages_checked"]
        p_absolute = self.report["pages_with_absolute_canonical"] / self.report["pages_with_canonical"] if self.report["pages_with_canonical"] > 0 else 1
        p_valid_target = self.report["pages_with_valid_canonical_target"] / self.report["pages_with_canonical"] if self.report["pages_with_canonical"] > 0 else 1

        # Scoring: 50% for presence, 25% for being absolute, 25% for being valid.
        score = (p_canonical * 50) + (p_canonical * p_absolute * 25) + (p_canonical * p_valid_target * 25)
        self.report["score"] = int(score)

        if score >= 90: self.report["status"] = "Excellent"
        elif score >= 70: self.report["status"] = "Good"
        elif score >= 40: self.report["status"] = "Needs Improvement"
        else: self.report["status"] = "Poor"

        # Recommendations
        if p_canonical < 1.0:
            self.report["recommendations"].append("Implement <link rel='canonical'> tags on all indexable pages.")
        if p_absolute < 1.0:
            self.report["recommendations"].append("Ensure all canonical tag href attributes use absolute URLs, not relative paths.")
        if p_valid_target < 1.0:
            self.report["recommendations"].append("Audit canonical URLs that are broken (e.g., 404s) or redirect, and point them to valid, final destinations.")
        if score < 70:
             self.report["recommendations"].append("Audit for duplicate content across different URL structures (e.g., www vs. non-www, http vs. https).")


    def _print_final_report(self):
        """Prints the final formatted report."""
        print_header("Final Assessment Report")
        print_status("Overall Status", self.report['status'])
        print_status("ARI Score (out of 100)", self.report['score'])

        print_subheader("Summary Statistics")
        print(f"Pages Analyzed: {self.report['pages_checked']}")
        if self.report['pages_checked'] > 0:
            p_canonical = (self.report['pages_with_canonical'] / self.report['pages_checked']) * 100
            print(f"Pages with a Canonical Tag: {self.report['pages_with_canonical']}/{self.report['pages_checked']} ({p_canonical:.1f}%)")
        if self.report['pages_with_canonical'] > 0:
            p_absolute = (self.report['pages_with_absolute_canonical'] / self.report['pages_with_canonical']) * 100
            p_valid = (self.report['pages_with_valid_canonical_target'] / self.report['pages_with_canonical']) * 100
            print(f"Absolute Canonical URLs: {self.report['pages_with_absolute_canonical']}/{self.report['pages_with_canonical']} ({p_absolute:.1f}%)")
            print(f"Accessible Canonical Targets: {self.report['pages_with_valid_canonical_target']}/{self.report['pages_with_canonical']} ({p_valid:.1f}%)")

        if self.report["issues"]:
            print_subheader("Detected Issues")
            for issue in self.report["issues"][:5]: # Show top 5 issues
                print(f"  - {issue}")

        if self.report["recommendations"]:
            print_subheader("Recommendations (Based on ARI v10.0)")
            for rec in self.report["recommendations"]:
                print_recommendation(rec)

