#!/usr/bin/env python3
"""
Stock Market Historical Replay with WizLight
Replays historical stock data with smooth light transitions

Works ANYTIME - no need to wait for market hours!
Perfect for testing, demos, and analyzing past market movements.

🟢 GREEN = Stock price UP from opening
🔴 RED = Stock price DOWN from opening
🟡 YELLOW = Stock price NEUTRAL
"""

import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import sys

from wiz_control import WizLight
from stock_analysis import StockDataFetcher
from color_mapping import StockPriceMapper
import stock_config as config


class StockReplay:
    """Historical stock data replay with WizLight visualization"""

    def __init__(self, light_ip=None, trading_symbol=None):
        """
        Initialize the stock replay visualizer.

        Args:
            light_ip (str): WizLight IP address (default: from config)
            trading_symbol (str): Stock symbol to replay (default: from config)
        """
        self.light_ip = light_ip or config.LIGHT_IP
        self.trading_symbol = trading_symbol or config.TRADING_SYMBOL

        # Initialize components
        self.light = WizLight(self.light_ip)
        self.fetcher = StockDataFetcher()
        self.mapper = StockPriceMapper(
            min_brightness=30,
            max_brightness=config.BRIGHTNESS,
            green_color=config.GREEN_COLOR,
            red_color=config.RED_COLOR,
            yellow_color=config.YELLOW_COLOR,
            threshold=config.PRICE_THRESHOLD,
        )

        # State tracking
        self.current_color = config.YELLOW_COLOR

        # Thread pool for parallel operations
        self.executor = ThreadPoolExecutor(max_workers=2)

    def smooth_transition(self, target_color, target_brightness):
        """
        Smoothly transition from current color to target color.

        Args:
            target_color (tuple): Target (r, g, b) color
            target_brightness (int): Target brightness (0-100)
        """
        if not config.SMOOTH_TRANSITIONS:
            # Instant transition
            self.light.set_color(
                target_color[0], target_color[1], target_color[2], target_brightness
            )
            self.current_color = target_color
            return

        # Smooth RGB interpolation
        from_color = self.current_color

        for i in range(config.TRANSITION_STEPS + 1):
            ratio = i / config.TRANSITION_STEPS

            # Interpolate RGB values
            r = int(from_color[0] + (target_color[0] - from_color[0]) * ratio)
            g = int(from_color[1] + (target_color[1] - from_color[1]) * ratio)
            b = int(from_color[2] + (target_color[2] - from_color[2]) * ratio)

            # Set color
            try:
                self.light.set_color(r, g, b, target_brightness)
            except Exception:
                pass  # Ignore network errors during transition

            time.sleep(config.TRANSITION_DELAY)

        self.current_color = target_color

    def get_market_day_timerange(self):
        """
        Get the market day timerange for historical data.
        Auto-detects last market day if current time is before market open.

        Returns:
            tuple: (start_time, end_time) datetime objects
        """
        current_time = datetime.now()
        today = current_time.date()

        # If before market open today, use previous day
        if current_time.hour < config.MARKET_OPEN_HOUR or (
            current_time.hour == config.MARKET_OPEN_HOUR
            and current_time.minute < config.MARKET_OPEN_MINUTE
        ):
            market_day = today - timedelta(days=1)
        else:
            market_day = today

        # Market hours timerange
        market_start = datetime.combine(
            market_day,
            datetime.strptime(
                f"{config.MARKET_OPEN_HOUR}:{config.MARKET_OPEN_MINUTE}:00", "%H:%M:%S"
            ).time(),
        )

        market_end = datetime.combine(
            market_day,
            datetime.strptime(
                f"{config.MARKET_CLOSE_HOUR}:{config.MARKET_CLOSE_MINUTE}:00", "%H:%M:%S"
            ).time(),
        )

        # Calculate timerange based on config
        end_time = market_end
        start_time = end_time - timedelta(hours=config.HOURS_TO_FETCH)

        # Don't go before market open
        if start_time < market_start:
            start_time = market_start

        return start_time, end_time

    def run(self):
        """Main replay loop"""
        print("=" * 80)
        print(f"📈 Historical Stock Replay - {self.trading_symbol} ({config.EXCHANGE})")
        print("=" * 80)
        print(f"💡 Light IP: {self.light_ip}")
        print(f"⚡ Replay Speed: {config.REPLAY_SPEED}x")
        print(
            f"📊 Fetching {config.HOURS_TO_FETCH} hours of {config.INTERVAL_MINUTES}-min candles"
        )
        print()
        print("Color Scheme:")
        print("  🟢 GREEN  = Price UP from opening")
        print("  🔴 RED    = Price DOWN from opening")
        print("  🟡 YELLOW = Price NEUTRAL")
        if config.SMOOTH_TRANSITIONS:
            print(
                f"  ✨ Smooth transitions: {config.TRANSITION_STEPS} steps × {int(config.TRANSITION_DELAY*1000)}ms"
            )
        print("=" * 80)
        print()

        # Initialize light
        print("🔌 Initializing light...")
        try:
            self.light.set_state(True)
            time.sleep(0.5)
            self.light.set_color(
                config.YELLOW_COLOR[0],
                config.YELLOW_COLOR[1],
                config.YELLOW_COLOR[2],
                config.BRIGHTNESS,
            )
            print("✅ Light ready!")
        except Exception as e:
            print(f"❌ Error initializing light: {e}")
            return

        print()

        # Get timerange
        start_time, end_time = self.get_market_day_timerange()

        print(
            f"📅 Fetching data from {start_time.strftime('%Y-%m-%d %H:%M')} "
            f"to {end_time.strftime('%Y-%m-%d %H:%M')}..."
        )
        print()

        try:
            # Fetch historical data
            candles = self.fetcher.get_historical_data(
                trading_symbol=self.trading_symbol,
                start_time=start_time,
                end_time=end_time,
                interval_minutes=config.INTERVAL_MINUTES,
            )

            if not candles:
                print("❌ No historical data found!")
                print("   This could mean:")
                print("   1. Market is closed and data for today isn't available yet")
                print("   2. Weekend/holiday - try running on a weekday")
                print("   3. API authentication issue")
                print("   4. Stock symbol might be incorrect")
                return

            # Get opening price from first candle
            opening_price = candles[0][1]  # [timestamp, open, high, low, close, volume]

            print(f"✅ Fetched {len(candles)} candles")
            print(f"📊 Opening Price: ₹{opening_price:.2f}")
            print(f"⏱️  Replay Duration: ~{len(candles) * config.INTERVAL_MINUTES / config.REPLAY_SPEED / 60:.1f} minutes")
            print("=" * 80)
            print()
            print("🎬 Starting replay in 3 seconds...")
            time.sleep(3)
            print()

            # Replay candles
            for i, candle in enumerate(candles):
                timestamp_epoch, open_p, high_p, low_p, close_p, volume = candle

                # Calculate day change from opening
                day_change = close_p - opening_price
                day_change_perc = (day_change / opening_price) * 100

                # Get color from mapper
                r, g, b, brightness = self.mapper.map(day_change, day_change_perc)
                target_color = (r, g, b)

                # Update light
                self.smooth_transition(target_color, brightness)

                # Get color name for display
                color_name = self.mapper.get_color_name(day_change)

                # Format timestamp
                candle_time = datetime.fromtimestamp(timestamp_epoch)

                # Format output
                change_symbol = "+" if day_change >= 0 else ""
                change_arrow = "↑" if day_change >= 0 else "↓"

                output = (
                    f"[{candle_time.strftime('%H:%M:%S')}] {self.trading_symbol} | "
                    f"Close: ₹{close_p:.2f} | "
                    f"Change: {change_symbol}₹{day_change:.2f} "
                    f"({change_symbol}{day_change_perc:.2f}%) {change_arrow}"
                )

                # Add optional data
                if config.SHOW_OHLC:
                    output += f" | O:{open_p:.2f} H:{high_p:.2f} L:{low_p:.2f}"

                if config.SHOW_VOLUME:
                    output += f" | Vol: {int(volume):,}"

                # Add candle change if enabled
                if config.SHOW_CANDLE_CHANGE:
                    candle_change = close_p - open_p
                    candle_symbol = "+" if candle_change >= 0 else ""
                    output += f" | Candle: {candle_symbol}₹{candle_change:.2f}"

                # Add light info
                output += f" | {color_name} ({brightness}%)"

                print(output)

                # Wait before next candle (unless it's the last one)
                if i < len(candles) - 1:
                    wait_time = (config.INTERVAL_MINUTES * 60) / config.REPLAY_SPEED
                    time.sleep(wait_time)

            print()
            print("=" * 80)
            print(f"✅ Replay complete! Showed {len(candles)} candles")
            final_price = candles[-1][4]
            final_change = final_price - opening_price
            final_change_perc = (final_change / opening_price) * 100
            print(
                f"📊 Final Price: ₹{final_price:.2f} "
                f"({'+'if final_change >= 0 else ''}{final_change:.2f}, "
                f"{'+'if final_change_perc >= 0 else ''}{final_change_perc:.2f}%)"
            )
            print("=" * 80)

        except KeyboardInterrupt:
            print("\n\n" + "=" * 80)
            print("🛑 Replay stopped by user")
            print("=" * 80)

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback

            traceback.print_exc()

        finally:
            # Reset light to yellow
            try:
                self.light.set_color(
                    config.YELLOW_COLOR[0],
                    config.YELLOW_COLOR[1],
                    config.YELLOW_COLOR[2],
                    config.BRIGHTNESS,
                )
                print("💡 Light set to yellow")
            except Exception:
                pass

            self.executor.shutdown(wait=False)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Historical stock replay visualizer")
    parser.add_argument(
        "--stock",
        type=str,
        help=f"Stock symbol to replay (default: {config.TRADING_SYMBOL})",
    )
    parser.add_argument(
        "--light", type=str, help=f"Light IP address (default: {config.LIGHT_IP})"
    )
    parser.add_argument(
        "--hours",
        type=int,
        help=f"Hours of data to fetch (default: {config.HOURS_TO_FETCH})",
    )
    parser.add_argument(
        "--speed",
        type=int,
        help=f"Replay speed multiplier (default: {config.REPLAY_SPEED}x)",
    )

    args = parser.parse_args()

    # Override config if arguments provided
    if args.hours:
        config.HOURS_TO_FETCH = args.hours
    if args.speed:
        config.REPLAY_SPEED = args.speed

    # Create and run replay
    replay = StockReplay(light_ip=args.light, trading_symbol=args.stock)

    try:
        replay.run()
    except Exception as e:
        print(f"\n❌ Fatal Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
