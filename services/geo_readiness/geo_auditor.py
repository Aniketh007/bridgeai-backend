from .sitemap import SitemapAnalyzer
from .robots_txt import RobotsTxtAnalyzer
from .canonicalization import CanonicalizationAnalyzer
from .ai_policy import Advanced_AI_Policy_Analyzer
from .agents_json import AgentsJsonAnalyzer
from .domain_trust import DomainTrustAnalyzer
from .authorship import AuthorshipAnalyzer
from .economic_model import EconomicModelAnalyzer
from .data_licensing import DataLicensingAnalyzer
from .metadata import MetadataAnalyzer

__all__ = [
    'SitemapAnalyzer',
    'RobotsTxtAnalyzer',
    'CanonicalizationAnalyzer',
    'Advanced_AI_Policy_Analyzer',
    'AgentsJsonAnalyzer',
    'DomainTrustAnalyzer',
    'AuthorshipAnalyzer',
    'EconomicModelAnalyzer',
    'DataLicensingAnalyzer',
    'MetadataAnalyzer',
    'GeoReadinessAnalyzer'
]


class GeoReadinessAnalyzer:
    """
    Runs a set of analyzers for GEO Readiness and provides an aggregated report.

    Attributes:
        base_url (str): URL to analyze
        max_pages (int): Max pages for canonicalization
        weights (dict): Sub-pillar weights
        results (dict): Raw analyzer results
        overall_score (int): Weighted overall score
        overall_status (str): Status based on overall_score
        recommendations (list): Aggregated recommendations
    """

    DEFAULT_WEIGHTS = {
        'sitemap': 0.15,
        'robots_txt': 0.12,
        'canonicalization': 0.10,
        'ai_policy': 0.08,
        'agents_json': 0.08,
        'domain_trust': 0.15,
        'authorship': 0.08,
        'economic_model': 0.06,
        'data_licensing': 0.08,
        'metadata': 0.10,
    }

    def __init__(self, base_url, max_pages=25, weights=None):
        self.base_url = base_url
        self.max_pages = max_pages
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
        self.results = {}
        self.overall_score = 0
        self.overall_status = 'Not Assessed'
        self.recommendations = []

    def run_all(self):
        """Execute all analyzers and compute aggregated results."""
        analyzers = {
            'sitemap': SitemapAnalyzer,
            'robots_txt': RobotsTxtAnalyzer,
            'canonicalization': (
                lambda url: CanonicalizationAnalyzer(url, self.max_pages)
            ),
            'ai_policy': Advanced_AI_Policy_Analyzer,
            'agents_json': AgentsJsonAnalyzer,
            'domain_trust': DomainTrustAnalyzer,
            'authorship': AuthorshipAnalyzer,
            'economic_model': EconomicModelAnalyzer,
            'data_licensing': DataLicensingAnalyzer,
            'metadata': MetadataAnalyzer,
        }

        for key, analyzer_cls in analyzers.items():
            try:
                analyzer = analyzer_cls(self.base_url)
                analyzer.run_analysis()
                report = getattr(analyzer, 'report', {})
            except Exception as e:
                report = {'score': 0, 'status': 'error', 'error': str(e)}

            self.results[key] = report
            self._collect_recommendations(key, report)

        self._compute_overall()
        return self.get_summary()

    def _collect_recommendations(self, key, report):
        recs = report.get('recommendations', [])
        for rec in recs[:2]:
            self.recommendations.append(f"[{key}] {rec}")

    def _compute_overall(self):
        total_weight = sum(self.weights.values())
        if total_weight <= 0:
            self.overall_score = 0
            self.overall_status = 'Not Assessed'
            return

        weighted = sum(
            self.results.get(k, {}).get('score', 0) * w
            for k, w in self.weights.items()
        )
        self.overall_score = round(weighted / total_weight)

        if self.overall_score >= 90:
            self.overall_status = 'Excellent'
        elif self.overall_score >= 75:
            self.overall_status = 'Good'
        elif self.overall_score >= 50:
            self.overall_status = 'Needs Improvement'
        elif self.overall_score >= 25:
            self.overall_status = 'Poor'
        else:
            self.overall_status = 'Critical'

    def get_summary(self):
        """Return a concise report summary."""
        return {
            'overall_score': self.overall_score,
            'overall_status': self.overall_status,
            'sub_pillars': {
                k: {
                    'score': v.get('score', 0),
                    'status': v.get('status', '')
                }
                for k, v in self.results.items()
            },
            'top_recommendations': self.recommendations[:5]
        }
