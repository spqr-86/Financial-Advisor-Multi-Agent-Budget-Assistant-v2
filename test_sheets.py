"""Test Google Sheets connection."""
import os
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

# Загрузить переменные окружения
load_dotenv()

# Настройка credentials
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

creds = Credentials.from_service_account_file(
    os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "service-account.json"),
    scopes=SCOPES,
)

# Подключение
client = gspread.authorize(creds)

# Открыть таблицу
spreadsheet_id = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
spreadsheet_name = os.getenv("GOOGLE_SHEETS_SPREADSHEET_NAME", "Budget Assistant Data")

if spreadsheet_id:
    spreadsheet = client.open_by_key(spreadsheet_id)
else:
    spreadsheet = client.open(spreadsheet_name)
print(f"✅ Подключено к таблице: {spreadsheet.title}")
print(f"   URL: {spreadsheet.url}")

# Получить лист (не создаем, используем существующий)
worksheet_name = "Траты и бюджет"
try:
    worksheet = spreadsheet.worksheet(worksheet_name)
    print(f"✅ Найден лист: {worksheet.title}")
except gspread.WorksheetNotFound:
    print(f"❌ ОШИБКА: Лист '{worksheet_name}' не найден!")
    print(f"   Создайте лист '{worksheet_name}' с колонками: Дата | Категория | Расшифровка | Сумма")
    exit(1)

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
