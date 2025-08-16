import google.generativeai as genai
from .agent_identification import AgentIdentification
from .conversational_bot import ConversationalBot
from .error_recovery import ErrorRecovery

__all__ = [
    'AgentIdentification',
    'ConversationalBot',
    'ErrorRecovery',
    'AxoAuditor'
]

class AxoAuditor:
    """
    Orchestrates Agent Identification, Conversational Bot Assistance,
    and Error Recovery analyzers to produce a unified audit report.
    """

    DEFAULT_WEIGHTS = {
        'agent_identification': 0.33,
        'conversational_bot': 0.33,
        'error_recovery': 0.34,
    }

    def __init__(self, base_url: str, model, weights: dict = {}, timeout: float = 15.0):
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
        self.results = {}
        self.recommendations = []
        self.overall_score = 0
        self.overall_status = 'Not Assessed'

    def run_all(self) -> dict:
        """
        Execute all three sub-pillar analyzers, aggregate scores,
        determine overall status, and return a summary report.
        """
        # Map analyzer keys to classes and init args
        analyzer_map = {
            'agent_identification': AgentIdentification,
            'conversational_bot': ConversationalBot,
            'error_recovery': ErrorRecovery,
        }

        for key, analyzer_cls in analyzer_map.items():
            try:
                analyzer = analyzer_cls(self.base_url, self.model, self.timeout)
                report = analyzer.run_and_analyze()
            except Exception as ex:
                report = {'score': 0, 'explanation': str(ex), 'recommendations': []}

            self.results[key] = report
            for rec in report.get('recommendations', [])[:2]:
                self.recommendations.append(f"[{key}] {rec}")

        # Compute weighted overall score
        total_weight = sum(self.weights.values())
        weighted_sum = sum(
            self.results[k].get('score', 0) * w
            for k, w in self.weights.items()
        ) if total_weight > 0 else 0

        self.overall_score = round(weighted_sum / total_weight) if total_weight > 0 else 0

        # Determine status
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

        # Build summary
        return {
            'overall_score': self.overall_score,
            'overall_status': self.overall_status,
            'sub_pillars': {
                key: {
                    'score': rpt.get('score', 0),
                    'explanation': rpt.get('explanation', ''),
                }
                for key, rpt in self.results.items()
            },
            'top_recommendations': self.recommendations[:5]
        }