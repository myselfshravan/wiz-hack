#!/usr/bin/env python3
"""
Music file visualizer for Wiz lights.
Plays an audio file (MP3/WAV/FLAC) while syncing lights to the music.
Perfect sync since we're analyzing the actual audio file, not mic input!

Usage:
    python music_visualizer.py --file song.mp3 [--mode MODE] [OPTIONS]
"""

import sounddevice as sd
import soundfile as sf
import numpy as np
import sys
import argparse
import time
import threading
import queue
from wiz_control import WizLight
from audio_analysis import AudioAnalyzer
from color_mapping import (
    FrequencyToRGBMapper,
    MultiLightMapper,
    PulseModeMapper,
    StrobeModeMapper,
    SpectrumPulseMapper,
    SimplePulseMapper,
)


class MusicVisualizer:
    """Music file visualizer with perfect audio-light sync."""

    def __init__(
        self,
        audio_file,
        light_ips,
        mode="frequency_bands",
        smoothing=0.3,
        brightness_boost=1.5,
        sensitivity=1.0,
        loop=False,
    ):
        """
        Initialize the music visualizer.

        Args:
            audio_file: Path to audio file (MP3, WAV, FLAC, etc.)
            light_ips: List of light IP addresses
            mode: Color mapping mode
            smoothing: Smoothing factor for colors
            brightness_boost: Brightness multiplier
            sensitivity: How dramatically brightness reacts
            loop: Whether to loop the song
        """
        self.audio_file = audio_file
        self.light_ips = light_ips
        self.lights = [WizLight(ip) for ip in light_ips]
        self.mode = mode
        self.loop = loop
        self.running = False
        self.paused = False

        # Load audio file
        print(f"Loading audio file: {audio_file}")
        self.audio_data, self.sample_rate = sf.read(audio_file, always_2d=True)

        # Convert to mono if stereo
        if self.audio_data.shape[1] > 1:
            self.audio_data = np.mean(self.audio_data, axis=1)
        else:
            self.audio_data = self.audio_data[:, 0]

        self.total_samples = len(self.audio_data)
        self.duration = self.total_samples / self.sample_rate

        print(f"✅ Loaded: {self.duration:.1f} seconds, {self.sample_rate} Hz")

        # Audio analysis
        self.analyzer = AudioAnalyzer(
            sample_rate=self.sample_rate,
            buffer_size=2048,
            smoothing=smoothing,
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

        # Stats
        self.current_position = 0
        self.current_bass = 0
        self.current_mids = 0
        self.current_treble = 0
        self.current_color = (0, 0, 0, 0)

    def _light_update_worker(self):
        """Background thread that sends color updates to lights."""
        while True:
            try:
                colors = self.color_queue.get(timeout=0.1)

                # Send to all lights
                if isinstance(colors, list):
                    # Multi-light mode
                    for light, (r, g, b, brightness) in zip(self.lights, colors):
                        try:
                            light.set_color(r, g, b, brightness)
                        except Exception:
                            pass
                else:
                    # Single color for all lights
                    r, g, b, brightness = colors
                    for light in self.lights:
                        try:
                            light.set_color(r, g, b, brightness)
                        except Exception:
                            pass

            except queue.Empty:
                continue

    def _process_audio_chunk(self, chunk):
        """Process an audio chunk and send colors to lights."""
        # Analyze frequencies
        bass, mids, treble = self.analyzer.analyze(chunk)
        amplitude = self.analyzer.get_amplitude(chunk)

        # Store for display
        self.current_bass = bass
        self.current_mids = mids
        self.current_treble = treble

        # Map to colors
        if self.mode == "multi" and len(self.lights) > 1:
            colors = self.mapper.map_lights(bass, mids, treble, len(self.lights))
        else:
            colors = self.mapper.map(bass, mids, treble, amplitude)

        self.current_color = colors

        # Send to light update thread (non-blocking)
        try:
            self.color_queue.put_nowait(colors)
        except queue.Full:
            pass

    def _print_progress(self):
        """Print progress bar and visualization."""
        elapsed = self.current_position / self.sample_rate
        progress = (elapsed / self.duration) * 100

        # Progress bar
        bar_length = 40
        filled = int(bar_length * progress / 100)
        bar = "█" * filled + "░" * (bar_length - filled)

        # Time display
        elapsed_str = f"{int(elapsed // 60)}:{int(elapsed % 60):02d}"
        total_str = f"{int(self.duration // 60)}:{int(self.duration % 60):02d}"

        # Frequency bars
        bass_bar = "█" * int(self.current_bass * 10)
        mids_bar = "█" * int(self.current_mids * 10)
        treble_bar = "█" * int(self.current_treble * 10)

        # Get brightness
        if isinstance(self.current_color, list):
            brightness = self.current_color[0][3] if self.current_color else 0
        else:
            brightness = self.current_color[3] if len(self.current_color) > 3 else 0

        brightness_bar = "█" * int(brightness / 10)

        # Color codes
        RED = "\033[91m"
        GREEN = "\033[92m"
        BLUE = "\033[94m"
        YELLOW = "\033[93m"
        CYAN = "\033[96m"
        RESET = "\033[0m"

        # Clear screen
        print("\033[2J\033[H", end="")

        # Print UI
        print(f"\n🎵 {CYAN}Music Visualizer{RESET}")
        print(f"File: {self.audio_file}")
        print(f"Mode: {self.mode}")
        print(f"\n{bar} {progress:5.1f}%")
        print(f"Time: {elapsed_str} / {total_str}")
        print(f"\n{RED}Bass:   {bass_bar:<10}{RESET}")
        print(f"{GREEN}Mids:   {mids_bar:<10}{RESET}")
        print(f"{BLUE}Treble: {treble_bar:<10}{RESET}")
        print(f"{YELLOW}Bright: {brightness_bar:<10} {brightness:3d}%{RESET}")
        print("\nControls: [Space] Pause | [Q] Quit | [R] Restart")

    def start(self):
        """Start playing the music with light visualization."""
        self.running = True
        self.current_position = 0

        print("\n🎵 Starting playback...")
        print(f"Mode: {self.mode}")
        print(f"Lights: {len(self.lights)} connected")

        # Audio output stream
        stream = sd.OutputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
        )

        stream.start()

        try:
            while self.running:
                if not self.paused:
                    # Calculate how many samples to read for ~50ms chunks
                    chunk_size = int(self.sample_rate * 0.05)  # 50ms chunks

                    # Get audio chunk
                    if self.current_position + chunk_size > self.total_samples:
                        if self.loop:
                            # Loop back to start
                            remaining = chunk_size - (
                                self.total_samples - self.current_position
                            )
                            chunk = np.concatenate(
                                [
                                    self.audio_data[self.current_position :],
                                    self.audio_data[:remaining],
                                ]
                            )
                            self.current_position = remaining
                        else:
                            # End of song
                            chunk = self.audio_data[self.current_position :]
                            self.current_position = self.total_samples
                            stream.write(chunk.astype("float32"))
                            self._process_audio_chunk(chunk)
                            break
                    else:
                        chunk = self.audio_data[
                            self.current_position : self.current_position + chunk_size
                        ]
                        self.current_position += chunk_size

                    # Play audio
                    stream.write(chunk.astype("float32"))

                    # Process for lights
                    self._process_audio_chunk(chunk)

                    # Update display
                    self._print_progress()

                else:
                    time.sleep(0.1)

        except KeyboardInterrupt:
            pass
        finally:
            stream.stop()
            stream.close()
            self.running = False
            print("\n\n✨ Playback stopped.")

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
        return []

    print(f"✅ Found {len(lights)} light(s):")
    for i, light in enumerate(lights, 1):
        ip = light["ip"]
        state = light["response"].get("result", {}).get("state", "unknown")
        print(f"  {i}. {ip} (state: {'on' if state else 'off'})")

    return [light["ip"] for light in lights]


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Music file visualizer for Wiz lights")
    parser.add_argument(
        "--file",
        type=str,
        required=True,
        help="Path to audio file (MP3, WAV, FLAC, etc.)",
    )
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
        ],
        default="frequency_bands",
        help="Color mapping mode (default: frequency_bands)",
    )
    parser.add_argument(
        "--lights",
        type=str,
        default="all",
        help='Light IPs to control, comma-separated or "all" (default: all)',
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
        help="Brightness multiplier (default: 1.5)",
    )
    parser.add_argument(
        "--sensitivity",
        type=float,
        default=1.0,
        help="Brightness sensitivity (default: 1.0, higher = more dramatic)",
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Loop the song continuously",
    )

    args = parser.parse_args()

    # Check if file exists
    import os

    if not os.path.exists(args.file):
        print(f"❌ Error: File not found: {args.file}")
        sys.exit(1)

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
    visualizer = MusicVisualizer(
        audio_file=args.file,
        light_ips=light_ips,
        mode=args.mode,
        smoothing=args.smoothing,
        brightness_boost=args.brightness_boost,
        sensitivity=args.sensitivity,
        loop=args.loop,
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
