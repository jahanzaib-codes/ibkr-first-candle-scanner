from dataclasses import dataclass
from typing import Dict, Any


# Application Version
APP_VERSION = "1.0.0"
APP_NAME = "IBKR First Candle Market Scanner"

# Default Connection Settings
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT_PAPER = 7497
DEFAULT_PORT_LIVE = 7496
DEFAULT_CLIENT_ID = 1

# Scanner Defaults
DEFAULT_EXCHANGE = "BOTH"
DEFAULT_TIMEFRAME = 2  # minutes
DEFAULT_MIN_PRICE = 0.0
DEFAULT_MAX_PRICE = 100.0
DEFAULT_MIN_MARKET_CAP = 0.0  # billions
DEFAULT_MAX_MARKET_CAP = 100.0  # billions
DEFAULT_MIN_VOLUME = 100000
DEFAULT_SCAN_INTERVAL = 30  # seconds

# Market Hours (US Eastern Time)
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MINUTE = 30
MARKET_CLOSE_HOUR = 16
MARKET_CLOSE_MINUTE = 0

# Scanner Limits
MAX_SCANNER_RESULTS = 50  # IBKR limit
MAX_ACTIVE_SCANS = 10  # IBKR limit

# Available Timeframes
AVAILABLE_TIMEFRAMES = [1, 2, 3, 5, 10, 15, 30, 60]

# GUI Theme
GUI_THEME = "dark"
GUI_COLOR_THEME = "blue"

# Colors
COLOR_BULLISH = "#28a745"
COLOR_BEARISH = "#dc3545"
COLOR_NEUTRAL = "#6c757d"

# Logging
LOG_FILE = "scanner.log"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
