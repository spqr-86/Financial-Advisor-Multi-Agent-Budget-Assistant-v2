#!/usr/bin/env python3
"""Test script for ADK Multi-Agent system."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.mcp.agents.adk_agents import ADKBudgetAgent


async def main():
    """Test ADK Multi-Agent system with google-adk patterns."""
    print("🤖 Testing ADK Multi-Agent Budget System\n")
    print("=" * 70)
    print("Architecture:")
    print("  - Root Agent (LLM Orchestrator)")
    print("  - RegistrarAgent (adds/deletes expenses)")
    print("  - AnalystAgent (views expenses/statistics)")
    print("  - Using google-adk patterns from 5-days course")
    print("=" * 70)

    agent = ADKBudgetAgent()

    # Test queries
    test_queries = [
        # Registrar agent tests
        "купил хлеб 50 рублей",
        "потратил на кино 500",

        # Analyst agent tests
        "покажи последние 5 расходов",
        "статистика за месяц",

        # General query
        "привет!",
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Пользователь: {query}")
        print("-" * 70)

        response = await agent.process(query=query, user_id="test_user")

        print(f"Ответ: {response}")
        print("=" * 70)

        # Small delay between requests
        await asyncio.sleep(2)

    print("\n✅ Тестирование ADK системы завершено!")
    print("\n📝 Проверьте Google Sheets - там должны быть новые записи")


if __name__ == "__main__":
    asyncio.run(main())
