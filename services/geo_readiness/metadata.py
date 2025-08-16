# Pillar 1, Sub-pillar 10
# See Bridge.ipynb cell 10 for logic
# ...existing code...
import requests
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

class MetadataAnalyzer:
    """
    Analyzes a page for metadata and rich snippet completeness.
    Based on ARI v10.0 Pillar 1, Sub-pillar 10.
    """
    # Define the core meta tags we are looking for
    TAG_CHECKLIST = {
        'title': {'present': False, 'content': '', 'rec': "Add a descriptive <title> tag to the page's <head>."},
        'description': {'present': False, 'content': '', 'rec': "Add a <meta name='description'> tag to summarize the page's content."},
        'og:title': {'present': False, 'content': '', 'rec': "Add an <meta property='og:title'> tag for social sharing."},
        'og:description': {'present': False, 'content': '', 'rec': "Add an <meta property='og:description'> tag for social sharing."},
        'og:image': {'present': False, 'content': '', 'rec': "Add an <meta property='og:image'> tag to specify a sharing image."},
        'og:type': {'present': False, 'content': '', 'rec': "Add an <meta property='og:type'> tag (e.g., 'website' or 'article')."},
        'og:url': {'present': False, 'content': '', 'rec': "Add an <meta property='og:url'> tag with the page's canonical URL."},
        'twitter:card': {'present': False, 'content': '', 'rec': "Add a <meta name='twitter:card'> tag (e.g., 'summary_large_image')."},
    }

    def __init__(self, target_url):
        if not target_url.startswith('http'):
            target_url = 'https' + '://' + target_url
        self.url = target_url
        self.report = {"score": 0, "status": "Not Assessed", "recommendations": []}

    def run_analysis(self):
        print_header("ARI Sub-Pillar 1.10: Metadata & Rich Snippet Completeness")
        try:
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print_status(f"Failed to fetch URL: {e}", "CRITICAL")
            return

        soup = BeautifulSoup(response.text, 'lxml')

        # --- Analyze Tags ---
        # Title Tag
        title_tag = soup.find('title')
        if title_tag and title_tag.string:
            self.TAG_CHECKLIST['title']['present'] = True
            self.TAG_CHECKLIST['title']['content'] = title_tag.string.strip()

        # Meta Tags
        meta_tags = soup.find_all('meta')
        for tag in meta_tags:
            key = tag.get('name') or tag.get('property')
            if key in self.TAG_CHECKLIST:
                content = tag.get('content', '').strip()
                if content:
                    self.TAG_CHECKLIST[key]['present'] = True
                    self.TAG_CHECKLIST[key]['content'] = content

        self._generate_final_report()
        self._print_final_report()

    def _generate_final_report(self):
        found_tags = sum(1 for tag in self.TAG_CHECKLIST.values() if tag['present'])
        total_tags = len(self.TAG_CHECKLIST)
        score = int((found_tags / total_tags) * 100)
        self.report['score'] = score

        if score == 100: self.report["status"] = "Excellent"
        elif score >= 80: self.report["status"] = "Good"
        elif score >= 50: self.report["status"] = "Needs Improvement"
        else: self.report["status"] = "Poor"

        # Populate recommendations for missing tags
        for tag_name, details in self.TAG_CHECKLIST.items():
            if not details['present']:
                self.report['recommendations'].append(details['rec'])

    def _print_final_report(self):
        print_header("Final Assessment Report")
        print_status("Overall Status", self.report['status'])
        print_status("Completeness Score", f"{self.report['score']}%")

        print_subheader("Metadata Checklist")
        for tag_name, details in self.TAG_CHECKLIST.items():
            status = "PASS" if details['present'] else "FAIL"
            content_preview = (details['content'][:70] + '...') if len(details['content']) > 70 else details['content']
            print_status(f"{tag_name}", status)
            if details['present']:
                print(f"  └─ Content: {content_preview}")

        if self.report["recommendations"]:
            print_subheader("Recommendations")
            for rec in self.report["recommendations"]:
                print_recommendation(rec)