import asyncio
import httpx
import json
import re
import logging
from urllib.parse import urljoin
from dotenv import load_dotenv

load_dotenv()

# --- Basic Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ConversationalBot:
    """
    Sub-pillar: Conversational Bot Assistance (Hybrid Detection)

    Audits a website's ability to provide programmatic assistance to an AI agent
    via a conversational interface (chatbot), using an LLM-first detection strategy.
    """
    def __init__(self, base_url: str, model, timeout: float = 15.0):
        self.base_url = base_url
        self.model = model
        self.timeout = timeout

        self.bot_patterns = {
            "Intercom": r"widget\.intercom\.io",
            "Drift": r"js\.driftt\.com",
            "HubSpot": r"js\.hs-scripts\.com",
            "Zendesk": r"static\.zdassets\.com/ekr\.js",
            "Dialogflow": r"dialogflow\.cloud\.google\.com"
        }
    
    async def _probe(self, client: httpx.AsyncClient, url: str, method: str = "GET", headers: dict = {}, data: dict = {}) -> dict:
        """
        Performs a single, safe and asynchronous request and returns the summary
        """
        try:
            if method.upper() == "POST":
                response = await client.post(url, headers=headers, json=data, timeout=self.timeout, follow_redirects=True)
            else:
                response = await client.get(url, headers=headers, timeout=self.timeout, follow_redirects=True)

            logging.info(f"Response from {url}: {response.status_code}")

            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.text
            }

        except httpx.RequestError as e:
            logging.warning(f"Request failed for {url}: {e}")
            return {"error": str(e)}
        
    async def _detect_bot(self, body: str):
        """
        Uses the LLM to intelligently detect a chatbot from HTML content.
        """
        if not body.strip():
            return "Unknown"

        prompt = f"""
        Analyze the following HTML content to detect any type of conversational bot, chatbot, live chat widget, or AI assistant.

        Look for ANY indicators of conversational interfaces including but not limited to:
        - Popular platforms: Intercom, Drift, HubSpot, Zendesk, LiveChat, Tawk.to, Freshchat, Crisp, Tidio, etc.
        - Custom chatbot implementations
        - AI assistants and virtual agents
        - Live chat widgets
        - Customer support chat interfaces
        - Voice assistants or speech interfaces
        - Embedded chat iframes
        - WebSocket chat connections
        - Bot framework implementations
        - Any conversational UI elements

        Examine:
        - Script tags loading chat/bot libraries
        - Chat widget HTML elements
        - CSS classes related to chat/messaging
        - JavaScript variables or functions for chat
        - API endpoints for messaging
        - WebSocket connections
        - Chat-related meta tags or configurations

        HTML Content:
        ```html
        {body}
        ```

        Respond with ONLY the name/type of the detected conversational platform. Examples:
        - "Intercom" (for Intercom widget)
        - "Custom Bot" (for custom implementations)
        - "Drift" (for Drift chat)
        - "LiveChat Widget" (for generic live chat)
        - "AI Assistant" (for AI-powered bots)
        - "Voice Assistant" (for voice interfaces)
        - "Unknown" (if no conversational interface detected)

        Be specific about the platform if identifiable, otherwise use descriptive terms like "Custom Bot" or "Live Chat Widget".
        """
        try:
            response = self.model.generate_content(prompt)
            # Clean up potential markdown or extra text
            platform = response.text.strip().replace("`", "").replace("\"", "")
            return platform if platform else "Unknown"
        except Exception as e:
            logging.error(f"LLM bot detection failed: {e}")
            return "Unknown"
        
    async def gather_evidence(self) -> dict:
        """
        Gathers evidence using a hybrid, LLM-first approach to detect a chatbot.
        """
        logging.info("Gathering conversational bot evidence...")
        evidence = {}
        
        async with httpx.AsyncClient(follow_redirects=True) as client:
            # 1. Get the homepage content
            homepage_response = await self._probe(client, self.base_url)
            homepage_body = homepage_response.get("body", "")
            evidence['homepage_scan_status'] = homepage_response.get("status_code")

            # 2. LLM-First Detection
            logging.info("-> Attempting bot detection with LLM...")
            llm_detected_platform = await self._detect_bot(homepage_body) # Use a snippet to manage token size
            evidence['llm_detection_result'] = llm_detected_platform
            
            detected_platform = llm_detected_platform

            # 3. Regex Fallback Detection
            if detected_platform == "Unknown":
                logging.info("-> LLM result inconclusive. Falling back to regex check...")
                regex_platform = "None"
                for platform, pattern in self.bot_patterns.items():
                    if re.search(pattern, homepage_body):
                        regex_platform = platform
                        break
                evidence['regex_fallback_result'] = regex_platform
                detected_platform = regex_platform # Use regex result if it's not None
            
            logging.info(f"--> Final Detected Platform: {detected_platform}")
            evidence['final_detected_platform'] = detected_platform

            # 4. Attempt a programmatic query if a bot was found
            if detected_platform != "None":
                logging.info("-> Attempting programmatic interaction...")
                manifest_url = urljoin(self.base_url, "/.well-known/agents.json")
                manifest_response = await self._probe(client, manifest_url)
                chat_api_url = None
                if manifest_response.get("status_code") == 200:
                    try:
                        manifest_data = json.loads(manifest_response.get("body", "{}"))
                        chat_api_url = manifest_data.get("agent_endpoints", {}).get("conversational_api")
                        evidence['manifest_discovery'] = {"found": True, "api_url": chat_api_url}
                    except json.JSONDecodeError:
                        evidence['manifest_discovery'] = {"found": True, "error": "Failed to parse JSON."}
                else:
                    evidence['manifest_discovery'] = {"found": False}

                # Step 4b: Fallback to a generic endpoint if not found in manifest
                if not chat_api_url:
                    logging.info("--> No chat API in manifest, falling back to generic endpoint.")
                    chat_api_url = urljoin(self.base_url, "/api/v1/chat")
                agent_query = {
                    "session_id": "agent-session-12345",
                    "query_type": "disambiguation",
                    "context": "Found two products named 'SuperWidget'. One is model 'X1', the other is 'X2'.",
                    "question": "Which is the newer version?"
                }
                interaction_attempt = await self._probe(client, chat_api_url, method='POST', data=agent_query)
                evidence['programmatic_interaction_attempt'] = interaction_attempt
            else:
                evidence['programmatic_interaction_attempt'] = {"status": "skipped", "reason": "No bot platform detected by any method."}

        logging.info("Evidence gathering complete.")
        return evidence
    
    def run_and_analyze(self) -> dict:
        """
        Gathers conversational bot evidence and sends it to the LLM for a final analysis.
        """

        evidence = asyncio.run(self.gather_evidence())

        prompt = f"""
        Act as a senior conversational AI and chatbot integration specialist. Your task is to audit a website's "Conversational Bot Assistance" for AI agents based on the following evidence.

        **Evidence Collected:**
        ```json
        {json.dumps(evidence, indent=2)}
        ```

        **Analysis Instructions:**
        1. **Bot Detection:** Evaluate if any conversational interface was successfully identified (chatbots, live chat, AI assistants, etc.)
        2. **API Discoverability:** Check if the site provides proper API endpoint discovery through agents.json manifest or similar mechanisms
        3. **Programmatic Access:** Assess if agents can successfully interact with conversational endpoints programmatically
        4. **Response Structure:** Analyze response format - structured JSON vs plain text, actionable data vs human-only responses
        5. **Agent Integration:** Evaluate overall ease of integration for AI agents to leverage conversational assistance

        **Scoring (0-100):**
        - 0-25: No conversational interface detected or completely inaccessible to agents
        - 26-50: Basic chat detected but poor/no programmatic access or discovery
        - 51-75: Good conversational interface with some programmatic capabilities and structure
        - 76-100: Excellent agent-friendly conversational API with proper discovery and structured responses

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
        
        except Exception as e:
            logging.error(f"An error occurred during Gemini analysis: {e}")
            logging.debug(f"Raw response was: {response.text if 'response' in locals() else 'No response'}")
            return {"score": -1, "explanation": f"Failed to analyze: {e}"}
        