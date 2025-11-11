"""
Stock Market Data Fetching and Analysis
Handles all Groww API interactions for stock price monitoring
"""

from datetime import datetime, timedelta
from growwapi import GrowwAPI
import stock_config as config
import time


class StockDataFetcher:
    """Handles fetching and analyzing stock market data from Groww API"""

    def __init__(self, auth_token=None):
        """
        Initialize the stock data fetcher.

        Args:
            auth_token (str): Groww API authentication token
        """
        self.auth_token = auth_token or config.API_AUTH_TOKEN
        self.groww = GrowwAPI(self.auth_token)
        self.last_request_time = 0
        self.min_request_interval = 1.0 / config.API_RATE_LIMIT_PER_SEC

    def _rate_limit_check(self):
        """Ensure we don't exceed API rate limits"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def get_ltp(self, trading_symbol=None, exchange=None):
        """
        Get Last Traded Price (LTP) for a stock.

        Args:
            trading_symbol (str): Stock symbol (e.g., "HDFCBANK")
            exchange (str): Exchange name (e.g., "NSE")

        Returns:
            float: Last traded price or None if error

        Example:
            >>> fetcher.get_ltp("HDFCBANK", "NSE")
            1650.50
        """
        trading_symbol = trading_symbol or config.TRADING_SYMBOL
        exchange = exchange or config.EXCHANGE

        try:
            self._rate_limit_check()

            exchange_symbol = f"{exchange}_{trading_symbol}"
            ltp_response = self.groww.get_ltp(
                segment=self.groww.SEGMENT_CASH,
                exchange_trading_symbols=exchange_symbol,
            )

            if ltp_response and exchange_symbol in ltp_response:
                return ltp_response[exchange_symbol]

            return None

        except Exception as e:
            print(f"Error fetching LTP: {e}")
            return None

    def get_quote(self, trading_symbol=None, exchange=None):
        """
        Get detailed quote for a stock including OHLC data.

        Args:
            trading_symbol (str): Stock symbol
            exchange (str): Exchange name

        Returns:
            dict: Quote data with keys like 'ltp', 'open', 'high', 'low', 'close',
                  'day_change', 'day_change_perc', 'volume', etc.
                  Returns None if error.

        Example:
            >>> quote = fetcher.get_quote("HDFCBANK", "NSE")
            >>> print(quote['ltp'], quote['day_change_perc'])
            1650.50 +1.25%
        """
        trading_symbol = trading_symbol or config.TRADING_SYMBOL
        exchange = exchange or config.EXCHANGE

        try:
            self._rate_limit_check()

            # Map exchange string to Groww constant
            exchange_code = (
                self.groww.EXCHANGE_NSE if exchange == "NSE" else self.groww.EXCHANGE_BSE
            )

            quote_response = self.groww.get_quote(
                exchange=exchange_code,
                segment=self.groww.SEGMENT_CASH,
                trading_symbol=trading_symbol,
            )

            if not quote_response:
                return None

            # Extract relevant data
            ohlc = quote_response.get("ohlc", {})
            ltp_info = quote_response.get("ltp", {})

            return {
                "ltp": ltp_info.get("ltp", 0),
                "open": ohlc.get("open", 0),
                "high": ohlc.get("high", 0),
                "low": ohlc.get("low", 0),
                "close": ohlc.get("close", 0),  # Previous day close
                "day_change": ltp_info.get("dayChange", 0),
                "day_change_perc": ltp_info.get("dayChangePerc", 0),
                "volume": quote_response.get("stats", {}).get("volume", 0),
                "timestamp": datetime.now(),
            }

        except Exception as e:
            print(f"Error fetching quote: {e}")
            return None

    def get_opening_price(self, trading_symbol=None, exchange=None):
        """
        Get today's opening price for a stock.

        Args:
            trading_symbol (str): Stock symbol
            exchange (str): Exchange name

        Returns:
            float: Opening price or None if error
        """
        quote = self.get_quote(trading_symbol, exchange)
        if quote:
            return quote["open"]
        return None

    def calculate_day_change(self, current_price, opening_price):
        """
        Calculate day change from opening price.

        Args:
            current_price (float): Current price
            opening_price (float): Opening price

        Returns:
            dict: Dictionary with 'absolute', 'percentage', and 'direction' keys

        Example:
            >>> fetcher.calculate_day_change(1650.50, 1630.00)
            {'absolute': 20.50, 'percentage': 1.26, 'direction': 'up'}
        """
        if not opening_price or opening_price == 0:
            return {"absolute": 0, "percentage": 0, "direction": "neutral"}

        absolute_change = current_price - opening_price
        percentage_change = (absolute_change / opening_price) * 100

        # Determine direction based on threshold
        if absolute_change > config.PRICE_THRESHOLD:
            direction = "up"
        elif absolute_change < -config.PRICE_THRESHOLD:
            direction = "down"
        else:
            direction = "neutral"

        return {
            "absolute": absolute_change,
            "percentage": percentage_change,
            "direction": direction,
        }

    def get_historical_data(
        self, trading_symbol=None, exchange=None, start_time=None, end_time=None, interval_minutes=None
    ):
        """
        Get historical candle data for a stock.

        Args:
            trading_symbol (str): Stock symbol
            exchange (str): Exchange name
            start_time (datetime): Start time for data
            end_time (datetime): End time for data
            interval_minutes (int): Candle interval (1, 5, 10, 60, 240, 1440)

        Returns:
            list: List of candles, each containing [timestamp, open, high, low, close, volume]
                  Returns None if error

        Example:
            >>> start = datetime(2024, 1, 15, 9, 15)
            >>> end = datetime(2024, 1, 15, 15, 30)
            >>> candles = fetcher.get_historical_data("HDFCBANK", "NSE", start, end, 1)
            >>> print(f"Fetched {len(candles)} 1-minute candles")
        """
        trading_symbol = trading_symbol or config.TRADING_SYMBOL
        exchange = exchange or config.EXCHANGE
        interval_minutes = interval_minutes or config.INTERVAL_MINUTES

        # Default time range: last market day
        if not end_time:
            end_time = datetime.now()

        if not start_time:
            start_time = end_time - timedelta(hours=config.HOURS_TO_FETCH)

        try:
            self._rate_limit_check()

            # Map exchange string to Groww constant
            exchange_code = (
                self.groww.EXCHANGE_NSE if exchange == "NSE" else self.groww.EXCHANGE_BSE
            )

            historical_response = self.groww.get_historical_candle_data(
                trading_symbol=trading_symbol,
                exchange=exchange_code,
                segment=self.groww.SEGMENT_CASH,
                start_time=start_time.strftime("%Y-%m-%d %H:%M:%S"),
                end_time=end_time.strftime("%Y-%m-%d %H:%M:%S"),
                interval_in_minutes=interval_minutes,
            )

            if historical_response and "candles" in historical_response:
                return historical_response["candles"]

            return None

        except Exception as e:
            print(f"Error fetching historical data: {e}")
            return None

    def get_market_day_timerange(self, target_date=None):
        """
        Get the market hours timerange for a given date.

        Args:
            target_date (datetime.date): Date to get timerange for (default: today)

        Returns:
            tuple: (market_start, market_end) datetime objects

        Example:
            >>> start, end = fetcher.get_market_day_timerange()
            >>> print(f"Market hours: {start} to {end}")
            Market hours: 2024-01-15 09:15:00 to 2024-01-15 15:30:00
        """
        if not target_date:
            target_date = datetime.now().date()

        market_start = datetime.combine(
            target_date,
            datetime.strptime(
                f"{config.MARKET_OPEN_HOUR}:{config.MARKET_OPEN_MINUTE}:00", "%H:%M:%S"
            ).time(),
        )

        market_end = datetime.combine(
            target_date,
            datetime.strptime(
                f"{config.MARKET_CLOSE_HOUR}:{config.MARKET_CLOSE_MINUTE}:00", "%H:%M:%S"
            ).time(),
        )

        return market_start, market_end

    def is_market_open(self):
        """
        Check if the market is currently open.

        Returns:
            bool: True if market is open, False otherwise
        """
        now = datetime.now()
        market_start, market_end = self.get_market_day_timerange()

        # Check if current time is within market hours
        # Note: This doesn't account for holidays - you'd need a holiday calendar for that
        is_weekday = now.weekday() < 5  # Monday=0, Friday=4
        is_within_hours = market_start <= now <= market_end

        return is_weekday and is_within_hours


# Example usage and testing
if __name__ == "__main__":
    print("=" * 80)
    print("Stock Data Fetcher Test")
    print("=" * 80)
    print()

    fetcher = StockDataFetcher()

    # Test 1: Check if market is open
    print(f"Market Open Status: {fetcher.is_market_open()}")
    print()

    # Test 2: Get LTP
    print(f"Fetching LTP for {config.TRADING_SYMBOL}...")
    ltp = fetcher.get_ltp()
    if ltp:
        print(f"✓ Last Traded Price: ₹{ltp:.2f}")
    else:
        print("✗ Failed to fetch LTP")
    print()

    # Test 3: Get Quote
    print(f"Fetching detailed quote for {config.TRADING_SYMBOL}...")
    quote = fetcher.get_quote()
    if quote:
        print(f"✓ Quote Data:")
        print(f"  LTP: ₹{quote['ltp']:.2f}")
        print(f"  Open: ₹{quote['open']:.2f}")
        print(f"  High: ₹{quote['high']:.2f}")
        print(f"  Low: ₹{quote['low']:.2f}")
        print(f"  Day Change: ₹{quote['day_change']:.2f} ({quote['day_change_perc']:.2f}%)")
        print(f"  Volume: {quote['volume']:,}")
    else:
        print("✗ Failed to fetch quote")
    print()

    # Test 4: Calculate day change
    if quote:
        change = fetcher.calculate_day_change(quote["ltp"], quote["open"])
        print(f"Day Change Analysis:")
        print(f"  Absolute: ₹{change['absolute']:.2f}")
        print(f"  Percentage: {change['percentage']:.2f}%")
        print(f"  Direction: {change['direction'].upper()}")
        print()

    # Test 5: Get historical data (last 1 hour)
    print(f"Fetching historical data (last 1 hour)...")
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=1)
    candles = fetcher.get_historical_data(start_time=start_time, end_time=end_time, interval_minutes=1)

    if candles:
        print(f"✓ Fetched {len(candles)} 1-minute candles")
        if len(candles) > 0:
            first_candle = candles[0]
            last_candle = candles[-1]
            print(f"  First candle: {datetime.fromtimestamp(first_candle[0]).strftime('%H:%M:%S')}")
            print(f"  Last candle: {datetime.fromtimestamp(last_candle[0]).strftime('%H:%M:%S')}")
            print(f"  Price range: ₹{min(c[3] for c in candles):.2f} - ₹{max(c[2] for c in candles):.2f}")
    else:
        print("✗ Failed to fetch historical data (may be outside market hours)")

    print()
    print("=" * 80)
    print("Test Complete")
    print("=" * 80)
