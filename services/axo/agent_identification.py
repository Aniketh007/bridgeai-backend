import asyncio
import json
import re
from urllib.parse import urljoin
import httpx
import logging

# --- Basic Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class AgentIdentification:
    """
    Sub-pillar 1: AI Agent Identification (Production Grade)

    Audits a website's agent identification capabilities by gathering evidence
    asynchronously and using an LLM for advanced analysis, scoring, and explanation.
    Combines high-performance probing with intelligent, context-aware analysis.
    """
    def __init__(self, base_url: str, model, timeout: float = 15.0):
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.user_agents = {
            "human_baseline": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "googlebot": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
            "bingbot": "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",
            "gptbot": "Mozilla/5.0 (compatible; GPTBot/1.0; +https://openai.com/gptbot)",
            "claude_bot": "Mozilla/5.0 (compatible; Claude-3/1.0; Anthropic AI Agent)",
            "headless_chrome": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/120.0.0.0 Safari/537.36",
            "human_windows_chrome": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "human_macos_safari": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
            "human_linux_firefox": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:108.0) Gecko/20100101 Firefox/108.0",
            "human_android_chrome": "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Mobile Safari/537.36",
            "human_ios_safari": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Mobile/15E148 Safari/604.1",
            "brave_browser": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36", # Brave often uses a similar UA to Chrome
            "edge_browser": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1462.54",
            "duckduckbot": "DuckDuckBot/1.0; (+http://duckduckgo.com/duckduckbot.html)",
            "slackbot": "Slackbot 1.0 (+https://api.slack.com/robots)",
            "comet": "Mozilla/5.0 (compatible; Comet/1.0; Perplexity AI Agent)",
            "gptbot": "Mozilla/5.0 (compatible; GPTBot/1.0; +https://openai.com/gptbot)",
            "claude": "Mozilla/5.0 (compatible; Claude-3/1.0; Anthropic AI Agent)",
            "gemini": "Mozilla/5.0 (compatible; Gemini/1.0; Google AI Agent)"
        }

    async def _probe(self, client: httpx.AsyncClient, url: str, headers: dict = {}) -> dict:
        """
        Performs a single, safe, asynchronous request.
        """
        try:
            response = await client.get(url, headers=headers, timeout=self.timeout, follow_redirects=True)
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
        Gathers all necessary evidence from the target website concurrently.
        """
        logging.info("Gathering evidence...")
        evidence = {}
        tasks = []

        async with httpx.AsyncClient() as client:
            # 1. Create task for agents.json manifest check
            manifest_url = urljoin(self.base_url, "/.well-known/agents.json")
            tasks.append(self._probe(client, manifest_url))

            # 2. Create tasks for probing with different User-Agents
            for ua_string in self.user_agents.values():
                tasks.append(self._probe(client, self.base_url, headers={"User-Agent": ua_string}))

            # 3. Create task for probing with custom agent headers
            custom_headers = {
                "User-Agent": self.user_agents["human_baseline"],
                "X-Agent-Type": "AI-Assistant",
                "X-Requested-By": "AI-Agent"
            }
            tasks.append(self._probe(client, self.base_url, headers=custom_headers))

            logging.info(f"Executing {len(tasks)} probes concurrently...")
            results = await asyncio.gather(*tasks)

        # Structure the results
        evidence['manifest_check'] = results[0]
        evidence['user_agent_probes'] = {name: result for name, result in zip(self.user_agents.keys(), results[1:-1])}
        evidence['custom_header_probe'] = results[-1]

        logging.info("Evidence gathering complete.")
        return evidence

    def run_and_analyze(self) -> dict:
        """
        Gathers evidence and sends it to the LLM for a final analysis.
        """
        evidence = asyncio.run(self.gather_evidence())

        prompt = f"""
        Act as a cybersecurity and web intelligence analyst. Your task is to audit a website's agent identification capabilities based on the following evidence.

        **Evidence Collected:**
        ```json
        {json.dumps(evidence, indent=2)}
        ```

        **Analysis Instructions:**
        1.  **Manifest Analysis:** Review `manifest_check`. Does the site provide a valid `agents.json` file (status 200)? If so, summarize its declarations. This is a strong positive signal.
        2.  **Differential Treatment (User-Agent):** Compare the `human_baseline` response in `user_agent_probes` to the bot responses (googlebot, gptbot, etc.). Note any significant differences in status code, content length, or headers. Different responses indicate the site is actively identifying and segmenting traffic.
        3.  **Differential Treatment (Custom Headers):** Compare the `human_baseline` response to the `custom_header_probe`. Is there any evidence (different status, content, or headers) that the site recognized the custom `X-Agent-*` headers?
        4.  **Behavioral Evasion:** Analyze the `content_snippet` from the `human_baseline` probe. Are there any JavaScript patterns suggesting anti-bot measures like `navigator.webdriver`, canvas fingerprinting, or JS challenges? The presence of these indicates a sophisticated, albeit potentially adversarial, detection mechanism.
        5.  **Final Score & Justification:** Based on all evidence, provide a final score from 0 (no detection) to 100 (sophisticated, multi-layered detection and differentiation). Justify your score with a concise, expert explanation, referencing your findings from the steps above.

        **Output Format:**
        Provide your response *only* as a valid JSON object with two keys: "score" (integer) and "explanation" (string). Do not include any other text or markdown formatting.
        """

        logging.info("Sending evidence to Gemini for analysis...")
        try:
            response = self.model.generate_content(prompt)
            # A robust way to extract JSON, even if wrapped in markdown
            match = re.search(r"```json\n(.*?)\n```", response.text, re.DOTALL)
            if match:
                json_string = match.group(1)
            else:
                json_string = response.text

            return json.loads(json_string)
        except Exception as e:
            logging.error(f"An error occurred during Gemini analysis: {e}")
            logging.debug(f"Raw response was: {response.text if 'response' in locals() else 'No response'}")
            return {"score": -1, "explanation": f"Failed to analyze: {e}"}
