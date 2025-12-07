#!/usr/bin/env python3
"""Test script for AI agent."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.mcp.agents.simple import SimpleBudgetAgent


async def main():
    """Test AI agent with various queries."""
    print("🤖 Testing AI Budget Agent\n")
    print("=" * 60)

    agent = SimpleBudgetAgent()

    # Test queries
    test_queries = [
        "купил хлеб 50 рублей",
        "потратил на кино 500",
        "покажи последние 5 расходов",
        "статистика за месяц",
        "удали последний расход",
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Пользователь: {query}")
        print("-" * 60)

        response = await agent.process(query=query, user_id="test_user")

        print(f"Агент: {response}")
        print("=" * 60)

        # Small delay between requests
        await asyncio.sleep(2)

    print("\n✅ Тестирование завершено!")
    print("\n📝 Проверьте Google Sheets - там должны быть новые записи")


if __name__ == "__main__":
    asyncio.run(main())
