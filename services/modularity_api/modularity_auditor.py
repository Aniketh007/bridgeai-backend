from .api_controls import ApiControlsAnalyzer
from .api_discoverability import ApiDiscoverabilityAnalyzer
from .api_documentation import ApiDocumentationAnalyzer
from .api_modularity import ApiModularityAnalyzer as CoreModularityAnalyzer
from .api_version import ApiVersioningAnalyzer
from .auth_analyzer import AuthAnalyzer
from .business_process import BusinessProcessApiAnalyzer
from .developer_experience import DeveloperExperienceAnalyzer
from .event_driven import EventDrivenArchitectureAnalyzer
from .idempotency import IdempotencyAnalyzer

__all__ = [
    'ApiControlsAnalyzer',
    'ApiDiscoverabilityAnalyzer',
    'ApiDocumentationAnalyzer',
    'CoreModularityAnalyzer',
    'ApiVersioningAnalyzer',
    'AuthAnalyzer',
    'BusinessProcessApiAnalyzer',
    'DeveloperExperienceAnalyzer',
    'EventDrivenArchitectureAnalyzer',
    'IdempotencyAnalyzer',
    'ModularityApiAnalyzer'
]

class ModularityApiAnalyzer:
    """
    Aggregates a suite of API analyzers and computes a weighted overall report.
    """

    DEFAULT_WEIGHTS = {
        'api_controls': 0.12,
        'api_discoverability': 0.15,
        'api_documentation': 0.15,
        'api_modularity': 0.12,
        'api_versioning': 0.10,
        'auth_analyzer': 0.10,
        'business_process': 0.08,
        'developer_experience': 0.08,
        'event_driven': 0.05,
        'idempotency': 0.05,
    }

    def __init__(self, base_url, weights=None):
        self.base_url = base_url
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
        self.results = {}
        self.recommendations = []
        self.overall_score = 0
        self.overall_status = 'Not Assessed'

    def run_all(self):
        """Run every analyzer, compute weighted overall score, and return summary."""
        analyzer_map = {
            'api_controls': ApiControlsAnalyzer,
            'api_discoverability': ApiDiscoverabilityAnalyzer,
            'api_documentation': ApiDocumentationAnalyzer,
            'api_modularity': CoreModularityAnalyzer,
            'api_versioning': ApiVersioningAnalyzer,
            'auth_analyzer': AuthAnalyzer,
            'business_process': BusinessProcessApiAnalyzer,
            'developer_experience': DeveloperExperienceAnalyzer,
            'event_driven': EventDrivenArchitectureAnalyzer,
            'idempotency': IdempotencyAnalyzer,
        }

        for key, cls in analyzer_map.items():
            try:
                analyzer = cls(self.base_url)
                analyzer.run_analysis()
                report = getattr(analyzer, 'report', {})
            except Exception as ex:
                report = {'score': 0, 'status': 'error', 'error': str(ex)}

            self.results[key] = report
            for rec in report.get('recommendations', [])[:2]:
                self.recommendations.append(f"[{key}] {rec}")

        total_weight = sum(self.weights.values())
        weighted_sum = sum(
            self.results[k].get('score', 0) * w
            for k, w in self.weights.items()
        ) if total_weight > 0 else 0

        self.overall_score = round(weighted_sum / total_weight) if total_weight > 0 else 0
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

        return {
            'overall_score': self.overall_score,
            'overall_status': self.overall_status,
            'sub_pillars': {
                key: {'score': rpt.get('score', 0), 'status': rpt.get('status', '')}
                for key, rpt in self.results.items()
            },
            'top_recommendations': self.recommendations[:5]
        }
