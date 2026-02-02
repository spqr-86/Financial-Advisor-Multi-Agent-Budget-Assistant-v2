"""Prompt loader utility using Jinja2 templates."""

import logging
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

logger = logging.getLogger(__name__)

# Base directory for prompts
PROMPTS_DIR = Path(__file__).parent
AGENTS_DIR = PROMPTS_DIR / "agents"

# Jinja2 environment (created once at module load)
_env = Environment(
    loader=FileSystemLoader(AGENTS_DIR),
    autoescape=False,  # Prompts are plain text, not HTML
)


def load_prompt(
    name: str,
    **variables,
) -> str:
    """
    Load and render a prompt template.

    Args:
        name: Template name without extension (e.g., "orchestrator", "registrar")
        **variables: Variables to inject into the template

    Returns:
        Rendered prompt string

    Raises:
        FileNotFoundError: If template doesn't exist

    Example:
        prompt = load_prompt(
            "registrar",
            categories="- Еда\\n- Транспорт\\n- Прочее"
        )
    """
    template_name = f"{name}.j2"

    try:
        template = _env.get_template(template_name)
        rendered = template.render(**variables)

        logger.debug(f"Loaded prompt '{name}' with {len(variables)} variables")
        return rendered

    except TemplateNotFound:
        logger.error(f"Prompt template not found: {template_name}")
        raise FileNotFoundError(f"Prompt template not found: {AGENTS_DIR / template_name}")


def load_orchestrator_prompt() -> str:
    """Load orchestrator prompt (no variables)."""
    return load_prompt("orchestrator")


def load_registrar_prompt(categories: str) -> str:
    """
    Load registrar prompt with categories.

    Args:
        categories: Newline-separated list of categories
    """
    return load_prompt("registrar", categories=categories)


def load_analyst_prompt(
    categories_with_emoji: str,
    current_date: str | None = None,
) -> str:
    """
    Load analyst prompt with categories and current date.

    Args:
        categories_with_emoji: Categories with emoji for formatting
        current_date: Current date string (default: today)
    """
    if current_date is None:
        current_date = datetime.now().strftime("%d.%m.%Y")

    return load_prompt(
        "analyst",
        categories_with_emoji=categories_with_emoji,
        current_date=current_date,
    )


# Version info for logging/debugging
PROMPT_VERSION = "v1.0.0"


def get_prompt_info() -> dict:
    """Get information about loaded prompts for debugging."""
    return {
        "version": PROMPT_VERSION,
        "prompts_dir": str(AGENTS_DIR),
        "templates": [p.name for p in AGENTS_DIR.glob("*.j2")],
    }
