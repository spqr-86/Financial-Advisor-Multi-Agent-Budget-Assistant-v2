"""Application constants - single source of truth for magic numbers."""

# HTTP Client
REQUEST_TIMEOUT = 30  # seconds
MAX_RETRIES = 3

# Cache TTL (seconds)
CACHE_TTL_LIMITS = 60
CACHE_TTL_STATS = 30
CACHE_TTL_HEALTH = 10

# Telegram
TELEGRAM_MAX_MESSAGE_LENGTH = 4096
MESSAGE_CHUNK_DELAY = 0.5  # seconds between chunks

# Google Sheets
WORKSHEET_EXPENSES = "Траты и бюджет"
WORKSHEET_LIMITS = "Лимиты"

# Progress bar
PROGRESS_BAR_WIDTH = 10
PROGRESS_BAR_FILLED = "█"
PROGRESS_BAR_EMPTY = "░"

# Quick amount buttons
QUICK_AMOUNTS = [50, 100, 200, 500, 1000, 2000, 5000]

# Rate limiting
RATE_LIMIT_REQUESTS = 10
RATE_LIMIT_PERIOD = 60  # seconds
