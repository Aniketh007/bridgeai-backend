from .schema_org import check_schema_org_depth
from .data_cleanliness import check_data_payload_cleanliness
from .semantic_html import check_semantic_html_fidelity
from .heading_hierarchy import check_heading_hierarchy
from .content_formatting import check_content_formatting
from .multimodal_annotation import check_multimodal_annotation
from .data_feed import check_data_feed_availability
from .internal_linking import check_internal_linking
from .logical_flow import check_logical_content_flow
from utils.featcher import fetch_html_selenium

__all__ = [
    "check_schema_org_depth",
    "check_data_payload_cleanliness",
    "check_semantic_html_fidelity",
    "check_heading_hierarchy",
    "check_content_formatting",
    "check_multimodal_annotation",
    "check_data_feed_availability",
    "check_internal_linking",
    "check_logical_content_flow",
]

class SemanticAuditor:
    """
    Orchestrates semantic checks for web content.
    """

    def __init__(self, base_url: str, timeout: float = 15.0) -> None:
        self.base_url = base_url
        self.timeout = timeout

    def run_all(self) -> dict:
        """
        Execute all semantic checks, aggregate results, and return a summary report.
        """
        results = {}
        recommendations = []
        overall_score = 0
        overall_status = 'Not Assessed'

        # Map check functions to their keys
        check_map = {
            'schema_org_depth': check_schema_org_depth,
            'data_payload_cleanliness': check_data_payload_cleanliness,
            'semantic_html_fidelity': check_semantic_html_fidelity,
            'heading_hierarchy': check_heading_hierarchy,
            'content_formatting': check_content_formatting,
            'multimodal_annotation': check_multimodal_annotation,
            'data_feed_availability': check_data_feed_availability,
            'internal_linking': check_internal_linking,
            'logical_content_flow': check_logical_content_flow,
        }

        try:

            html = fetch_html_selenium(self.base_url)

            for key, check_func in check_map.items():
                try:
                    score, issues, recommendations = check_func(self.base_url, html)
                    results[key] = {'score': score, 'issues': issues, 'recommendations': recommendations}
                    overall_score += score
                    recommendations.extend(recommendations)
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