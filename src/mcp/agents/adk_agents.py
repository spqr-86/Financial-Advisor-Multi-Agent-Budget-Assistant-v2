"""Multi-agent system using google-adk patterns from 5-days course."""

import logging
import os

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools import AgentTool
from google.genai import types

from src.core.categories import format_categories_for_prompt, get_categories_list
from src.mcp.agents.tools.code_executor import execute_analysis_code
from src.mcp.agents.tools.sheets import (
    add_expense_tool,
    delete_last_expense_tool,
    get_expenses_tool,
    get_statistics_tool,
)
from src.mcp.config import settings
from prompts.loader import (
    load_analyst_prompt,
    load_orchestrator_prompt,
    load_registrar_prompt,
)

# Generate categories text for prompts
_categories_list = "\n".join(f"- {cat}" for cat in get_categories_list())
_categories_with_emoji = format_categories_for_prompt()

# Load prompts from templates (at startup)
_orchestrator_prompt = load_orchestrator_prompt()
_registrar_prompt = load_registrar_prompt(categories=_categories_list)
_analyst_prompt = load_analyst_prompt(categories_with_emoji=_categories_with_emoji)

logger = logging.getLogger(__name__)

# Setup API key in environment (ADK way)
os.environ["GOOGLE_API_KEY"] = settings.google_api_key

# Retry configuration for robustness
# Exponential backoff: 1s, 2s, 4s, 8s (total ~15s max wait)
retry_config = types.HttpRetryOptions(
    attempts=4,
    exp_base=2,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)


# Registrar Agent - specialized in adding/deleting expenses
registrar_agent = LlmAgent(
    name="RegistrarAgent",
    model=Gemini(
        model=settings.gemini_model,  # Configurable via GEMINI_MODEL env var
        retry_options=retry_config,
    ),
    instruction=_registrar_prompt,  # Loaded from prompts/agents/registrar.j2
    tools=[add_expense_tool, delete_last_expense_tool],
    output_key="registrar_result",
)


# Analyst Agent - specialized in viewing expenses and statistics
analyst_agent = LlmAgent(
    name="AnalystAgent",
    model=Gemini(
        model=settings.gemini_model,  # Configurable via GEMINI_MODEL env var
        retry_options=retry_config,
    ),
    instruction=_analyst_prompt,  # Loaded from prompts/agents/analyst.j2
    tools=[get_expenses_tool, get_statistics_tool, execute_analysis_code],
    output_key="analyst_result",
)


# Root Agent (LLM Orchestrator) - coordinates specialized agents
root_agent = LlmAgent(
    name="BudgetOrchestrator",
    model=Gemini(
        model=settings.gemini_model,  # Configurable via GEMINI_MODEL env var
        retry_options=retry_config,
    ),
    instruction=_orchestrator_prompt,  # Loaded from prompts/agents/orchestrator.j2
    tools=[
        AgentTool(registrar_agent),
        AgentTool(analyst_agent),
    ],
)


class ADKBudgetAgent:
    """Budget agent system using google-adk architecture."""

    def __init__(self):
        """Initialize the ADK budget agent."""
        self.runner = InMemoryRunner(agent=root_agent)
        logger.info("ADKBudgetAgent initialized with google-adk patterns (5-days course)")

    async def process(self, query: str, user_id: str = "default") -> str:
        """
        Process user query through multi-agent system.

        Args:
            query: User's message
            user_id: User identifier (currently defaults to "default")

        Returns:
            Agent's response
        """
        try:
            logger.info(f"ADK processing query for user {user_id}: {query[:50]}...")

            # Run through ADK runner - returns list of events
            events = await self.runner.run_debug(query)

            # Extract text from events
            response_text = ""
            if events is None:
                logger.warning("ADK runner returned None events")
                return "Извините, не смог обработать запрос."

            for event in events:
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            response_text += part.text

            if response_text:
                logger.info(f"ADK response: {response_text[:100]}...")
                return response_text
            else:
                logger.warning("No text in ADK response")
                return "Извините, не смог обработать запрос."

        except Exception as e:
            # Check if it's a quota/rate limit error (429)
            error_str = str(e).lower()
            if "429" in error_str or "quota" in error_str or "resource_exhausted" in error_str:
                logger.error(
                    "🚨 GEMINI API QUOTA EXCEEDED! "
                    f"Model quota exhausted. Error: {e}",
                    exc_info=True
                )
                return "Извините, превышен лимит запросов к AI. Попробуйте позже."

            logger.error(f"Error in ADK agent: {e}", exc_info=True)
            return f"Произошла ошибка: {str(e)}"
