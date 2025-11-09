#!/usr/bin/env python3
"""
Audio-reactive Wiz light controller.
Makes your Wiz lights react to music from your microphone in real-time.

Usage:
    python audio_visualizer.py [--mode MODE] [--lights all|IP]

Modes:
    - frequency_bands: Bass→Red, Mids→Green, Treble→Blue (default)
    - energy: Warm/cool colors based on energy level
    - rainbow: Rainbow colors based on dominant frequency
    - multi: Different lights show different frequency bands
"""

import sounddevice as sd
import sys
import argparse
import time
import threading
import queue
from concurrent.futures import ThreadPoolExecutor
from wiz_control import WizLight
from audio_analysis import AudioAnalyzer
from color_mapping import (
    FrequencyToRGBMapper,
    MultiLightMapper,
    PulseModeMapper,
    StrobeModeMapper,
    SpectrumPulseMapper,
    SimplePulseMapper,
    StereoSplitMapper,
    ComplementaryPulseMapper,
    BeatLeaderFollowerMapper,
    FrequencyDanceMapper,
    SpectrumGradientMapper,
)


class AudioVisualizer:
    """Audio-reactive light controller."""

    def __init__(
        self,
        light_ips,
        mode="frequency_bands",
        sample_rate=22050,
        buffer_size=2048,
        smoothing=0.3,
        brightness_boost=1.5,
        sensitivity=1.0,
    ):
        """
        Initialize the visualizer.

        Args:
            light_ips: List of light IP addresses
            mode: Color mapping mode
            sample_rate: Audio sample rate
            buffer_size: Audio buffer size
            smoothing: Smoothing factor for colors
            brightness_boost: Brightness multiplier (default: 1.5)
            sensitivity: How dramatically brightness reacts (default: 1.0)
        """
        self.light_ips = light_ips
        self.lights = [WizLight(ip) for ip in light_ips]
        self.mode = mode
        self.running = False

        # Audio analysis
        self.analyzer = AudioAnalyzer(
            sample_rate=sample_rate, buffer_size=buffer_size, smoothing=smoothing
        )

        # Color mapping
        if mode == "multi" and len(light_ips) > 1:
            self.mapper = MultiLightMapper()
        elif mode == "pulse":
            self.mapper = PulseModeMapper(
                sensitivity=sensitivity,
            )
        elif mode == "strobe":
            self.mapper = StrobeModeMapper(
                sensitivity=sensitivity,
            )
        elif mode == "spectrum_pulse":
            self.mapper = SpectrumPulseMapper(
                brightness_emphasis=brightness_boost,
                sensitivity=sensitivity,
            )
        elif mode == "spectrum_pulse_v3":
            self.mapper = SimplePulseMapper(
                min_brightness=10,
                max_brightness=100,
                peak_decay=0.985,
                gamma=0.9,
                noise_gate=0.05,
                max_step=8,
            )
        # New dual-light creative modes
        elif mode == "stereo_split":
            self.mapper = StereoSplitMapper(
                min_brightness=10,
                max_brightness=70,
                peak_decay=0.985,
                gamma=0.9,
                noise_gate=0.05,
                max_step=8,
            )
        elif mode == "complementary_pulse":
            self.mapper = ComplementaryPulseMapper(
                min_brightness=15,
                max_brightness=70,
                peak_decay=0.985,
                gamma=0.9,
                noise_gate=0.05,
                max_step=8,
            )
        elif mode == "beat_leader_follower":
            self.mapper = BeatLeaderFollowerMapper(
                min_brightness=10,
                max_brightness=70,
                peak_decay=0.985,
                gamma=0.7,
                noise_gate=0.05,
                max_step=15,
                delay_frames=4,
            )
        elif mode == "frequency_dance":
            self.mapper = FrequencyDanceMapper(
                min_brightness=15,
                max_brightness=70,
                peak_decay=0.985,
                gamma=0.9,
                noise_gate=0.05,
                max_step=8,
            )
        elif mode == "spectrum_gradient":
            self.mapper = SpectrumGradientMapper(
                min_brightness=10,
                max_brightness=70,
                peak_decay=0.985,
                gamma=0.9,
                noise_gate=0.05,
                max_step=8,
            )
        else:
            self.mapper = FrequencyToRGBMapper(
                mode=mode, brightness_boost=brightness_boost
            )

        # Threading for non-blocking light updates
        self.color_queue = queue.Queue(maxsize=1)
        self.update_thread = threading.Thread(
            target=self._light_update_worker, daemon=True
        )
        self.update_thread.start()

        # Stats for terminal display
        self.current_bass = 0
        self.current_mids = 0
        self.current_treble = 0
        self.current_color = (0, 0, 0, 0)
        self.update_count = 0
        self.last_print_time = time.time()

    def _light_update_worker(self):
        """Background thread that sends color updates to lights in parallel."""
        # Create thread pool for parallel UDP transmission
        executor = ThreadPoolExecutor(max_workers=len(self.lights))

        def safe_set_color(light, r, g, b, brightness):
            """Wrapper to safely set color with error handling."""
            try:
                light.set_color(r, g, b, brightness)
            except Exception:
                pass  # Ignore network errors

        while True:
            try:
                colors = self.color_queue.get(timeout=0.1)

                # Send to all lights IN PARALLEL
                if isinstance(colors, list):
                    # Multi-light mode: different color per light
                    futures = [
                        executor.submit(safe_set_color, light, r, g, b, brightness)
                        for light, (r, g, b, brightness) in zip(self.lights, colors)
                    ]
                    # Wait for all parallel updates to complete
                    for future in futures:
                        future.result()
                else:
                    # Single color for all lights - still parallel
                    r, g, b, brightness = colors
                    futures = [
                        executor.submit(safe_set_color, light, r, g, b, brightness)
                        for light in self.lights
                    ]
                    # Wait for all parallel updates to complete
                    for future in futures:
                        future.result()

                self.update_count += 1

            except queue.Empty:
                continue

    def _audio_callback(self, indata, frames, time_info, status):
        """Callback function for audio stream."""
        if status:
            print(f"Audio status: {status}", file=sys.stderr)

        # Get mono audio
        audio = indata[:, 0] if indata.ndim > 1 else indata

        # Analyze frequencies
        bass, mids, treble = self.analyzer.analyze(audio)
        amplitude = self.analyzer.get_amplitude(audio)

        # Store for display
        self.current_bass = bass
        self.current_mids = mids
        self.current_treble = treble

        # Map to colors
        # Dual-light modes use map_lights() for two-light effects
        dual_light_modes = [
            "multi",
            "stereo_split",
            "complementary_pulse",
            "beat_leader_follower",
            "frequency_dance",
            "spectrum_gradient",
        ]

        if self.mode in dual_light_modes and len(self.lights) > 1:
            colors = self.mapper.map_lights(bass, mids, treble, len(self.lights))
        else:
            colors = self.mapper.map(bass, mids, treble, amplitude)

        self.current_color = colors

        # Send to light update thread (non-blocking)
        try:
            self.color_queue.put_nowait(colors)
        except queue.Full:
            pass  # Skip if queue is full (previous color still being sent)

    def _print_visualization(self):
        """Print terminal visualization of current state."""
        # Clear line
        print("\r" + " " * 120 + "\r", end="")

        # Create ASCII bar graphs
        bass_bar = "█" * int(self.current_bass * 20)
        mids_bar = "█" * int(self.current_mids * 20)
        treble_bar = "█" * int(self.current_treble * 20)

        # Color codes for terminal (if supported)
        RED = "\033[91m"
        GREEN = "\033[92m"
        BLUE = "\033[94m"
        YELLOW = "\033[93m"
        RESET = "\033[0m"

        # Get brightness for display
        if isinstance(self.current_color, list):
            # Multi-light mode
            brightness = self.current_color[0][3] if self.current_color else 0
        else:
            brightness = self.current_color[3] if len(self.current_color) > 3 else 0

        brightness_bar = "█" * int(brightness / 5)  # 0-100 -> 0-20 bars

        # Print bars with brightness prominently displayed
        print(
            f"{RED}B:{bass_bar:<20}{RESET} "
            f"{GREEN}M:{mids_bar:<20}{RESET} "
            f"{BLUE}T:{treble_bar:<20}{RESET} "
            f"{YELLOW}💡:{brightness_bar:<20} {brightness:3d}%{RESET}",
            end="",
            flush=True,
        )

    def start(self):
        """Start the audio visualizer."""
        print("\n🎵 Audio Visualizer Starting...")
        print(f"Mode: {self.mode}")
        print(f"Lights: {len(self.lights)} connected")
        print(f"Sample rate: {self.analyzer.sample_rate} Hz")
        print(f"Buffer size: {self.analyzer.buffer_size} samples")

        self.running = True

        try:
            with sd.InputStream(
                callback=self._audio_callback,
                channels=1,
                samplerate=self.analyzer.sample_rate,
                blocksize=self.analyzer.buffer_size,
            ):
                while self.running:
                    # Update visualization every 50ms
                    current_time = time.time()
                    if current_time - self.last_print_time > 0.05:
                        self._print_visualization()
                        self.last_print_time = current_time

                    time.sleep(0.01)

        except KeyboardInterrupt:
            print("\n\n✨ Visualizer stopped.")
            print(f"Total updates sent: {self.update_count}")

    def stop(self):
        """Stop the visualizer."""
        self.running = False


def discover_lights():
    """Discover all Wiz lights on the network."""
    print("🔍 Discovering Wiz lights...")
    wiz = WizLight()
    lights = wiz.discover()

    if not lights:
        print("❌ No lights found on network!")
        print("Make sure:")
        print("  - You're connected to the same WiFi as your lights")
        print("  - Your lights are powered on")
        print("  - Firewall isn't blocking UDP port 38899")
        return []

    print(f"✅ Found {len(lights)} light(s):")
    for i, light in enumerate(lights, 1):
        ip = light["ip"]
        state = light["response"].get("result", {}).get("state", "unknown")
        print(f"  {i}. {ip} (state: {'on' if state else 'off'})")

    return [light["ip"] for light in lights]


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Audio-reactive Wiz light controller")
    parser.add_argument(
        "--mode",
        choices=[
            "frequency_bands",
            "energy",
            "rainbow",
            "multi",
            "pulse",
            "strobe",
            "spectrum_pulse",
            "spectrum_pulse_v3",
            "stereo_split",
            "complementary_pulse",
            "beat_leader_follower",
            "frequency_dance",
            "spectrum_gradient",
        ],
        default="frequency_bands",
        help="Color mapping mode (default: frequency_bands)",
    )
    parser.add_argument(
        "--lights",
        type=str,
        default="all",
        help='Light IPs to control, comma-separated or "all" for auto-discover (default: all)',
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=22050,
        help="Audio sample rate in Hz (default: 22050)",
    )
    parser.add_argument(
        "--buffer-size",
        type=int,
        default=2048,
        help="Audio buffer size (default: 2048)",
    )
    parser.add_argument(
        "--smoothing",
        type=float,
        default=0.3,
        help="Color smoothing factor 0-1 (default: 0.3)",
    )
    parser.add_argument(
        "--brightness-boost",
        type=float,
        default=1.5,
        help="Brightness multiplier - higher = brighter (default: 1.5, try 2.0-3.0 for max brightness)",
    )
    parser.add_argument(
        "--sensitivity",
        type=float,
        default=1.0,
        help="Brightness reaction sensitivity (default: 1.0, higher = more dramatic, try 2.0-3.0 for party mode)",
    )
    parser.add_argument(
        "--list-devices", action="store_true", help="List available audio devices"
    )

    args = parser.parse_args()

    # List audio devices and exit
    if args.list_devices:
        print("Available audio input devices:")
        print(sd.query_devices())
        return

    # Discover or parse light IPs
    if args.lights == "all":
        light_ips = discover_lights()
    else:
        light_ips = [ip.strip() for ip in args.lights.split(",")]
        print(f"Using lights: {', '.join(light_ips)}")

    if not light_ips:
        print("No lights to control. Exiting.")
        sys.exit(1)

    # Create and start visualizer
    visualizer = AudioVisualizer(
        light_ips=light_ips,
        mode=args.mode,
        sample_rate=args.sample_rate,
        buffer_size=args.buffer_size,
        smoothing=args.smoothing,
        brightness_boost=args.brightness_boost,
        sensitivity=args.sensitivity,
    )

    try:
        visualizer.start()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
