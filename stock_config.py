"""
Stock Market Visualizer Configuration
Centralized config for all stock-related settings
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# =============================================================================
# GROWW API CONFIGURATION
# =============================================================================
# Get API token from environment variable
API_AUTH_TOKEN = os.getenv("GROWW_AUTH_TOKEN")

# =============================================================================
# WIZLIGHT CONFIGURATION
# =============================================================================
# Your WizLight IP address (find with: python wiz_control.py discover)
LIGHT_IP = "192.168.1.52"  # Default to first discovered light

# Light brightness (0-100)
BRIGHTNESS = 70

# =============================================================================
# STOCK CONFIGURATION
# =============================================================================
# Stock to monitor (NSE symbols: HDFCBANK, RELIANCE, TCS, INFY, etc.)
TRADING_SYMBOL = "HDFCBANK"

# Exchange (NSE or BSE)
EXCHANGE = "NSE"

# Exchange token from data/instrument.csv
# Common tokens:
#   HDFCBANK: 1333
#   RELIANCE: 2885
#   TCS: 11536
#   INFY: 1594
#   TATAMOTORS: 884
EXCHANGE_TOKEN = "1333"  # Default: HDFCBANK

# =============================================================================
# UPDATE INTERVALS
# =============================================================================
# Seconds between price updates (for live mode)
# Recommended: 1-5 seconds (Groww API allows 10 req/sec)
UPDATE_INTERVAL = 1

# Replay speed multiplier for historical data
# 20x means 1 minute of market data plays in 3 seconds
# Full day (375 minutes) plays in ~19 minutes at 20x
REPLAY_SPEED = 20

# =============================================================================
# COLOR SETTINGS
# =============================================================================
# RGB color tuples (0-255 for each channel)
# Softer colors provide smoother transitions

# Price going UP from opening
GREEN_COLOR = (0, 255, 100)

# Price going DOWN from opening
RED_COLOR = (255, 50, 0)

# Price NEUTRAL (unchanged from opening)
YELLOW_COLOR = (255, 200, 0)

# =============================================================================
# SMOOTH TRANSITION SETTINGS
# =============================================================================
# Enable smooth color transitions (highly recommended!)
SMOOTH_TRANSITIONS = True

# Number of interpolation steps for transitions
# Higher = smoother but slower (10-20 is good)
TRANSITION_STEPS = 10

# Delay between transition steps in seconds
# Total transition time = TRANSITION_STEPS * TRANSITION_DELAY
# 10 steps * 0.05s = 0.5 second total transition
TRANSITION_DELAY = 0.05

# =============================================================================
# PRICE CHANGE THRESHOLDS
# =============================================================================
# Minimum absolute price change (in ₹) to trigger color change
# This prevents flickering on tiny fluctuations
# For expensive stocks (>1000): use 0.50
# For cheaper stocks (<500): use 0.10
PRICE_THRESHOLD = 0.10

# =============================================================================
# HISTORICAL REPLAY SETTINGS
# =============================================================================
# Candle interval in minutes for historical data
# Valid values: 1, 5, 10, 60, 240, 1440
# 1 = 1-minute candles (most detailed)
# 5 = 5-minute candles (balanced)
# 60 = 1-hour candles (broader trends)
INTERVAL_MINUTES = 1

# How many hours of historical data to fetch
# Full market day = 6.25 hours (9:15 AM - 3:30 PM)
# Recommended: 2-6 hours for interesting replays
HOURS_TO_FETCH = 4

# =============================================================================
# DISPLAY SETTINGS
# =============================================================================
# Show volume in terminal output
SHOW_VOLUME = True

# Show OHLC (Open, High, Low, Close) data
SHOW_OHLC = True

# Show per-candle change (for historical replay)
SHOW_CANDLE_CHANGE = True

# =============================================================================
# ADVANCED SETTINGS (don't change unless you know what you're doing)
# =============================================================================
# Groww API rate limits
API_RATE_LIMIT_PER_SEC = 10
API_RATE_LIMIT_PER_MIN = 300

# Market hours (IST)
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MINUTE = 15
MARKET_CLOSE_HOUR = 15
MARKET_CLOSE_MINUTE = 30

# Timezone
TIMEZONE = "Asia/Kolkata"

# =============================================================================
# QUICK PRESETS
# =============================================================================
# Uncomment a preset to quickly switch configurations

# # PRESET: Volatile Stock (High-risk tech stocks)
# TRADING_SYMBOL = "ADANIPORTS"
# EXCHANGE_TOKEN = "15083"
# PRICE_THRESHOLD = 1.0  # Higher threshold for volatile stocks

# # PRESET: Blue Chip (Stable, less volatile)
# TRADING_SYMBOL = "TCS"
# EXCHANGE_TOKEN = "11536"
# PRICE_THRESHOLD = 0.50

# # PRESET: Fast Replay (Full day in ~6 minutes)
# REPLAY_SPEED = 60
# INTERVAL_MINUTES = 5

# # PRESET: Slow Motion (Detailed analysis)
# REPLAY_SPEED = 5
# INTERVAL_MINUTES = 1

# # PRESET: Party Mode (Dramatic colors, instant transitions)
# GREEN_COLOR = (0, 255, 0)  # Pure green
# RED_COLOR = (255, 0, 0)    # Pure red
# YELLOW_COLOR = (255, 255, 0)  # Pure yellow
# SMOOTH_TRANSITIONS = False
# BRIGHTNESS = 100

print(f"📈 Stock Config Loaded: {TRADING_SYMBOL} on {EXCHANGE}")
print(f"💡 Light IP: {LIGHT_IP}")
print(f"⚙️  Smooth Transitions: {'Enabled' if SMOOTH_TRANSITIONS else 'Disabled'}")
