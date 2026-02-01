"""Application constants - single source of truth for magic numbers."""

# HTTP Client
REQUEST_TIMEOUT = 30  # seconds
MAX_RETRIES = 3

# Telegram
TELEGRAM_MAX_MESSAGE_LENGTH = 4096
MESSAGE_CHUNK_DELAY = 0.5  # seconds between chunks

# Google Sheets
WORKSHEET_EXPENSES = "Траты и бюджет"
WORKSHEET_LIMITS = "Лимиты"

# Progress bar
PROGRESS_BAR_FILLED = "█"
PROGRESS_BAR_EMPTY = "░"

# Rate limiting
RATE_LIMIT_REQUESTS = 10
RATE_LIMIT_PERIOD = 60  # seconds
