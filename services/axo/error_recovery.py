import re
import asyncio
import logging
import json
from urllib.parse import urljoin
import httpx


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ErrorRecovery:
    """
    Sub-pillar 2: Error Recovery Assistance

    Audits a website's ability to provide actionable assistance to an AI agent
    when an error occurs, enabling the agent to recover and continue its task.
    """
    def __init__(self, base_url: str, model, timeout: float = 15.0):
        self.base_url = base_url
        self.model = model
        self.timeout = timeout

    async def _probe(self, client: httpx.AsyncClient, url: str, method: str = "GET", headers: dict = {}, data: dict = {}) -> dict:
        """
        Performs a single, safe, asynchronous request.
        """
        try:
            if method.upper() == "POST":
                response = await client.post(url, headers=headers, json=data, timeout=self.timeout, follow_redirects=True)
            else:
                response = await client.get(url, headers=headers, timeout=self.timeout, follow_redirects=True)

            logging.info(f"Response from {url}: {response.status_code}")

            return {
                "status_code": response.status_code,
                "content_length": len(response.content),
                "content_type": response.headers.get("content-type", "unknown"),
                "headers": dict(response.headers),
                "final_url": str(response.url),
                "content_snippet": response.text[:500]  # Snippet for behavioral analysis
            }

        except httpx.RequestError as e:
            logging.warning(f"Request failed for {url}: {e}")
            return {"error": str(e)}
        
    async def gather_evidence(self) -> dict:
        """
        Gathers evidence by intentionally triggering client-side and server-side errors.
        """
        logging.info("Gathering error recovery evidence...")
        evidence = {}

        async with httpx.AsyncClient() as client:
            # 1. client side errors: 4xx errors
            logging.info("Gathering client-side error evidence...")
            error_url = urljoin(self.base_url, "/api/register")
            invalid_data = {"email": "invalid-email", "password": "short"}
            evidence["client_side_errors"] = await self._probe(
                client, error_url, "POST", headers={"Content-Type": "application/json"}, data=invalid_data
            )

            # 2. server side errors: 5xx errors
            logging.info("Gathering server-side error evidence...")
            rate_limit_url = urljoin(self.base_url, "/api/users")
            # Send a burst of requests to try and trigger a rate limit
            burst_tasks = [self._probe(client, rate_limit_url) for _ in range(10)]
            burst_results = await asyncio.gather(*burst_tasks)
            
            # Find the first rate-limit or server error response
            rate_limit_response = None
            for resp in burst_results:
                if resp.get("status_code") in [429, 503]:
                    rate_limit_response = resp
                    break
            
            evidence['rate_limit_attempt'] = rate_limit_response if rate_limit_response else {"status_code": 200, "body": "No rate-limit triggered."}

        logging.info("Evidence gathering complete.")
        return evidence
    
    def run_and_analyze(self) -> dict:
        """
        Gathers error evidence and sends it to the LLM for a final analysis.
        """

        evidence = asyncio.run(self.gather_evidence())
        logging.info("Sending evidence to LLM for analysis...")

        prompt = f"""
        Act as a senior API design and resilience engineer. Your task is to audit a website's "Error Recovery Assistance" for AI agents based on the following evidence.

        **Evidence Collected:**
        ```json
        {json.dumps(evidence, indent=2)}
        ```

        **Analysis Instructions:**
        1. **Client-Side Errors:** Check if error responses contain structured error codes, clear messages, and actionable guidance
        2. **404 Handling:** Evaluate if 404 responses provide helpful navigation or suggestions
        3. **Rate Limiting:** Check for proper Retry-After headers and clear rate limit guidance
        4. **Recovery Guidance:** Assess if errors help agents understand how to fix issues and retry

        **Scoring (0-100):**
        - 0-25: Generic errors, no recovery guidance
        - 26-50: Basic error messages, minimal structure
        - 51-75: Good error structure, some recovery hints
        - 76-100: Excellent structured errors with clear recovery paths

        **Output Format:**
        Provide response as valid JSON only:
        {{"score": <integer>, "explanation": "<analysis>", "recommendations": ["<suggestions>"]}}
        """

        try:
            response = self.model.generate_content(prompt)
            logging.info("LLM analysis complete.")
            
            response_text = response.text
            match = re.search(r"```json\n(.*?)\n```", response_text, re.DOTALL)
            if match:
                response_text = match.group(1)
            return json.loads(response_text)
        
        except Exception as e:  # Handle any exceptions from the LLM call
            logging.error(f"An error occurred during Gemini analysis: {e}")
            logging.debug(f"Raw response was: {response.text if 'response' in locals() else 'No response'}")
            return {"score": 0, "explanation": "Error during analysis. Please check logs."}
