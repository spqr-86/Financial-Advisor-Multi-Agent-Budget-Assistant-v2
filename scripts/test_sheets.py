#!/usr/bin/env python3
"""Test script for Google Sheets integration."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.mcp.storage.sheets import GoogleSheetsStorage


async def main():
    """Test Google Sheets storage."""
    print("🧪 Testing Google Sheets Integration\n")

    storage = GoogleSheetsStorage()

    # Test 1: Health check
    print("1️⃣ Testing health check...")
    health = await storage.health_check()
    print(f"   Status: {health.get('status')}")
    if health.get("status") == "healthy":
        print(f"   ✅ Connected to: {health.get('spreadsheet')}\n")
    else:
        print(f"   ❌ Error: {health.get('error')}\n")
        return

    # Test 2: Add expense
    print("2️⃣ Testing add expense...")
    result = await storage.add_expense(
        user_id="test_user_123",
        category="Еда",
        amount=150.50,
        description="Обед в кафе",
    )
    print(f"   Status: {result.get('status')}")
    if result.get("status") == "success":
        print(f"   ✅ Added: {result.get('category')} - {result.get('amount')} руб.\n")
    else:
        print(f"   ❌ Error: {result.get('error')}\n")

    # Test 3: Add more expenses
    print("3️⃣ Adding more test expenses...")
    expenses = [
        ("Транспорт", 85.0, "Метро"),
        ("Еда", 320.0, "Продукты в магазине"),
        ("Развлечения", 500.0, "Кино"),
    ]

    for category, amount, description in expenses:
        await storage.add_expense(
            user_id="test_user_123",
            category=category,
            amount=amount,
            description=description,
        )
    print(f"   ✅ Added {len(expenses)} more expenses\n")

    # Test 4: Get expenses
    print("4️⃣ Testing get expenses...")
    result = await storage.get_expenses(
        user_id="test_user_123",
        limit=10,
    )
    print(f"   Status: {result.get('status')}")
    if result.get("status") == "success":
        print(f"   ✅ Found {result.get('count')} expenses")
        for exp in result.get("expenses", []):
            print(f"      - {exp.get('Дата')}: {exp.get('Категория')} - {exp.get('Сумма')} руб.")
        print()
    else:
        print(f"   ❌ Error: {result.get('error')}\n")

    # Test 5: Get statistics
    print("5️⃣ Testing get statistics...")
    result = await storage.get_statistics(
        user_id="test_user_123",
        period="month",
    )
    print(f"   Status: {result.get('status')}")
    if result.get("status") == "success":
        print(f"   ✅ Total: {result.get('total')} руб.")
        print(f"   📊 By category:")
        for category, total in result.get("by_category", {}).items():
            print(f"      - {category}: {total} руб.")
        print()
    else:
        print(f"   ❌ Error: {result.get('error')}\n")

    print("✅ All tests completed!")
    print("\n📝 Check your Google Sheets: https://docs.google.com/spreadsheets/")
    print("   Look for worksheet: 'User_test_user_123'")


if __name__ == "__main__":
    asyncio.run(main())
