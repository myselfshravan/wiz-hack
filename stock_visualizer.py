#!/usr/bin/env python3
"""
Real-time Stock Market Visualizer with WizLight
Monitors live stock prices and changes light color based on performance

🟢 GREEN = Stock price UP from opening
🔴 RED = Stock price DOWN from opening
🟡 YELLOW = Stock price NEUTRAL

Run during market hours (9:15 AM - 3:30 PM IST) for live monitoring.
"""

import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import sys

from wiz_control import WizLight
from stock_analysis import StockDataFetcher
from color_mapping import StockPriceMapper
import stock_config as config


class StockVisualizer:
    """Real-time stock market visualizer with WizLight integration"""

    def __init__(self, light_ip=None, trading_symbol=None):
        """
        Initialize the stock visualizer.

        Args:
            light_ip (str): WizLight IP address (default: from config)
            trading_symbol (str): Stock symbol to monitor (default: from config)
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
        self.opening_price = 0
        self.current_color = config.YELLOW_COLOR
        self.running = False

        # Thread pool for parallel light updates
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

    def initialize(self):
        """Initialize light and fetch opening price"""
        print("=" * 80)
        print(f"📈 Stock Market Visualizer - {self.trading_symbol} ({config.EXCHANGE})")
        print("=" * 80)
        print(f"💡 Light IP: {self.light_ip}")
        print(f"⏱️  Update Interval: {config.UPDATE_INTERVAL}s")
        print(f"🎨 Smooth Transitions: {'Enabled' if config.SMOOTH_TRANSITIONS else 'Disabled'}")
        print()
        print("Color Scheme:")
        print("  🟢 GREEN  = Price UP from opening")
        print("  🔴 RED    = Price DOWN from opening")
        print("  🟡 YELLOW = Price NEUTRAL (within ±₹" + f"{config.PRICE_THRESHOLD:.2f})")
        if config.SMOOTH_TRANSITIONS:
            print(
                f"  ✨ Smooth transitions: {config.TRANSITION_STEPS} steps × {int(config.TRANSITION_DELAY*1000)}ms"
            )
        print("=" * 80)
        print()

        # Turn on light
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
            return False

        print()

        # Check if market is open
        if not self.fetcher.is_market_open():
            print("⚠️  WARNING: Market appears to be closed")
            print("   This visualizer works during market hours: 9:15 AM - 3:30 PM IST")
            print("   Use stock_replay.py for historical data visualization")
            print()
            response = input("Continue anyway? (y/n): ")
            if response.lower() != "y":
                return False
            print()

        # Get opening price
        print("📊 Fetching opening price...")
        try:
            self.opening_price = self.fetcher.get_opening_price(self.trading_symbol)

            if not self.opening_price:
                print("❌ Failed to fetch opening price")
                print("   Please check:")
                print("   1. Your GROWW_AUTH_TOKEN in .env file")
                print("   2. Stock symbol is correct in stock_config.py")
                print("   3. Internet connection")
                return False

            # Also get current quote for more info
            quote = self.fetcher.get_quote(self.trading_symbol)
            if quote:
                print(f"✅ Today's Open: ₹{self.opening_price:.2f}")
                print(f"   Previous Close: ₹{quote['close']:.2f}")
                print(f"   Current LTP: ₹{quote['ltp']:.2f}")
                print()
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

        print("=" * 80)
        print()
        return True

    def run(self):
        """Main monitoring loop"""
        if not self.initialize():
            return

        print("🚀 Starting live monitoring...")
        print("   Press Ctrl+C to stop")
        print()

        self.running = True
        error_count = 0
        max_errors = 5

        try:
            while self.running:
                try:
                    # Fetch current price
                    current_price = self.fetcher.get_ltp(self.trading_symbol)

                    if current_price is None:
                        error_count += 1
                        if error_count >= max_errors:
                            print(f"\n❌ Too many errors ({max_errors}). Stopping...")
                            break
                        time.sleep(config.UPDATE_INTERVAL)
                        continue

                    # Reset error count on success
                    error_count = 0

                    # Calculate day change
                    day_change = current_price - self.opening_price
                    day_change_perc = (day_change / self.opening_price) * 100

                    # Get color from mapper
                    r, g, b, brightness = self.mapper.map(day_change, day_change_perc)
                    target_color = (r, g, b)

                    # Update light if color changed
                    if target_color != self.current_color:
                        self.smooth_transition(target_color, brightness)

                    # Get color name for display
                    color_name = self.mapper.get_color_name(day_change)

                    # Format output
                    change_symbol = "+" if day_change >= 0 else ""
                    change_arrow = "↑" if day_change >= 0 else "↓"
                    timestamp = datetime.now().strftime("%H:%M:%S")

                    # Print status line
                    print(
                        f"[{timestamp}] {self.trading_symbol} | "
                        f"Price: ₹{current_price:.2f} | "
                        f"Change: {change_symbol}₹{day_change:.2f} "
                        f"({change_symbol}{day_change_perc:.2f}%) {change_arrow} | "
                        f"Light: {color_name} ({brightness}%)"
                    )

                    # Wait before next update
                    time.sleep(config.UPDATE_INTERVAL)

                except KeyboardInterrupt:
                    raise  # Re-raise to handle in outer try-except
                except Exception as e:
                    error_count += 1
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] ⚠️  Error: {e}")

                    if error_count >= max_errors:
                        print(f"\n❌ Too many errors ({max_errors}). Stopping...")
                        break

                    time.sleep(config.UPDATE_INTERVAL)

        except KeyboardInterrupt:
            print("\n")
            print("=" * 80)
            print("🛑 Stopping monitor...")

        finally:
            # Reset light to yellow on exit
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
            print("✅ Monitor stopped")
            print("=" * 80)

    def stop(self):
        """Stop the visualizer"""
        self.running = False


def main():
    """Main entry point"""
    # Check if custom arguments provided
    import argparse

    parser = argparse.ArgumentParser(description="Real-time stock market visualizer")
    parser.add_argument(
        "--stock",
        type=str,
        help=f"Stock symbol to monitor (default: {config.TRADING_SYMBOL})",
    )
    parser.add_argument(
        "--light", type=str, help=f"Light IP address (default: {config.LIGHT_IP})"
    )

    args = parser.parse_args()

    # Create and run visualizer
    visualizer = StockVisualizer(
        light_ip=args.light, trading_symbol=args.stock
    )

    try:
        visualizer.run()
    except Exception as e:
        print(f"\n❌ Fatal Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
