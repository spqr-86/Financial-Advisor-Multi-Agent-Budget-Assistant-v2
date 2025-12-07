"""Test Google Sheets connection."""
import gspread
from google.oauth2.service_account import Credentials

# Настройка credentials
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

creds = Credentials.from_service_account_file(
    "service-account.json",
    scopes=SCOPES,
)

# Подключение
client = gspread.authorize(creds)

# Открыть таблицу
spreadsheet = client.open("Budget Assistant Data")
print(f"✅ Подключено к таблице: {spreadsheet.title}")
print(f"   URL: {spreadsheet.url}")

# Получить или создать лист
try:
    worksheet = spreadsheet.worksheet("Расходы")
    print(f"✅ Найден лист: {worksheet.title}")
except gspread.WorksheetNotFound:
    worksheet = spreadsheet.add_worksheet("Расходы", rows=1000, cols=4)
    worksheet.append_row(["Дата", "Категория", "Описание", "Сумма"])
    print(f"✅ Создан новый лист: {worksheet.title}")

# Добавить тестовую запись
from datetime import datetime
test_row = [
    datetime.now().strftime("%d.%m.%Y %H:%M"),
    "Тест",
    "Проверка подключения",
    100.0,
]
worksheet.append_row(test_row)
print(f"✅ Добавлена тестовая запись: {test_row}")

print("\n🎉 Настройка Google Sheets завершена успешно!")
