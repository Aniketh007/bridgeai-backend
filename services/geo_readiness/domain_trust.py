# Pillar 1, Sub-pillar 6
# See Bridge.ipynb cell 6 for logic
# ...existing code...
import requests
import ssl
import socket
from datetime import datetime
from urllib.parse import urlparse
try:
    import dns.resolver
except ImportError:
    print("Please install dnspython: pip install dnspython")

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

class DomainTrustAnalyzer:
    """
    Analyzes a domain's security and trust signals based on ARI v10.0 Pillar 1, Sub-pillar 6.
    """
    def __init__(self, target_url):
        if not target_url.startswith('http'):
            target_url = 'https://' + target_url
        self.url = target_url
        self.parsed_url = urlparse(self.url)
        self.domain = self.parsed_url.netloc
        self.report = {
            "checks": {}, "recommendations": [], "score": 0, "status": "Not Assessed"
        }
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'ARI-DomainTrust-Analyzer/1.0'})

    def check_https_enforcement(self):
        print_subheader("1. HTTPS Enforcement")
        # Check 1: Strict Redirect from HTTP to HTTPS
        http_url = self.url.replace('https://', 'http://')
        try:
            res = self.session.head(http_url, allow_redirects=True, timeout=5)
            if res.url.startswith('https://'):
                self.report["checks"]["http_redirect"] = True
                print_status("HTTP requests redirect to HTTPS", "PASS")
            else:
                self.report["checks"]["http_redirect"] = False
                print_status("HTTP does not redirect to HTTPS", "FAIL")
                self.report["recommendations"].append("Implement a server-side 301 redirect from HTTP to all pages.")
        except requests.exceptions.RequestException:
            self.report["checks"]["http_redirect"] = True # If HTTP fails to connect, it's effectively enforced
            print_status("HTTP port is not open (good)", "PASS")

        # Check 2: SSL Certificate Validity
        try:
            # The request itself will fail on bad certs, but we can get expiry info manually
            context = ssl.create_default_context()
            with socket.create_connection((self.domain, 443)) as sock:
                with context.wrap_socket(sock, server_hostname=self.domain) as ssock:
                    cert = ssock.getpeercert()
            self.report["checks"]["ssl_valid"] = True
            print_status("SSL Certificate is trusted", "PASS")

            # Check Expiry
            expiry_date = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
            days_left = (expiry_date - datetime.utcnow()).days
            if days_left < 14:
                 print_status(f"Certificate expires in {days_left} days", "WARN")
                 self.report["recommendations"].append("Renew the SSL certificate soon.")
            else:
                 print_status(f"Certificate is valid for {days_left} more days", "PASS")

        except (ssl.SSLError, socket.gaierror, ConnectionRefusedError) as e:
            self.report["checks"]["ssl_valid"] = False
            print_status(f"SSL Certificate is invalid or untrusted: {e}", "FAIL")
            self.report["recommendations"].append("Install a valid, trusted SSL certificate from a known CA.")

    def check_security_headers(self):
        print_subheader("2. Security Headers")
        try:
            res = self.session.get(self.url, timeout=5)
            headers = res.headers

            # Check for HSTS
            if 'Strict-Transport-Security' in headers:
                self.report["checks"]["hsts_header"] = True
                print_status("Strict-Transport-Security (HSTS) header", "PASS")
            else:
                self.report["checks"]["hsts_header"] = False
                print_status("Strict-Transport-Security (HSTS) header", "FAIL")
                self.report["recommendations"].append("Implement the HSTS header to prevent downgrade attacks.")

            # Check for CSP
            if 'Content-Security-Policy' in headers:
                self.report["checks"]["csp_header"] = True
                print_status("Content-Security-Policy (CSP) header", "PASS")
            else:
                self.report["checks"]["csp_header"] = False
                print_status("Content-Security-Policy (CSP) header", "WARN")
                self.report["recommendations"].append("Implement a CSP to mitigate XSS and other injection attacks.")

            # Check for X-Content-Type-Options
            if headers.get('X-Content-Type-Options', '').lower() == 'nosniff':
                self.report["checks"]["x_content_type_header"] = True
                print_status("X-Content-Type-Options header is 'nosniff'", "PASS")
            else:
                self.report["checks"]["x_content_type_header"] = False
                print_status("X-Content-Type-Options header", "WARN")
                self.report["recommendations"].append("Set the X-Content-Type-Options header to 'nosniff'.")

        except requests.exceptions.RequestException:
             print_status("Could not fetch headers from the domain", "FAIL")

    def check_domain_identity_records(self):
        print_subheader("3. Domain Identity & Trust (DNS Records)")
        base_domain = self.domain.replace('www.', '')
        # Check for CAA
        try:
            dns.resolver.resolve(base_domain, 'CAA')
            self.report["checks"]["caa_record"] = True
            print_status("Certification Authority Authorization (CAA) record", "PASS")
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            self.report["checks"]["caa_record"] = False
            print_status("Certification Authority Authorization (CAA) record", "WARN")
            self.report["recommendations"].append("Add a CAA DNS record to specify which CAs can issue certificates.")

        # Check for DMARC
        try:
            dns.resolver.resolve(f'_dmarc.{base_domain}', 'TXT')
            self.report["checks"]["dmarc_record"] = True
            print_status("DMARC email authentication record", "PASS")
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            self.report["checks"]["dmarc_record"] = False
            print_status("DMARC email authentication record", "WARN")
            self.report["recommendations"].append("Add a DMARC DNS record to prevent email spoofing and phishing.")

    def run_analysis(self):
        print_header("ARI Sub-Pillar 1.6: Domain Security & Identity Trust")
        self.check_https_enforcement()
        self.check_security_headers()
        self.check_domain_identity_records()
        self._generate_final_report()
        self._print_final_report()

    def _generate_final_report(self):
        score = 0
        if self.report["checks"].get("http_redirect"): score += 20
        if self.report["checks"].get("ssl_valid"): score += 20
        if self.report["checks"].get("hsts_header"): score += 15
        if self.report["checks"].get("csp_header"): score += 10
        if self.report["checks"].get("x_content_type_header"): score += 5
        if self.report["checks"].get("caa_record"): score += 15
        if self.report["checks"].get("dmarc_record"): score += 5

        self.report["score"] = min(100, score)

        if self.report["score"] >= 90: self.report["status"] = "Excellent"
        elif self.report["score"] >= 70: self.report["status"] = "Good"
        elif self.report["score"] >= 40: self.report["status"] = "Needs Improvement"
        else: self.report["status"] = "Poor"

    def _print_final_report(self):
        print_header("Final Assessment Report")
        print_status("Overall Status", self.report['status'])
        print_status("ARI Score (out of 100)", self.report['score'])

        if self.report["recommendations"]:
            print_subheader("Recommendations")
            for rec in self.report["recommendations"]:
                print_recommendation(rec)
