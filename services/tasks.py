from datetime import datetime
import uuid
import json
import re
from typing import Dict, Any
from celery_app import celery_app
from services.axo.axo_auditor import AxoAuditor
from services.automation.automation_auditor import AutomationAuditor
from services.geo_readiness.geo_auditor import GeoReadinessAnalyzer
from services.modularity_api.modularity_auditor import ModularityApiAnalyzer
from services.semantic.semantic_auditor import SemanticAuditor
from utils.featcher import fetch_html_selenium
import google.generativeai as genai

@celery_app.task(bind=True)
def run_audit(self, url: str, api_key: str) -> Dict[str, Any]:
    """
    Run a comprehensive audit based on the provided URL and API key.
    """
    if not url:
        raise ValueError("URL is required")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    reports = {}
    # Pillars in order, mapping to auditor classes
    pillars = [
        ("Agent Experience",   AxoAuditor),
        ("GEO Readiness & Governance", GeoReadinessAnalyzer),
        ("API Readiness",      ModularityApiAnalyzer),
        ("Performance & Reliability", AutomationAuditor),
        ("Structural & Semantic", SemanticAuditor),
    ]
    start = datetime.now()

    for idx, (name, AuditorCls) in enumerate(pillars, start=1):
        # update progress
        self.update_state(
            state="PROGRESS",
            meta={"current": idx, "total": len(pillars), "last_completed": name}
        )

        # run each auditor
        if AuditorCls is AxoAuditor:
            rpt = AuditorCls(base_url=url, model=model).run_all()
        else:
            rpt = AuditorCls(base_url=url).run_all()
        reports[name] = rpt

    end = datetime.now()
    # combine via your aggregate_scans logic
    final = aggregate_scans(
        model,
        reports["Agent Experience"],
        reports["GEO Readiness & Governance"],
        reports["API Readiness"],
        reports["Performance & Reliability"],
        reports["Structural & Semantic"],
    )

    end = datetime.now()
    final["duration_minutes"] = round((end - start).total_seconds() / 60, 2)
    final["assessed_on"] = start.strftime("%Y-%m-%d")

    return final


def aggregate_scans(model, axo_report: dict, geo_report: dict, modular_report: dict, automation_report: dict, semantic_report: dict) -> dict:
    """
    Sends combined reports to LLM for unified formatting and total aggregate scoring.

    Args:
        axo_report: Output of AxoAuditor.run_all()
        geo_report: Output of GeoReadinessAnalyzer.run_all()
        modular_report: Output of ModularityApiAnalyzer.run_all()

    Returns:
        dict: JSON-parsed response from LLM containing 'aggregate_score',
              'formatted_report', and 'recommendations'.
    """
    prompt = """
You are an API & web-intelligence auditor. Given these five JSON reports:

AXO (Agent Experience):
```json
""" + json.dumps(axo_report, indent=2) + """
```


2. GEO Readiness & Governance:
```json
""" + json.dumps(geo_report, indent=2) + """
```

3. API Readiness:
```json
""" + json.dumps(modular_report, indent=2) + """
```

4. Automation (Performance & Reliability):
```json
""" + json.dumps(automation_report, indent=2) + """
```

5. Structural & Semantic:
```json
""" + json.dumps(semantic_report, indent=2) + """
```

Task:
- Calculate an overall combined score (0-100) by averaging the five overall_scores.
- Assign a letter "grade": A (≥90), B (≥80), C (≥70), D (≥60), F (<60)
- Build a "pillars" array of five objects, each with:
    - "name": one of "GEO Readiness & Governance", "Structural & Semantic", "API Readiness", "Agent Experience", "Performance & Reliability".
    - "score": the pillar's numeric score.
    - "weight": assign the weight based on the pillar requirements for the website category, analyze which pillar requires more weightage for the website and provide accordingly.
- Create a "detailed_pillar_analysis" array: for each pillar include:
    - "pillar": same name as above.
    - "sub_components": list of {"name": <sub-component>, "score": <int>, "status": "<status>"}.
- Merge and dedupe all recommendations from the five reports into `"combined_recommendations"` (max 5 items).

Output only this JSON—no markdown or extra text.

Respond with ONLY the JSON, no other text.
"""
    
    response = model.generate_content(prompt)
    # Extract JSON block if wrapped
    text = response.text.strip()
    m = re.search(r"```json\n(.*?)\n```", text, re.DOTALL)
    json_str = m.group(1) if m else text
    return json.loads(json_str)