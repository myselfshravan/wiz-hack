#!/usr/bin/env python3
"""
Video analysis module for extracting color information from video frames.
Supports multiple analysis modes: dominant color, edge analysis (Ambilight-style), etc.
"""

import cv2
import numpy as np


class VideoAnalyzer:
    """Analyzes video frames to extract color information for light control."""

    def __init__(self, mode="dominant_color", edge_thickness=0.15, smoothing=0.5):
        """
        Initialize the video analyzer.

        Args:
            mode: Analysis mode - 'dominant_color', 'edge_analysis', or 'average'
            edge_thickness: Percentage of frame to use for edge analysis (0.0-0.5)
            smoothing: Smoothing factor for color transitions (0.0-1.0)
        """
        self.mode = mode
        self.edge_thickness = edge_thickness
        self.smoothing = smoothing
        self.last_color = np.array([0, 0, 0], dtype=float)

    def analyze_frame(self, frame):
        """
        Analyze a video frame and extract RGB color.

        Args:
            frame: OpenCV frame (BGR format)

        Returns:
            tuple: (r, g, b) values 0-255
        """
        if self.mode == "dominant_color":
            return self._dominant_color(frame)
        elif self.mode == "edge_analysis":
            return self._edge_analysis(frame)
        elif self.mode == "average":
            return self._average_color(frame)
        else:
            return self._dominant_color(frame)

    def _dominant_color(self, frame):
        """
        Extract dominant color using K-means clustering.
        Fast and effective for most scenes.
        """
        # Resize for faster processing
        small_frame = cv2.resize(frame, (150, 150))

        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # Reshape to list of pixels
        pixels = rgb_frame.reshape((-1, 3)).astype(np.float32)

        # K-means clustering to find dominant colors
        k = 3  # Find top 3 colors
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, labels, centers = cv2.kmeans(
            pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS
        )

        # Find most common cluster
        unique, counts = np.unique(labels, return_counts=True)
        dominant_idx = unique[np.argmax(counts)]
        dominant_color = centers[dominant_idx]

        # Apply smoothing
        smoothed = self._smooth_color(dominant_color)

        return tuple(map(int, smoothed))

    def _edge_analysis(self, frame):
        """
        Ambilight-style edge analysis.
        Extracts colors from the edges of the frame.
        """
        h, w = frame.shape[:2]
        edge_w = int(w * self.edge_thickness)
        edge_h = int(h * self.edge_thickness)

        # Extract edge regions
        top = frame[:edge_h, :]
        bottom = frame[-edge_h:, :]
        left = frame[:, :edge_w]
        right = frame[:, -edge_w:]

        # Combine all edge pixels
        edges = np.vstack([
            top.reshape(-1, 3),
            bottom.reshape(-1, 3),
            left.reshape(-1, 3),
            right.reshape(-1, 3)
        ])

        # Calculate average edge color
        avg_color = np.mean(edges, axis=0)

        # Convert BGR to RGB
        rgb_color = avg_color[::-1]

        # Apply smoothing
        smoothed = self._smooth_color(rgb_color)

        return tuple(map(int, smoothed))

    def _average_color(self, frame):
        """
        Simple average of all pixels.
        Fast but may be washed out for complex scenes.
        """
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Calculate average
        avg_color = np.mean(rgb_frame.reshape(-1, 3), axis=0)

        # Apply smoothing
        smoothed = self._smooth_color(avg_color)

        return tuple(map(int, smoothed))

    def _smooth_color(self, color):
        """
        Apply exponential smoothing to color transitions.
        Prevents jarring color jumps between frames.
        """
        # Exponential moving average
        self.last_color = (
            self.smoothing * self.last_color + (1 - self.smoothing) * np.array(color)
        )
        return self.last_color


class SceneBrightnessAnalyzer:
    """Analyzes scene brightness for dynamic brightness control."""

    def __init__(self, min_brightness=10, max_brightness=100, smoothing=0.5):
        """
        Initialize brightness analyzer.

        Args:
            min_brightness: Minimum brightness level
            max_brightness: Maximum brightness level
            smoothing: Smoothing factor for brightness transitions
        """
        self.min_brightness = min_brightness
        self.max_brightness = max_brightness
        self.smoothing = smoothing
        self.last_brightness = min_brightness

    def analyze_brightness(self, frame):
        """
        Analyze frame brightness and map to light brightness.

        Args:
            frame: OpenCV frame (BGR format)

        Returns:
            int: Brightness value 0-100
        """
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Calculate average brightness (0-255)
        avg_brightness = np.mean(gray)

        # Map to brightness range (0-255 -> min-max)
        brightness_range = self.max_brightness - self.min_brightness
        brightness = self.min_brightness + (avg_brightness / 255.0) * brightness_range

        # Apply smoothing
        self.last_brightness = (
            self.smoothing * self.last_brightness + (1 - self.smoothing) * brightness
        )

        return int(np.clip(self.last_brightness, self.min_brightness, self.max_brightness))


class HybridAnalyzer:
    """
    Combines video visual analysis with audio analysis.
    Colors from video, brightness from audio beats.
    """

    def __init__(self, video_analyzer, audio_analyzer=None, brightness_from_audio=True):
        """
        Initialize hybrid analyzer.

        Args:
            video_analyzer: VideoAnalyzer instance
            audio_analyzer: AudioAnalyzer instance (optional)
            brightness_from_audio: Whether to use audio for brightness control
        """
        self.video_analyzer = video_analyzer
        self.audio_analyzer = audio_analyzer
        self.brightness_from_audio = brightness_from_audio
        self.scene_brightness = SceneBrightnessAnalyzer()

    def analyze(self, frame, audio_chunk=None):
        """
        Analyze both video and audio.

        Args:
            frame: OpenCV frame
            audio_chunk: Audio data (optional)

        Returns:
            tuple: (r, g, b, brightness)
        """
        # Get color from video
        r, g, b = self.video_analyzer.analyze_frame(frame)

        # Get brightness
        if self.brightness_from_audio and audio_chunk is not None and self.audio_analyzer:
            # Use audio energy for brightness
            bass, mids, treble = self.audio_analyzer.analyze(audio_chunk)
            amplitude = self.audio_analyzer.get_amplitude(audio_chunk)
            brightness = int(np.clip(10 + amplitude * 90, 0, 100))
        else:
            # Use scene brightness
            brightness = self.scene_brightness.analyze_brightness(frame)

        return r, g, b, brightness
