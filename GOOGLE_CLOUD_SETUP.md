# 🔧 Настройка Google Cloud для Google Sheets API

> Пошаговая инструкция по настройке Service Account для работы с Google Sheets

---

## 📋 Что мы настроим

1. Google Cloud Project
2. Google Sheets API и Google Drive API
3. Service Account (сервисный аккаунт для бота)
4. JSON credentials (ключи для авторизации)
5. Доступ к Google Sheets

**Время:** ~10-15 минут
**Стоимость:** Бесплатно (в пределах квот)

---

## Шаг 1: Создание проекта в Google Cloud Console

### 1.1 Перейти в консоль

🔗 **Откройте:** https://console.cloud.google.com/

- Если у вас нет аккаунта Google Cloud, создайте его (требуется Google аккаунт)
- При первом входе может попросить согласиться с условиями

### 1.2 Создать новый проект

1. Нажмите на выпадающий список **проектов** в верхней панели (рядом с логотипом Google Cloud)
2. Нажмите **"NEW PROJECT"** (Создать проект)
3. Заполните форму:
   - **Project name:** `budget-assistant` (или любое другое имя)
   - **Organization:** оставьте "No organization" (если нет GSuite)
   - **Location:** оставьте как есть
4. Нажмите **"CREATE"** (Создать)

⏱️ Подождите 10-30 секунд пока проект создастся.

### 1.3 Выбрать созданный проект

1. В выпадающем списке проектов найдите `budget-assistant`
2. Кликните на него, чтобы переключиться на этот проект
3. Убедитесь, что в верхней панели отображается название вашего проекта

---

## Шаг 2: Включение API

### 2.1 Включить Google Sheets API

1. В левом меню нажмите **"APIs & Services"** → **"Library"**

   🔗 Или прямая ссылка: https://console.cloud.google.com/apis/library

2. В поиске введите: **"Google Sheets API"**

3. Кликните на **"Google Sheets API"** в результатах

4. Нажмите синюю кнопку **"ENABLE"** (Включить)

⏱️ Подождите пару секунд пока API активируется.

### 2.2 Включить Google Drive API

1. Вернитесь в **"APIs & Services"** → **"Library"**

2. В поиске введите: **"Google Drive API"**

3. Кликните на **"Google Drive API"** в результатах

4. Нажмите синюю кнопку **"ENABLE"** (Включить)

**❓ Зачем Drive API?**
Google Sheets технически является частью Google Drive. Для создания новых таблиц и управления доступом нужен Drive API.

---

## Шаг 3: Создание Service Account

### 3.1 Перейти в раздел Service Accounts

1. В левом меню: **"APIs & Services"** → **"Credentials"**

   🔗 Или прямая ссылка: https://console.cloud.google.com/apis/credentials

2. Нажмите **"+ CREATE CREDENTIALS"** (вверху страницы)

3. Выберите **"Service account"**

### 3.2 Заполнить данные Service Account

**Шаг 1 из 3: Service account details**

- **Service account name:** `budget-bot`
- **Service account ID:** `budget-bot` (автоматически заполнится)
- **Description:** `Service account for Budget Assistant bot`

Нажмите **"CREATE AND CONTINUE"**

**Шаг 2 из 3: Grant this service account access to project**

- **Select a role:** Пропустите (оставьте пустым)
- Нажмите **"CONTINUE"**

**Шаг 3 из 3: Grant users access to this service account**

- Пропустите (оставьте пустым)
- Нажмите **"DONE"**

---

## Шаг 4: Создание JSON ключа

### 4.1 Открыть Service Account

1. В списке Service Accounts найдите `budget-bot@budget-assistant.iam.gserviceaccount.com`
2. Кликните на **email адрес** сервисного аккаунта

### 4.2 Создать ключ

1. Перейдите на вкладку **"KEYS"** (вверху)

2. Нажмите **"ADD KEY"** → **"Create new key"**

3. Выберите тип ключа: **JSON**

4. Нажмите **"CREATE"**

📥 **Автоматически скачается файл:** `budget-assistant-xxxxxxxxxx.json`

⚠️ **ВАЖНО:** Этот файл содержит приватные ключи! Не публикуйте его в Git!

### 4.3 Сохранить ключ в проект

1. Переименуйте скачанный файл в: `service-account.json`

2. Переместите файл в корень проекта:
   ```bash
   mv ~/Downloads/budget-assistant-*.json /Users/petrbaldaev/Dev/budget-assistant-v2/service-account.json
   ```

3. Проверьте, что файл на месте:
   ```bash
   ls -lh service-account.json
   ```

4. Убедитесь, что `service-account.json` в `.gitignore`:
   ```bash
   cat .gitignore | grep service-account
   ```

   Если нет — добавьте:
   ```bash
   echo "service-account.json" >> .gitignore
   ```

---

## Шаг 5: Скопировать email Service Account

### 5.1 Найти email

В файле `service-account.json` найдите поле `client_email`:

```bash
cat service-account.json | grep client_email
```

Вы увидите что-то вроде:
```json
"client_email": "budget-bot@budget-assistant.iam.gserviceaccount.com",
```

📋 **Скопируйте этот email** — он понадобится в следующем шаге!

---

## Шаг 6: Создание и настройка Google Sheets

### 6.1 Создать таблицу

1. Откройте Google Sheets: https://sheets.google.com

2. Нажмите **"+ Blank"** (Создать пустую таблицу)

3. Переименуйте таблицу: **"Budget Assistant Data"**

### 6.2 Предоставить доступ Service Account

1. В правом верхнем углу нажмите **"Share"** (Настроить доступ)

2. В поле "Add people and groups" вставьте **email Service Account**:
   ```
   budget-bot@budget-assistant.iam.gserviceaccount.com
   ```

3. Выберите права: **"Editor"** (Редактор)

4. **Снимите галочку** "Notify people" (не нужно уведомлять бота)

5. Нажмите **"Share"** / **"Поделиться"**

### 6.3 Скопировать название таблицы

📋 **Скопируйте название таблицы:** `Budget Assistant Data`

Или используйте Spreadsheet ID из URL:
```
https://docs.google.com/spreadsheets/d/1a2b3c4d5e6f7g8h9i0/edit
                                       ^^^^^^^^^^^^^^^^
                                       Это Spreadsheet ID
```

---

## Шаг 7: Настройка переменных окружения

### 7.1 Создать .env файл (если не существует)

```bash
touch .env
```

### 7.2 Добавить переменные

Откройте `.env` и добавьте:

```bash
# Google Cloud
GOOGLE_APPLICATION_CREDENTIALS=./service-account.json
GOOGLE_SHEETS_SPREADSHEET_NAME=Budget Assistant Data

# ИЛИ используйте Spreadsheet ID:
# GOOGLE_SHEETS_SPREADSHEET_ID=1a2b3c4d5e6f7g8h9i0

# Telegram Bot (если еще не добавлено)
TELEGRAM_BOT_TOKEN=your-token-here

# API URLs
BUDGET_API_URL=http://localhost:8081
MCP_API_URL=http://localhost:8082
```

### 7.3 Пример .env.example

Создайте файл `.env.example` (шаблон для других разработчиков):

```bash
cat > .env.example << 'EOF'
# Google Cloud
GOOGLE_APPLICATION_CREDENTIALS=./service-account.json
GOOGLE_SHEETS_SPREADSHEET_NAME=Budget Assistant Data

# Telegram Bot
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11

# API URLs
BUDGET_API_URL=http://localhost:8081
MCP_API_URL=http://localhost:8082

# Logging
LOG_LEVEL=INFO
ENVIRONMENT=development
EOF
```

---

## Шаг 8: Проверка настройки

### 8.1 Установить зависимости

```bash
poetry add gspread google-auth
```

### 8.2 Тестовый скрипт

Создайте файл `test_sheets.py`:

```python
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
```

### 8.3 Запустить тест

```bash
poetry run python test_sheets.py
```

**Ожидаемый вывод:**
```
✅ Подключено к таблице: Budget Assistant Data
   URL: https://docs.google.com/spreadsheets/d/...
✅ Создан новый лист: Расходы
✅ Добавлена тестовая запись: ['07.12.2025 15:30', 'Тест', 'Проверка подключения', 100.0]

🎉 Настройка Google Sheets завершена успешно!
```

### 8.4 Проверить в браузере

1. Откройте вашу таблицу в Google Sheets
2. Перейдите на лист "Расходы"
3. Должна быть строка с заголовками и тестовая запись

---

## 📝 Итоговый чеклист

После выполнения всех шагов у вас должно быть:

- ✅ Google Cloud Project: `budget-assistant`
- ✅ Включены API: Google Sheets API, Google Drive API
- ✅ Service Account: `budget-bot@budget-assistant.iam.gserviceaccount.com`
- ✅ JSON ключ: `service-account.json` (в корне проекта)
- ✅ Google Sheets таблица: "Budget Assistant Data"
- ✅ Service Account имеет доступ к таблице (Editor)
- ✅ `.env` файл с переменными окружения
- ✅ `service-account.json` в `.gitignore`
- ✅ Зависимости установлены: `gspread`, `google-auth`
- ✅ Тестовый скрипт работает ✅

---

## 🔒 Безопасность

### ⚠️ НИКОГДА не коммитьте:

```
service-account.json       # Приватные ключи
.env                       # Токены и секреты
```

### ✅ Проверьте .gitignore:

```bash
cat .gitignore
```

Должно быть:
```
.env
service-account.json
*.json  # Если хотите исключить все JSON
credentials.json
```

### 🔐 Для production (Cloud Run):

Вместо файла `service-account.json` используйте:
- **Secret Manager** в Google Cloud
- Или передавайте JSON как строку в переменной окружения:
  ```bash
  GOOGLE_APPLICATION_CREDENTIALS_JSON='{"type":"service_account",...}'
  ```

---

## 🐛 Troubleshooting

### Ошибка: "API has not been used in project"

**Решение:** Вернитесь в Шаг 2 и убедитесь, что включили оба API (Sheets и Drive)

### Ошибка: "The caller does not have permission"

**Решение:**
1. Проверьте, что в Шаге 6.2 вы дали Service Account права "Editor"
2. Проверьте, что используете правильный email из `service-account.json`

### Ошибка: "Spreadsheet not found"

**Решение:**
1. Проверьте название таблицы (регистр важен!)
2. Или используйте Spreadsheet ID вместо названия
3. Убедитесь, что Service Account имеет доступ к таблице

### Ошибка: "Could not load credentials"

**Решение:**
1. Проверьте путь к `service-account.json`
2. Убедитесь, что файл валидный JSON:
   ```bash
   python -m json.tool service-account.json
   ```

### Ошибка: "gspread.exceptions.APIError: PERMISSION_DENIED"

**Решение:**
1. Включите Google Drive API (Шаг 2.2)
2. Подождите 1-2 минуты после включения API

---

## 🎯 Следующий шаг

После успешной настройки Google Cloud переходите к:

**Итерация 5: Реализация Google Sheets Storage**

Я создам файлы:
- `src/mcp/storage/interface.py` — абстрактный интерфейс
- `src/mcp/storage/sheets.py` — Google Sheets реализация
- Обновлю `src/mcp/config.py` — добавлю настройки для Sheets
- Добавлю тестовые endpoints

Готов начать? 🚀
