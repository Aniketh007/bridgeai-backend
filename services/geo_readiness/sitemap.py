# Pillar 1, Sub-pillar 1
# See Bridge.ipynb cell 1 for logic
# ...existing code...
import requests
import xml.etree.ElementTree as ET
import gzip
from io import BytesIO
from urllib.parse import urlparse, urljoin
from datetime import datetime, timezone

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
    print(f"{message:<45} [{status}]")

def print_recommendation(rec):
    print(f"  - {rec}")

class SitemapAnalyzer:
    """
    Analyzes a website's sitemap health and freshness based on ARI v10.0 Pillar 1, Sub-pillar 1.
    """
    def __init__(self, base_url):
        self.base_url = self._format_base_url(base_url)
        self.sitemaps_to_process = []
        self.processed_sitemaps = set()
        self.report = {
            "sitemap_locations": [],
            "total_urls": 0,
            "urls_with_lastmod": 0,
            "error_log": [],
            "recommendations": [],
            "score": 0,
            "status": "Critical Failure"
        }
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ARI-Sitemap-Analyzer/1.0'
        })

    def _format_base_url(self, url):
        """Ensures the URL has a scheme and is just the base domain."""
        parsed = urlparse(url)
        if not parsed.scheme:
            url = "https://" + url
            parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def _fetch_url(self, url):
        """Fetches a URL, handles redirects and exceptions."""
        try:
            response = self.session.get(url, timeout=15, allow_redirects=True)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            self.report["error_log"].append(f"Failed to fetch {url}: {e}")
            return None

    def _get_sitemap_content(self, response):
        """Decompresses content if gzipped, returns text."""
        if response.url.endswith('.gz') or response.headers.get('Content-Type') == 'application/gzip':
            try:
                with gzip.GzipFile(fileobj=BytesIO(response.content)) as gz_file:
                    return gz_file.read().decode('utf-8')
            except Exception as e:
                self.report["error_log"].append(f"Failed to decompress gzipped sitemap {response.url}: {e}")
                return None
        return response.text

    def find_sitemaps_from_robots(self):
        """Parses robots.txt to find sitemap locations."""
        print_status(f"Checking robots.txt at {urljoin(self.base_url, 'robots.txt')}", "IN PROGRESS")
        robots_url = urljoin(self.base_url, 'robots.txt')
        response = self._fetch_url(robots_url)

        if response:
            lines = response.text.splitlines()
            found = False
            for line in lines:
                if line.lower().startswith('sitemap:'):
                    sitemap_url = line.split(':', 1)[1].strip()
                    self.sitemaps_to_process.append(sitemap_url)
                    found = True
            if found:
                 print_status(f"Found {len(self.sitemaps_to_process)} sitemap(s) in robots.txt", "OK")
            else:
                 print_status("No sitemap directive in robots.txt", "WARNING")
        else:
             print_status("Could not fetch robots.txt", "WARNING")

    def _parse_sitemap(self, xml_content, sitemap_url):
        """Parses XML content to find URLs or other sitemaps."""
        try:
            root = ET.fromstring(xml_content.encode('utf-8'))
            namespace = root.tag.split('}')[0][1:] if '}' in root.tag else ''

            # It's a sitemap index file
            if root.tag.endswith('sitemapindex'):
                sitemaps = root.findall(f'{{{namespace}}}sitemap')
                for sitemap in sitemaps:
                    loc = sitemap.find(f'{{{namespace}}}loc')
                    if loc is not None:
                        new_sitemap_url = loc.text.strip()
                        if new_sitemap_url not in self.processed_sitemaps:
                            self.sitemaps_to_process.append(new_sitemap_url)
                print_status(f"Parsed sitemap index: Found {len(sitemaps)} more sitemaps", "INFO")

            # It's a URL set
            elif root.tag.endswith('urlset'):
                urls = root.findall(f'{{{namespace}}}url')
                self.report["total_urls"] += len(urls)
                for url in urls:
                    lastmod = url.find(f'{{{namespace}}}lastmod')
                    if lastmod is not None and lastmod.text:
                        self.report["urls_with_lastmod"] += 1
                print_status(f"Parsed URL set: Found {len(urls)} URLs", "INFO")

            else:
                 self.report["error_log"].append(f"Unknown root tag '{root.tag}' in {sitemap_url}")

        except ET.ParseError as e:
            self.report["error_log"].append(f"XML Parse Error in {sitemap_url}: {e}")


    def run_analysis(self):
        """Main execution logic."""
        print_header("ARI Sub-Pillar 1.1: Sitemap Health & Freshness")

        # 1. Discover sitemaps
        self.find_sitemaps_from_robots()
        if not self.sitemaps_to_process:
            print_status("Falling back to default sitemap.xml location", "INFO")
            self.sitemaps_to_process.append(urljoin(self.base_url, 'sitemap.xml'))

        # 2. Process all found sitemaps (including those discovered recursively)
        print_subheader("Processing Sitemaps")
        while self.sitemaps_to_process:
            sitemap_url = self.sitemaps_to_process.pop(0)
            if sitemap_url in self.processed_sitemaps:
                continue

            self.processed_sitemaps.add(sitemap_url)
            print(f"\n-> Fetching: {sitemap_url}")
            response = self._fetch_url(sitemap_url)

            if response:
                self.report["sitemap_locations"].append(sitemap_url)
                xml_content = self._get_sitemap_content(response)
                if xml_content:
                    self._parse_sitemap(xml_content, response.url)
                else:
                    print_status("Failed to get sitemap content", "ERROR")
            else:
                print_status(f"Sitemap not found or inaccessible at {sitemap_url}", "ERROR")

        # 3. Generate Score and Recommendations
        self._generate_final_report()

        # 4. Print Report
        self._print_final_report()

    def _generate_final_report(self):
        """Calculate final score and populate recommendations."""
        # Critical Failures (BLOCKER)
        if not self.report["sitemap_locations"]:
            self.report["status"] = "Critical Failure"
            self.report["score"] = 0
            self.report["recommendations"].append("Generate sitemap.xml using automated crawling tools as no sitemap was found.")
            self.report["recommendations"].append("Submit the sitemap to Google Search Console and Bing Webmaster Tools.")
            return

        if self.report["error_log"] and any("XML Parse Error" in e for e in self.report["error_log"]):
            self.report["status"] = "Critical Failure"
            self.report["score"] = 10
            self.report["recommendations"].append("Sitemap is malformed. Validate XML structure and correct parsing errors.")

        if self.report["total_urls"] == 0:
            self.report["status"] = "Critical Failure"
            self.report["score"] = 15
            self.report["recommendations"].append("Sitemap is empty or could not be parsed correctly. Ensure it contains URL entries.")
            return

        # Scoring Logic
        # Base score for having a valid sitemap
        score = 50

        lastmod_percentage = self.report["urls_with_lastmod"] / self.report["total_urls"]
        score += 50 * lastmod_percentage # Up to 50 points for lastmod coverage

        self.report["score"] = int(score)

        if self.report["score"] >= 95:
            self.report["status"] = "Excellent"
        elif self.report["score"] >= 70:
            self.report["status"] = "Good"
        elif self.report["score"] >= 40:
            self.report["status"] = "Needs Improvement"
        else:
            self.report["status"] = "Poor"

        # Recommendations for low scores
        if lastmod_percentage < 0.9:
            self.report["recommendations"].append("Improve coverage of <lastmod> timestamps for all URLs to signal content freshness.")
        if lastmod_percentage < 1.0:
            self.report["recommendations"].append("Consider implementing automatic sitemap updates in a CI/CD pipeline to keep timestamps current.")

    def _print_final_report(self):
        """Prints the final formatted report."""
        print_header("Final Assessment Report")
        print_status("Overall Status", self.report['status'])
        print_status("ARI Score (out of 100)", self.report['score'])

        print_subheader("Summary")
        print(f"Discovered and processed {len(self.report['sitemap_locations'])} sitemap file(s).")
        print(f"Found a total of {self.report['total_urls']} URLs.")
        if self.report['total_urls'] > 0:
            lastmod_percent = (self.report['urls_with_lastmod'] / self.report['total_urls']) * 100
            print(f"{self.report['urls_with_lastmod']} URLs have a <lastmod> timestamp ({lastmod_percent:.2f}% coverage).")

        if self.report["recommendations"]:
            print_subheader("Recommendations (Based on ARI v10.0)")
            for rec in self.report["recommendations"]:
                print_recommendation(rec)

        if self.report["error_log"]:
            print_subheader("Error Log")
            for err in self.report["error_log"]:
                print(f"  - {err}")
