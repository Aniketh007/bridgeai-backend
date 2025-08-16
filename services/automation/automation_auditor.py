# === services/automation_resilience/__init__.py ===
from .captcha import check_captcha_presence
from .form_predictability import check_form_predictability
from .url_navigability import check_url_navigability
from .session_recovery import check_session_state_recovery
from .feedback import check_clear_action_feedback
from .graceful_degradation import check_graceful_degradation
from .anti_automation import check_anti_automation_absence
from .mfa_handling import check_mfa_handling
from .encapsulation import check_encapsulation_analysis
from .intrusive_elements import check_intrusive_elements
from utils.featcher import fetch_html_selenium

__all__ = [
    "check_captcha_presence",
    "check_form_predictability",
    "check_url_navigability",
    "check_session_state_recovery",
    "check_clear_action_feedback",
    "check_graceful_degradation",
    "check_anti_automation_absence",
    "check_mfa_handling",
    "check_encapsulation_analysis",
    "check_intrusive_elements",
]

class AutomationAuditor:
    """
    Orchestrates automation resilience checks for web content.
    """

    def __init__(self, base_url: str, timeout: float = 15.0) -> None:
        self.base_url = base_url
        self.timeout = timeout

    def run_all(self) -> dict:
        """
        Execute all automation resilience checks, aggregate results, and return a summary report.
        """
        results = {}
        recommendations = []
        overall_score = 0
        overall_status = 'Not Assessed'

        # Map check functions to their keys
        check_map = {
            'captcha_presence': check_captcha_presence,
            'form_predictability': check_form_predictability,
            'url_navigability': check_url_navigability,
            'session_state_recovery': check_session_state_recovery,
            'clear_action_feedback': check_clear_action_feedback,
            'graceful_degradation': check_graceful_degradation,
            'anti_automation_absence': check_anti_automation_absence,
            'mfa_handling': check_mfa_handling,
            'encapsulation_analysis': check_encapsulation_analysis,
            'intrusive_elements': check_intrusive_elements,
        }

        try:
            html = fetch_html_selenium(self.base_url)

            for key, check_func in check_map.items():
                try:
                    score, issues, recs = check_func(self.base_url, html)
                    results[key] = {'score': score, 'issues': issues, 'recommendations': recs}
                    overall_score += score
                    recommendations.extend(recs)
                except Exception as ex:
                    results[key] = {'score': 0, 'explanation': str(ex), 'recommendations': []}

            # Determine overall status based on score
            if overall_score >= 90:
                overall_status = 'Excellent'
            elif overall_score >= 80:
                overall_status = 'Good'
            elif overall_score >= 70:
                overall_status = 'Fair'
            elif overall_score >= 60:
                overall_status = 'Poor'
            else:
                overall_status = 'Critical'

        except Exception as e:
            # If HTML fetching fails
            overall_status = 'Failed'
            recommendations.append(f"Failed to fetch HTML: {str(e)}")
            
            # Set all checks as failed
            for key in check_map.keys():
                results[key] = {
                    'score': 0,
                    'issues': [f"Could not perform check due to HTML fetch failure: {str(e)}"],
                    'recommendations': ["Ensure the URL is accessible and try again"]
                }

        return {
            'overall_score': round(overall_score, 2),
            'overall_status': overall_status,
            'sub_pillars': {
                k: {
                    'score': v.get('score', 0),
                    'issues': v.get('issues', []),
                }
                for k, v in results.items()
            },
            'recommendations': recommendations[:5],
        }