# AXO (Agent eXperience Optimization) Pillar

The AXO pillar evaluates how well websites are optimized for AI agents and automated systems. This includes agent identification, accessibility, documentation, and overall agent experience.

## Sub-pillars

### 1. Agent Identification (`agent_identification.py`)

Evaluates a website's ability to identify and differentiate AI agents from human users.

**Key Features:**
- Agent manifest discovery (agents.json, robots.txt)
- Differential treatment analysis across 15+ user agents
- Anti-bot measure detection
- Comprehensive scoring and recommendations

**Usage:**
```python
from services.axo import AgentIdentificationAuditor

auditor = AgentIdentificationAuditor(timeout=30.0)
result = await auditor.evaluate("https://example.com")

print(f"Score: {result.score}/100")
print(f"Status: {result.status}")
print(f"Recommendations: {result.recommendations}")
```

**Scoring Criteria:**
- **Manifest (0-40 points)**: Presence and quality of agent declarations
- **Differential Treatment (0-35 points)**: Smart agent handling and routing
- **Anti-bot Measures (0-25 points)**: Balanced security vs accessibility

**Status Levels:**
- **Excellent (90-100)**: Sophisticated agent detection and optimization
- **Good (70-89)**: Clear agent identification mechanisms
- **Fair (50-69)**: Basic detection capabilities
- **Poor (25-49)**: Limited or inconsistent detection
- **None (0-24)**: No detectable agent identification

### 2. Error Recovery Assistance (`error_recovery.py`)

Evaluates a website's ability to provide actionable assistance to AI agents when errors occur, enabling agents to recover and continue their tasks.

**Key Features:**
- Client-side error analysis (4xx responses)
- Server-side error testing (5xx responses, rate limiting)
- Error message structure evaluation
- Recovery guidance assessment
- LLM-powered analysis and scoring

**Usage:**
```python
from services.axo.error_recovery import ErrorRecovery
import google.generativeai as genai

# Configure your model
model = genai.GenerativeModel('gemini-pro')

recovery = ErrorRecovery(
    base_url="https://example.com",
    model=model,
    timeout=15.0
)

result = recovery.run_and_analyze()

print(f"Score: {result['score']}/100")
print(f"Explanation: {result['explanation']}")
print(f"Recommendations: {result['recommendations']}")
```

**Error Testing Methods:**
- **Client-Side Errors**: Sends invalid registration data to trigger 4xx responses
- **Server-Side Errors**: Performs burst requests to attempt rate limiting (429/503)
- **Error Structure Analysis**: Evaluates error message quality and actionable guidance

**Scoring Criteria (0-100):**
- **0-25**: Generic errors, no recovery guidance
- **26-50**: Basic error messages, minimal structure
- **51-75**: Good error structure, some recovery hints
- **76-100**: Excellent structured errors with clear recovery paths

**Analysis Focus:**
- Structured error codes and clear messages
- 404 handling with helpful navigation
- Rate limiting with proper Retry-After headers
- Actionable recovery guidance for agents

### 3. Conversational Bot Assistance (`conversational_bot.py`)

Evaluates a website's ability to provide programmatic assistance to AI agents via conversational interfaces (chatbots), using a hybrid LLM-first detection strategy.

**Key Features:**
- Hybrid detection strategy (LLM + regex fallback)
- Multi-platform support for popular and custom chatbots
- API endpoint discovery via agents.json manifest
- Programmatic interaction testing
- Comprehensive analysis of agent-friendly conversational capabilities

**Usage:**
```python
import google.generativeai as genai
from services.axo.conversational_bot import ConversationalBot

# Configure Gemini
genai.configure(api_key="your_api_key")
model = genai.GenerativeModel('gemini-1.5-flash')

# Initialize and run analysis
bot = ConversationalBot("https://example.com", model, timeout=20.0)
result = bot.run_and_analyze()

print(f"Score: {result['score']}/100")
print(f"Analysis: {result['explanation']}")
print(f"Recommendations: {result['recommendations']}")
```

**Detection Methods:**
1. **LLM Analysis**: Uses Gemini to intelligently analyze HTML content for any conversational interfaces
2. **Regex Fallback**: Pattern matching for known chat platforms when LLM detection is inconclusive
3. **Manifest Discovery**: Looks for standardized agent endpoint specifications in `.well-known/agents.json`
4. **API Testing**: Attempts programmatic queries to discovered or common chat endpoints

**Supported Platforms:**
- Intercom (`widget\.intercom\.io`)
- Drift (`js\.driftt\.com`)
- HubSpot (`js\.hs-scripts\.com`)
- Zendesk (`static\.zdassets\.com/ekr\.js`)
- Dialogflow (`dialogflow\.cloud\.google\.com`)
- Custom implementations and other platforms via LLM detection

**Scoring Criteria (0-100):**
- **0-25**: No conversational interface detected or completely inaccessible to agents
- **26-50**: Basic chat detected but poor/no programmatic access or discovery mechanisms
- **51-75**: Good conversational interface with some programmatic capabilities and structured responses
- **76-100**: Excellent agent-friendly conversational API with proper discovery and structured responses

**Analysis Areas:**
- Bot platform detection and identification
- API discoverability through standard mechanisms
- Programmatic access capabilities
- Response structure quality (JSON vs plain text)
- Overall agent integration potential

## Architecture

### Models

- `AgentIdentificationResult`: Comprehensive analysis result
- `AgentManifest`: Agent manifest file structure
- `DifferentialTreatmentResult`: User agent treatment analysis
- `ProbeResponse`: HTTP probe response structure
- `ErrorRecovery`: Error recovery assistance auditor class
- `ConversationalBot`: Conversational bot assistance auditor class

### Key Methods

**Agent Identification:**
- `evaluate(base_url)`: Main evaluation method
- `_discover_agent_manifest()`: Finds and parses agent manifests
- `_analyze_differential_treatment()`: Tests various user agents
- `_detect_anti_bot_measures()`: Identifies security measures

**Error Recovery:**
- `run_and_analyze()`: Main analysis method combining evidence gathering and LLM evaluation
- `gather_evidence()`: Collects error response data through controlled testing
- `_probe()`: Performs safe HTTP requests for error testing

**Conversational Bot:**
- `run_and_analyze()`: Complete analysis with evidence gathering and LLM evaluation
- `gather_evidence()`: Hybrid detection approach combining LLM and regex methods
- `_detect_bot(body)`: LLM-powered bot detection from HTML content
- `_probe(client, url, method, headers, data)`: Safe asynchronous HTTP request execution

## Production Features

- **Async/Await**: Full async support for performance
- **Error Handling**: Comprehensive error handling and logging
- **Rate Limiting**: Built-in semaphore for request management
- **Retry Logic**: Exponential backoff for failed requests
- **Validation**: Pydantic models for data validation
- **Logging**: Structured logging throughout
- **Timeouts**: Configurable timeouts for all operations

## Testing

### Agent Identification Testing
Run the test file to see the auditor in action:

```bash
python -m services.axo.test_agent_identification
```

### Conversational Bot Testing
Test the conversational bot detection directly:

```bash
python -m services.axo.conversational_bot
```

This will test popular websites with known chat implementations:
- Intercom (https://www.intercom.com)
- Drift (https://www.drift.com) 
- Zendesk (https://www.zendesk.com)
- Or customize with your own URL

**Sample Test Output:**
```
Testing Conversational Bot Detection for: https://www.intercom.com
============================================================

🤖 CONVERSATIONAL BOT ANALYSIS RESULTS:
==================================================
Score: 85/100
Explanation: The website successfully implements Intercom chat widget with good programmatic potential...

📋 Recommendations:
  1. Implement agents.json manifest for better API discovery
  2. Provide structured JSON responses for programmatic queries
  3. Add rate limiting information in API responses

📊 Full Analysis Result:
{
  "score": 85,
  "explanation": "...",
  "recommendations": [...]
}
```

## Configuration

The auditor can be configured with:

```python
auditor = AgentIdentificationAuditor(
    timeout=30.0,        # Request timeout in seconds
    max_retries=3        # Maximum retry attempts
)
```

## Dependencies

- `httpx`: Modern async HTTP client
- `pydantic`: Data validation and settings management
- `tenacity`: Retry logic with exponential backoff
- `google.generativeai`: LLM integration for error analysis (Error Recovery)
- `asyncio`: Asynchronous programming support
- `urllib.parse`: URL manipulation utilities

## Integration

This sub-pillar integrates with the main ARI scoring system:

```python
from services.axo import AgentIdentificationAuditor
from services.axo.error_recovery import ErrorRecovery
from services.axo.conversational_bot import ConversationalBot
import google.generativeai as genai

async def evaluate_axo_pillar(base_url: str) -> dict:
    # Configure Gemini model
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Agent Identification
    agent_auditor = AgentIdentificationAuditor()
    agent_result = await agent_auditor.evaluate(base_url)
    
    # Error Recovery
    error_recovery = ErrorRecovery(base_url, model)
    recovery_result = error_recovery.run_and_analyze()
    
    # Conversational Bot
    conv_bot = ConversationalBot(base_url, model)
    bot_result = conv_bot.run_and_analyze()
    
    return {
        "agent_identification": {
            "sub_pillar_code": "axo_1",
            "name": "Agent Identification",
            "score": agent_result.score,
            "status": agent_result.status.value,
            "recommendations": agent_result.recommendations,
            "technical_details": agent_result.technical_details
        },
        "error_recovery": {
            "sub_pillar_code": "axo_2", 
            "name": "Error Recovery Assistance",
            "score": recovery_result.get('score', 0),
            "explanation": recovery_result.get('explanation', ''),
            "recommendations": recovery_result.get('recommendations', [])
        },
        "conversational_bot": {
            "sub_pillar_code": "axo_3",
            "name": "Conversational Bot Assistance", 
            "score": bot_result.get('score', 0),
            "explanation": bot_result.get('explanation', ''),
            "recommendations": bot_result.get('recommendations', [])
        }
    }
```