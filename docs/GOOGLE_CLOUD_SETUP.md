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

**Iteration 9 реализует полный Cloud Run deployment с Secret Manager.**

См. детальную инструкцию в разделе **"Шаг 9: Cloud Run Deployment"** ниже.

---

## Шаг 9: Cloud Run Deployment (Iteration 9)

> Этот раздел описывает развертывание всех трех сервисов (Bot, API, MCP) в Google Cloud Run с использованием Secret Manager для безопасного хранения credentials.

### 9.1 Предварительные требования

**Убедитесь, что установлены:**
- ✅ gcloud CLI (Google Cloud SDK)
- ✅ Docker для сборки образов
- ✅ Локально работает `docker-compose up` (для тестирования)

**Проверка gcloud:**
```bash
gcloud --version
gcloud auth list
```

**Если gcloud не установлен:**
```bash
# macOS
brew install google-cloud-sdk

# Linux/WSL
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

### 9.2 Аутентификация и настройка проекта

```bash
# Войти в Google Cloud
gcloud auth login

# Установить проект по умолчанию
gcloud config set project budget-assistant

# Проверить текущий проект
gcloud config get-value project
```

### 9.3 Включение необходимых API

```bash
# Cloud Run API
gcloud services enable run.googleapis.com

# Container Registry (для хранения Docker образов)
gcloud services enable containerregistry.googleapis.com

# Secret Manager API (для безопасного хранения credentials)
gcloud services enable secretmanager.googleapis.com
```

⏱️ Подождите 30-60 секунд после включения API.

### 9.4 Настройка Docker для Google Container Registry

```bash
# Настроить Docker для аутентификации с GCR
gcloud auth configure-docker

# Проверка
docker info | grep -A 5 "Registry"
```

### 9.5 Создание секретов в Secret Manager

**Iteration 9 автоматизирует этот процесс**, но можно создать вручную:

#### 9.5.1 Service Account JSON

```bash
# Создать секрет из файла service-account.json
gcloud secrets create service-account-json \
    --data-file=./service-account.json \
    --replication-policy=automatic
```

#### 9.5.2 Telegram Bot Token

```bash
# Создать секрет из переменной окружения
echo -n "${TELEGRAM_BOT_TOKEN}" | gcloud secrets create telegram-bot-token \
    --data-file=- \
    --replication-policy=automatic
```

#### 9.5.3 Google API Key (Gemini)

```bash
echo -n "${GOOGLE_API_KEY}" | gcloud secrets create google-api-key \
    --data-file=- \
    --replication-policy=automatic
```

#### 9.5.4 Webhook Secret

```bash
echo -n "${WEBHOOK_SECRET}" | gcloud secrets create webhook-secret \
    --data-file=- \
    --replication-policy=automatic
```

**Проверить созданные секреты:**
```bash
gcloud secrets list
```

**Вывод:**
```
NAME                    CREATED              REPLICATION_POLICY  LOCATIONS
service-account-json    2025-12-09T10:00:00  automatic           -
telegram-bot-token      2025-12-09T10:01:00  automatic           -
google-api-key          2025-12-09T10:02:00  automatic           -
webhook-secret          2025-12-09T10:03:00  automatic           -
```

### 9.6 Автоматический деплой всех сервисов

**Iteration 9 предоставляет скрипт `deploy_all.sh`** для автоматического развертывания:

```bash
# Установить переменные окружения
export GCP_PROJECT_ID=budget-assistant
export GCP_REGION=us-central1
export TELEGRAM_BOT_TOKEN=your-token
export GOOGLE_API_KEY=your-gemini-key
export WEBHOOK_SECRET=your-secret
export GOOGLE_SHEETS_SPREADSHEET_ID=1a2b3c4d5e6f7g8h9i0
export TELEGRAM_ADMIN_IDS=123456789,987654321

# Запустить деплой
./scripts/deploy_all.sh
```

**Скрипт выполнит:**
1. ✅ Проверит/создаст секреты в Secret Manager
2. ✅ Соберет и загрузит Docker образ для MCP Service
3. ✅ Развернет MCP на Cloud Run → получит URL
4. ✅ Соберет и развернет API Gateway с MCP_API_URL
5. ✅ Соберет и развернет Bot с BUDGET_API_URL
6. ✅ Автоматически настроит Telegram webhook

⏱️ **Время деплоя:** ~5-10 минут (первый раз, затем быстрее).

### 9.7 Ручной деплой отдельных сервисов

**Если нужно развернуть только один сервис:**

#### MCP Service (первым)
```bash
export GOOGLE_SHEETS_SPREADSHEET_ID=your-spreadsheet-id
export GEMINI_MODEL=gemini-flash-latest
./scripts/deploy_mcp.sh
```

#### API Gateway (вторым)
```bash
# Получить URL MCP сервиса
export MCP_API_URL=$(gcloud run services describe budget-mcp \
    --region us-central1 --format 'value(status.url)')

./scripts/deploy_api.sh
```

#### Bot (третьим)
```bash
# Получить URL API сервиса
export BUDGET_API_URL=$(gcloud run services describe budget-api \
    --region us-central1 --format 'value(status.url)')

export TELEGRAM_ADMIN_IDS=123456789
./scripts/deploy_bot.sh

# Настроить webhook вручную
BOT_URL=$(gcloud run services describe budget-bot \
    --region us-central1 --format 'value(status.url)')

curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook?url=${BOT_URL}/webhook&secret_token=${WEBHOOK_SECRET}"
```

### 9.8 Проверка развертывания

#### 9.8.1 Список сервисов
```bash
gcloud run services list --region us-central1
```

**Ожидаемый вывод:**
```
SERVICE      REGION        URL                                    LAST DEPLOYED
budget-mcp   us-central1   https://budget-mcp-xxx.run.app         2025-12-09
budget-api   us-central1   https://budget-api-xxx.run.app         2025-12-09
budget-bot   us-central1   https://budget-bot-xxx.run.app         2025-12-09
```

#### 9.8.2 Проверка health endpoints
```bash
# MCP
curl https://budget-mcp-xxx.run.app/health

# API
curl https://budget-api-xxx.run.app/health

# Bot
curl https://budget-bot-xxx.run.app/health
```

**Все должны вернуть:** `{"status":"healthy",...}`

#### 9.8.3 Проверка Telegram webhook
```bash
curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo"
```

**Должно показать:**
```json
{
  "ok": true,
  "result": {
    "url": "https://budget-bot-xxx.run.app/webhook",
    "has_custom_certificate": false,
    "pending_update_count": 0,
    "max_connections": 40
  }
}
```

### 9.9 Просмотр логов

```bash
# Логи MCP Service (Gemini AI, Google Sheets)
gcloud run logs tail budget-mcp --region us-central1

# Логи API Gateway
gcloud run logs tail budget-api --region us-central1

# Логи Bot (Telegram webhook)
gcloud run logs tail budget-bot --region us-central1

# Последние 100 строк с фильтром
gcloud run logs tail budget-mcp --limit 100 | grep ERROR
```

### 9.10 Обновление секретов

**Если нужно изменить токен или ключ:**

```bash
# Обновить значение секрета
echo -n "new-token-value" | gcloud secrets versions add telegram-bot-token \
    --data-file=-

# Пересоздать деплоймент сервиса (для подгрузки нового секрета)
gcloud run services update budget-bot --region us-central1
```

**Для service-account.json:**
```bash
# Обновить JSON
gcloud secrets versions add service-account-json \
    --data-file=./service-account.json

# Перезапустить MCP сервис
gcloud run services update budget-mcp --region us-central1
```

### 9.11 Мониторинг стоимости

**Проверить расходы:**
```bash
# Перейти в Cloud Console → Billing → Reports
# https://console.cloud.google.com/billing/
```

**Ожидаемые расходы (Iteration 9):**
- Cloud Run (легкая нагрузка ~1000 сообщений/месяц): **Бесплатно** (в пределах free tier)
- Secret Manager (4 секрета): **$0.36/месяц**
- Container Registry (<500MB): **Бесплатно** (в пределах free tier)

**Итого: < $1/месяц** 💰

### 9.12 Откат к предыдущей версии

**Если что-то сломалось после деплоя:**

```bash
# Посмотреть список ревизий
gcloud run revisions list --service budget-bot --region us-central1

# Откатить трафик на предыдущую ревизию
gcloud run services update-traffic budget-bot \
    --to-revisions=budget-bot-00002-abc=100 \
    --region us-central1
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

## 🎯 Следующие шаги

### Для локальной разработки (Iteration 1-8 завершены)

После успешной настройки Google Cloud вы можете:

1. **Запустить все сервисы локально:**
   ```bash
   docker-compose up --build
   ```

2. **Тестировать бота в Telegram:**
   ```bash
   poetry run python -m src.bot.run_polling
   ```

3. **Проверить интеграцию с Google Sheets:**
   - Отправить боту: "купил хлеб 50 рублей"
   - Проверить, что запись появилась в таблице

### Для production деплоя (Iteration 9)

**Развернуть в Google Cloud Run:**

1. Установить и настроить gcloud CLI (см. Шаг 9.1-9.4)
2. Создать секреты в Secret Manager (см. Шаг 9.5)
3. Запустить автоматический деплой:
   ```bash
   ./scripts/deploy_all.sh
   ```

**Iteration 9 включает:**
- ✅ docker-compose для локальной разработки
- ✅ Secret Manager для безопасного хранения credentials
- ✅ Автоматический деплой всех 3 сервисов
- ✅ Настройка Telegram webhook
- ✅ Полная документация Cloud Run deployment

### Iteration 10 (в разработке)

Следующая итерация добавит:
- 📊 Cloud Monitoring и Error Reporting
- 🔒 VPC networking для internal-only сервисов
- 🏗️ Infrastructure as Code с Terraform
- 🚀 CI/CD автоматизация через GitHub Actions

Готовы к деплою? 🚀
