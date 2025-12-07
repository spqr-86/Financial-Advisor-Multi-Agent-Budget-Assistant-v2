#!/usr/bin/env python3
"""Test script for delete last expense functionality."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.mcp.storage.sheets import GoogleSheetsStorage


async def main():
    """Test delete last expense."""
    print("🧪 Testing Delete Last Expense\n")

    storage = GoogleSheetsStorage()

    # Test 1: Get current expenses
    print("1️⃣ Getting current expenses...")
    result = await storage.get_expenses(user_id="test_user", limit=1000)
    if result.get("status") == "success":
        count_before = result.get("count")
        expenses = result.get("expenses", [])
        print(f"   Total expenses: {count_before}")
        if expenses:
            last = expenses[-1]
            print(f"   Last expense: {last.get('Дата')} - {last.get('Категория')} - {last.get('Сумма')}\n")
        else:
            print("   No expenses found!\n")
            return
    else:
        print(f"   ❌ Error: {result.get('error')}\n")
        return

    # Test 2: Delete last expense
    print("2️⃣ Deleting last expense...")
    result = await storage.delete_last_expense(user_id="test_user")
    if result.get("status") == "success":
        deleted = result.get("deleted_expense", {})
        print(f"   ✅ Deleted: {deleted.get('Дата')} - {deleted.get('Категория')} - {deleted.get('Сумма')}\n")
    else:
        print(f"   ❌ Error: {result.get('error')}\n")
        return

    # Test 3: Verify deletion
    print("3️⃣ Verifying deletion...")
    result = await storage.get_expenses(user_id="test_user", limit=1000)
    if result.get("status") == "success":
        count_after = result.get("count")
        expenses = result.get("expenses", [])
        print(f"   Before: {count_before} expenses")
        print(f"   After:  {count_after} expenses")
        if count_after == count_before - 1:
            print("   ✅ Deletion confirmed!")
            if expenses:
                new_last = expenses[-1]
                print(f"   New last: {new_last.get('Дата')} - {new_last.get('Категория')} - {new_last.get('Сумма')}\n")
        else:
            print("   ⚠️ Count mismatch!\n")
    else:
        print(f"   ❌ Error: {result.get('error')}\n")

    print("✅ Test completed!")
    print("\n📝 Check your Google Sheets to verify the last row was deleted")


if __name__ == "__main__":
    asyncio.run(main())
