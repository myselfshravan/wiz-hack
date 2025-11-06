#!/usr/bin/env python3
"""
Video visualizer for Wiz lights.
Plays a video file while syncing lights to the visual content (and optionally audio).
Like DIY Philips Ambilight but way cooler.

Usage:
    python video_visualizer.py --file video.mp4 [--mode MODE] [OPTIONS]

Modes:
    - dominant_color: Extract dominant color from entire frame (default)
    - edge_analysis: Ambilight-style - colors from frame edges
    - average: Average color of entire frame
    - hybrid: Visual colors + audio brightness (requires audio track)
"""

import cv2
import numpy as np
import sys
import argparse
import time
import threading
import queue
from wiz_control import WizLight
from video_analysis import VideoAnalyzer, SceneBrightnessAnalyzer, HybridAnalyzer

# Check if audio support is available
try:
    import sounddevice as sd
    import soundfile as sf
    from audio_analysis import AudioAnalyzer
    AUDIO_SUPPORT = True
except ImportError:
    AUDIO_SUPPORT = False


class VideoVisualizer:
    """Video visualizer with light synchronization."""

    def __init__(
        self,
        video_file,
        light_ips,
        mode="dominant_color",
        edge_thickness=0.15,
        color_smoothing=0.5,
        min_brightness=10,
        max_brightness=100,
        brightness_from_audio=False,
        display_video=True,
    ):
        """
        Initialize the video visualizer.

        Args:
            video_file: Path to video file (MP4, AVI, etc.)
            light_ips: List of light IP addresses
            mode: Analysis mode
            edge_thickness: Edge thickness for edge_analysis mode
            color_smoothing: Color transition smoothing (0.0-1.0)
            min_brightness: Minimum brightness level
            max_brightness: Maximum brightness level
            brightness_from_audio: Use audio for brightness control
            display_video: Whether to display the video window
        """
        self.video_file = video_file
        self.light_ips = light_ips
        self.lights = [WizLight(ip) for ip in light_ips]
        self.mode = mode
        self.display_video = display_video
        self.running = False
        self.paused = False

        # Open video file
        self.cap = cv2.VideoCapture(video_file)
        if not self.cap.isOpened():
            raise ValueError(f"Could not open video file: {video_file}")

        # Video properties
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.duration = self.total_frames / self.fps if self.fps > 0 else 0
        self.frame_time = 1.0 / self.fps if self.fps > 0 else 0.033

        print(f"✅ Video loaded: {self.width}x{self.height} @ {self.fps:.1f} FPS")
        print(f"Duration: {self.duration:.1f} seconds ({self.total_frames} frames)")

        # Video analyzer
        self.video_analyzer = VideoAnalyzer(
            mode=mode,
            edge_thickness=edge_thickness,
            smoothing=color_smoothing,
        )

        # Brightness analyzer
        self.brightness_analyzer = SceneBrightnessAnalyzer(
            min_brightness=min_brightness,
            max_brightness=max_brightness,
            smoothing=color_smoothing,
        )

        # Audio support - always try to load audio for playback
        self.audio_analyzer = None
        self.audio_data = None
        self.audio_sample_rate = None
        self.audio_position = 0
        self.brightness_from_audio = brightness_from_audio

        if AUDIO_SUPPORT:
            # Always try to load audio for playback
            self._load_audio()

            if self.audio_data is not None:
                print(f"✅ Audio loaded: {self.audio_sample_rate} Hz, {len(self.audio_data)/self.audio_sample_rate:.1f}s")

                # If using audio for brightness control, create analyzer
                if brightness_from_audio:
                    self.audio_analyzer = AudioAnalyzer(
                        sample_rate=self.audio_sample_rate,
                        buffer_size=2048,
                        smoothing=color_smoothing,
                    )
                    print("✅ Audio brightness control enabled")
            else:
                print("⚠️  No audio track found in video or extraction failed")
        else:
            print("⚠️  Audio support not available. Install: pip install sounddevice soundfile")
            if brightness_from_audio:
                print("    Falling back to scene brightness analysis.")

        # Threading for non-blocking light updates
        self.color_queue = queue.Queue(maxsize=1)
        self.update_thread = threading.Thread(
            target=self._light_update_worker, daemon=True
        )
        self.update_thread.start()

        # Stats
        self.current_frame = 0
        self.current_color = (0, 0, 0, 0)
        self.frame_count = 0
        self.dropped_frames = 0

        # Audio playback stream
        self.audio_stream = None
        if self.audio_data is not None and AUDIO_SUPPORT:
            self.audio_stream = sd.OutputStream(
                samplerate=self.audio_sample_rate,
                channels=1,
                dtype='float32',
            )

    def _load_audio(self):
        """Load audio track from video file."""
        try:
            import subprocess
            import tempfile
            import os

            # Check if ffmpeg is available
            try:
                subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("⚠️  ffmpeg not found. Install it to enable audio playback:")
                print("    macOS: brew install ffmpeg")
                print("    Ubuntu: sudo apt install ffmpeg")
                print("    Windows: download from ffmpeg.org")
                self.audio_data = None
                return

            # Create temp audio file
            temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            temp_audio.close()

            print("🔊 Extracting audio from video...")

            # Extract audio with ffmpeg (suppress output)
            cmd = [
                'ffmpeg', '-i', self.video_file,
                '-vn',  # No video
                '-acodec', 'pcm_s16le',  # PCM audio
                '-ar', '22050',  # 22050 Hz sample rate
                '-ac', '1',  # Mono
                '-y',  # Overwrite
                '-loglevel', 'error',  # Only show errors
                temp_audio.name
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                # Load extracted audio
                self.audio_data, self.audio_sample_rate = sf.read(temp_audio.name)
                os.unlink(temp_audio.name)
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                if "does not contain any stream" in error_msg or "Stream" in error_msg:
                    print("⚠️  Video file has no audio track")
                else:
                    print(f"⚠️  Audio extraction failed: {error_msg}")
                self.audio_data = None

        except Exception as e:
            print(f"⚠️  Audio extraction error: {e}")
            import traceback
            traceback.print_exc()
            self.audio_data = None

    def _light_update_worker(self):
        """Background thread that sends color updates to lights."""
        while True:
            try:
                r, g, b, brightness = self.color_queue.get(timeout=0.1)

                # Send to all lights
                for light in self.lights:
                    try:
                        light.set_color(r, g, b, brightness)
                    except Exception:
                        pass  # Ignore network errors

            except queue.Empty:
                continue

    def _process_frame(self, frame):
        """Process a video frame and send colors to lights."""
        # Get audio chunk if available
        audio_chunk = None
        if self.audio_analyzer and self.audio_data is not None:
            # Calculate corresponding audio position
            samples_per_frame = int(self.audio_sample_rate / self.fps)
            start = self.audio_position
            end = min(start + samples_per_frame, len(self.audio_data))

            if start < len(self.audio_data):
                audio_chunk = self.audio_data[start:end]
                self.audio_position = end

                # Play audio chunk through speakers
                if self.audio_stream is not None and len(audio_chunk) > 0:
                    self.audio_stream.write(audio_chunk.astype('float32'))

        # Analyze frame
        r, g, b = self.video_analyzer.analyze_frame(frame)

        # Get brightness
        if self.audio_analyzer and audio_chunk is not None and len(audio_chunk) > 0:
            # Use audio for brightness
            _, _, _ = self.audio_analyzer.analyze(audio_chunk)
            amplitude = self.audio_analyzer.get_amplitude(audio_chunk)
            brightness = int(np.clip(10 + amplitude * 90, 0, 100))
        else:
            # Use scene brightness
            brightness = self.brightness_analyzer.analyze_brightness(frame)

        self.current_color = (r, g, b, brightness)

        # Send to light update thread (non-blocking)
        try:
            self.color_queue.put_nowait((r, g, b, brightness))
        except queue.Full:
            pass  # Skip if queue is full

    def _display_frame(self, frame):
        """Display frame with overlay information."""
        # Create overlay
        overlay = frame.copy()
        h, w = frame.shape[:2]

        # Add color bar at bottom
        r, g, b, brightness = self.current_color
        color_bar_height = 40
        cv2.rectangle(
            overlay,
            (0, h - color_bar_height),
            (w, h),
            (b, g, r),  # BGR format
            -1,
        )

        # Add text info
        progress = (self.current_frame / self.total_frames) * 100 if self.total_frames > 0 else 0
        elapsed = self.current_frame / self.fps if self.fps > 0 else 0
        info_text = f"Frame: {self.current_frame}/{self.total_frames} ({progress:.1f}%) | Time: {elapsed:.1f}s | Brightness: {brightness}%"

        cv2.putText(
            overlay,
            info_text,
            (10, h - color_bar_height + 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

        cv2.putText(
            overlay,
            f"RGB: ({r}, {g}, {b})",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

        cv2.imshow("Video Visualizer", overlay)

    def start(self):
        """Start playing the video with light visualization."""
        self.running = True
        self.current_frame = 0
        self.audio_position = 0

        print("\n🎬 Starting playback...")
        print(f"Mode: {self.mode}")
        print(f"Lights: {len(self.lights)} connected")
        if self.audio_stream:
            print("Audio: Enabled")
        print("\nControls: [Space] Pause | [Q] Quit | [R] Restart")

        if self.display_video:
            cv2.namedWindow("Video Visualizer", cv2.WINDOW_NORMAL)

        # Start audio stream
        if self.audio_stream:
            self.audio_stream.start()

        frame_start_time = time.time()

        try:
            while self.running:
                if not self.paused:
                    # Read frame
                    ret, frame = self.cap.read()

                    if not ret:
                        # End of video
                        print("\n✨ Video finished!")
                        break

                    self.current_frame += 1
                    self.frame_count += 1

                    # Process frame for lights
                    self._process_frame(frame)

                    # Display frame
                    if self.display_video:
                        self._display_frame(frame)

                    # Frame timing
                    current_time = time.time()
                    elapsed = current_time - frame_start_time
                    sleep_time = self.frame_time - elapsed

                    if sleep_time > 0:
                        time.sleep(sleep_time)
                    else:
                        self.dropped_frames += 1

                    frame_start_time = time.time()

                # Handle keyboard input
                if self.display_video:
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q') or key == 27:  # Q or ESC
                        break
                    elif key == ord(' '):  # Space
                        self.paused = not self.paused
                        print("\n⏸️  Paused" if self.paused else "\n▶️  Resumed")
                    elif key == ord('r'):  # R
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        self.current_frame = 0
                        self.audio_position = 0
                        frame_start_time = time.time()
                        print("\n🔄 Restarted")
                else:
                    time.sleep(0.001)

        except KeyboardInterrupt:
            pass
        finally:
            # Stop audio stream
            if self.audio_stream:
                self.audio_stream.stop()
                self.audio_stream.close()

            self.cap.release()
            if self.display_video:
                cv2.destroyAllWindows()
            self.running = False

            # Print stats
            print("\n📊 Stats:")
            print(f"Frames processed: {self.frame_count}")
            print(f"Dropped frames: {self.dropped_frames}")
            if self.frame_count > 0:
                drop_rate = (self.dropped_frames / self.frame_count) * 100
                print(f"Drop rate: {drop_rate:.1f}%")

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
    parser = argparse.ArgumentParser(
        description="Video visualizer for Wiz lights - DIY Ambilight!"
    )
    parser.add_argument(
        "--file",
        type=str,
        required=True,
        help="Path to video file (MP4, AVI, etc.)",
    )
    parser.add_argument(
        "--mode",
        choices=["dominant_color", "edge_analysis", "average", "hybrid"],
        default="dominant_color",
        help="Analysis mode (default: dominant_color)",
    )
    parser.add_argument(
        "--lights",
        type=str,
        default="all",
        help='Light IPs to control, comma-separated or "all" (default: all)',
    )
    parser.add_argument(
        "--edge-thickness",
        type=float,
        default=0.15,
        help="Edge thickness for edge_analysis mode 0.0-0.5 (default: 0.15)",
    )
    parser.add_argument(
        "--color-smoothing",
        type=float,
        default=0.5,
        help="Color transition smoothing 0-1 (default: 0.5)",
    )
    parser.add_argument(
        "--min-brightness",
        type=int,
        default=10,
        help="Minimum brightness 0-100 (default: 10)",
    )
    parser.add_argument(
        "--max-brightness",
        type=int,
        default=100,
        help="Maximum brightness 0-100 (default: 100)",
    )
    parser.add_argument(
        "--audio-brightness",
        action="store_true",
        help="Use audio track for brightness control (hybrid mode)",
    )
    parser.add_argument(
        "--no-display",
        action="store_true",
        help="Don't display video window (lights only)",
    )

    args = parser.parse_args()

    # Check if file exists
    import os
    if not os.path.exists(args.file):
        print(f"❌ Error: File not found: {args.file}")
        sys.exit(1)

    # Check audio support if needed
    if args.audio_brightness and not AUDIO_SUPPORT:
        print("❌ Audio support not available!")
        print("Install dependencies: pip install sounddevice soundfile")
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
    visualizer = VideoVisualizer(
        video_file=args.file,
        light_ips=light_ips,
        mode=args.mode,
        edge_thickness=args.edge_thickness,
        color_smoothing=args.color_smoothing,
        min_brightness=args.min_brightness,
        max_brightness=args.max_brightness,
        brightness_from_audio=args.audio_brightness,
        display_video=not args.no_display,
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
