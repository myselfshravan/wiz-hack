#!/usr/bin/env python3
"""
Color mapping module for converting audio features to RGB values.
Maps frequency bands to color channels for audio-reactive lighting.
"""

import numpy as np


class FrequencyToRGBMapper:
    """Maps audio frequency bands to RGB color values."""

    def __init__(self, mode="frequency_bands", brightness_boost=1.5):
        """
        Initialize the color mapper.

        Args:
            mode: Mapping mode - 'frequency_bands', 'energy', or 'rainbow'
            brightness_boost: Multiplier for brightness (default: 1.5)
        """
        self.mode = mode
        self.brightness_boost = brightness_boost
        self.min_brightness = 10  # Minimum brightness to keep lights visible

    def map(self, bass, mids, treble, amplitude=None):
        """
        Map frequency bands to RGB color.

        Args:
            bass: Bass intensity (0.0-1.0)
            mids: Mids intensity (0.0-1.0)
            treble: Treble intensity (0.0-1.0)
            amplitude: Overall amplitude (0.0-1.0), optional

        Returns:
            tuple: (r, g, b, brightness) - RGB values 0-255, brightness 0-100
        """
        if self.mode == "frequency_bands":
            return self._frequency_bands_mapping(bass, mids, treble, amplitude)
        elif self.mode == "energy":
            return self._energy_mapping(bass, mids, treble, amplitude)
        elif self.mode == "rainbow":
            return self._rainbow_mapping(bass, mids, treble, amplitude)
        else:
            return self._frequency_bands_mapping(bass, mids, treble, amplitude)

    def _frequency_bands_mapping(self, bass, mids, treble, amplitude):
        """
        Map frequency bands directly to RGB channels.
        Bass → Red, Mids → Green, Treble → Blue
        """
        # Apply non-linear scaling for more dramatic effects
        bass_scaled = self._apply_curve(bass, power=1.5)
        mids_scaled = self._apply_curve(mids, power=1.5)
        treble_scaled = self._apply_curve(treble, power=1.5)

        # Map to RGB (0-255)
        r = int(np.clip(bass_scaled * 255, 0, 255))
        g = int(np.clip(mids_scaled * 255, 0, 255))
        b = int(np.clip(treble_scaled * 255, 0, 255))

        # Calculate brightness from overall energy
        if amplitude is not None:
            brightness = int(
                np.clip(
                    self.min_brightness + amplitude * 90 * self.brightness_boost, 0, 100
                )
            )
        else:
            # Use average of all bands
            avg_intensity = (bass + mids + treble) / 3
            brightness = int(
                np.clip(
                    self.min_brightness + avg_intensity * 90 * self.brightness_boost,
                    0,
                    100,
                )
            )

        return r, g, b, brightness

    def _energy_mapping(self, bass, mids, treble, amplitude):
        """
        Map energy to warm/cool colors.
        High energy → Warm (red/orange)
        Low energy → Cool (blue/purple)
        """
        total_energy = (bass + mids + treble) / 3

        # Warm colors for high energy
        if total_energy > 0.5:
            r = int(255 * total_energy)
            g = int(165 * total_energy)  # Orange tint
            b = int(50 * (1 - total_energy))
        else:
            # Cool colors for low energy
            r = int(128 * total_energy)
            g = int(50 * total_energy)
            b = int(255 * (1 - total_energy))

        brightness = int(
            np.clip(
                self.min_brightness + total_energy * 90 * self.brightness_boost, 0, 100
            )
        )

        return r, g, b, brightness

    def _rainbow_mapping(self, bass, mids, treble, amplitude):
        """
        Create rainbow effect based on dominant frequency.
        """
        # Find dominant frequency band
        bands = [bass, mids, treble]
        dominant_idx = np.argmax(bands)
        dominant_intensity = bands[dominant_idx]

        # Map to rainbow colors
        if dominant_idx == 0:  # Bass dominant → Red/Purple
            r = int(255 * dominant_intensity)
            g = int(50 * dominant_intensity)
            b = int(200 * dominant_intensity)
        elif dominant_idx == 1:  # Mids dominant → Green/Yellow
            r = int(200 * dominant_intensity)
            g = int(255 * dominant_intensity)
            b = int(50 * dominant_intensity)
        else:  # Treble dominant → Cyan/Blue
            r = int(50 * dominant_intensity)
            g = int(200 * dominant_intensity)
            b = int(255 * dominant_intensity)

        brightness = int(
            np.clip(
                self.min_brightness + dominant_intensity * 90 * self.brightness_boost,
                0,
                100,
            )
        )

        return r, g, b, brightness

    def _apply_curve(self, value, power=2.0):
        """
        Apply power curve for more dramatic color changes.
        Lower values get compressed, higher values get emphasized.
        """
        return np.power(value, power)


class BeatReactiveMapper:
    """Mapper that reacts to beats with flashes and pulses."""

    def __init__(self, base_mapper, flash_duration=0.1):
        """
        Initialize beat-reactive mapper.

        Args:
            base_mapper: Base FrequencyToRGBMapper instance
            flash_duration: Duration of beat flash in seconds
        """
        self.base_mapper = base_mapper
        self.flash_duration = flash_duration
        self.beat_timer = 0
        self.is_flashing = False

    def map(self, bass, mids, treble, amplitude=None, is_beat=False):
        """
        Map with beat detection.

        Args:
            bass, mids, treble: Frequency intensities
            amplitude: Overall amplitude
            is_beat: Whether a beat was detected

        Returns:
            tuple: (r, g, b, brightness)
        """
        # Get base color
        r, g, b, brightness = self.base_mapper.map(bass, mids, treble, amplitude)

        # Flash white on beat
        if is_beat:
            self.is_flashing = True
            self.beat_timer = 0
            return 255, 255, 255, 100  # Full white flash

        # Return to normal color after flash
        return r, g, b, brightness


class MultiLightMapper:
    """Mapper for controlling multiple lights with different frequency bands."""

    def __init__(self):
        """Initialize multi-light mapper."""
        pass

    def map_lights(self, bass, mids, treble, num_lights=3):
        """
        Create color mapping for multiple lights.

        Args:
            bass, mids, treble: Frequency intensities
            num_lights: Number of lights to control

        Returns:
            list: List of (r, g, b, brightness) tuples for each light
        """
        colors = []

        if num_lights >= 1:
            # Light 1: Bass-heavy (red/purple)
            r = int(bass * 255)
            g = int(bass * 50)
            b = int(bass * 200)
            brightness = int(np.clip(10 + bass * 90, 0, 100))
            colors.append((r, g, b, brightness))

        if num_lights >= 2:
            # Light 2: Mids (green/yellow)
            r = int(mids * 200)
            g = int(mids * 255)
            b = int(mids * 50)
            brightness = int(np.clip(10 + mids * 90, 0, 100))
            colors.append((r, g, b, brightness))

        if num_lights >= 3:
            # Light 3: Treble (cyan/blue)
            r = int(treble * 50)
            g = int(treble * 200)
            b = int(treble * 255)
            brightness = int(np.clip(10 + treble * 90, 0, 100))
            colors.append((r, g, b, brightness))

        # Additional lights cycle through combinations
        for i in range(3, num_lights):
            offset = i % 3
            if offset == 0:
                r, g, b = int(bass * 255), int(treble * 255), int(mids * 255)
            elif offset == 1:
                r, g, b = int(mids * 255), int(bass * 255), int(treble * 255)
            else:
                r, g, b = int(treble * 255), int(mids * 255), int(bass * 255)

            avg = (bass + mids + treble) / 3
            brightness = int(np.clip(10 + avg * 90, 0, 100))
            colors.append((r, g, b, brightness))

        return colors


class PulseModeMapper:
    """
    Brightness-focused mapper with static color.
    Brightness pulses with music energy - makes sync super obvious.
    """

    def __init__(
        self,
        base_color=(255, 200, 150),
        min_brightness=10,
        max_brightness=100,
        sensitivity=1.0,
    ):
        """
        Initialize pulse mode mapper.

        Args:
            base_color: RGB tuple for static color (default: warm white)
            min_brightness: Minimum brightness level (default: 10)
            max_brightness: Maximum brightness level (default: 100)
            sensitivity: How dramatically brightness reacts (default: 1.0, higher = more dramatic)
        """
        self.base_color = base_color
        self.min_brightness = min_brightness
        self.max_brightness = max_brightness
        self.sensitivity = sensitivity

    def map(self, bass, mids, treble, amplitude=None):
        """
        Map audio to static color with brightness pulse.

        Args:
            bass, mids, treble: Frequency intensities (not used much)
            amplitude: Overall amplitude (primary driver)

        Returns:
            tuple: (r, g, b, brightness)
        """
        r, g, b = self.base_color

        # Use overall energy to drive brightness
        if amplitude is not None:
            energy = amplitude
        else:
            # Fallback to average of frequency bands
            energy = (bass + mids + treble) / 3

        # Map energy to brightness within user-defined range
        # Sensitivity controls the power curve: higher = more dramatic swings
        power = 1.5 / self.sensitivity if self.sensitivity > 0 else 1.5
        brightness_range = self.max_brightness - self.min_brightness
        brightness = int(
            np.clip(
                self.min_brightness + (energy**power) * brightness_range,
                self.min_brightness,
                self.max_brightness,
            )
        )

        return r, g, b, brightness


class StrobeModeMapper:
    """
    Aggressive strobe effect - brightness reacts HARD to beats.
    No smoothing, dramatic swings within defined range.
    """

    def __init__(
        self,
        strobe_color=(255, 255, 255),
        threshold=1.3,
        min_brightness=5,
        max_brightness=100,
        sensitivity=1.0,
    ):
        """
        Initialize strobe mode mapper.

        Args:
            strobe_color: RGB tuple for strobe color (default: pure white)
            threshold: Beat detection sensitivity (lower = more sensitive)
            min_brightness: Minimum brightness level (default: 5)
            max_brightness: Maximum brightness level (default: 100)
            sensitivity: How dramatically brightness reacts (default: 1.0, higher = more dramatic)
        """
        self.strobe_color = strobe_color
        # Adjust threshold based on sensitivity: higher sensitivity = easier to trigger
        self.threshold = threshold / sensitivity if sensitivity > 0 else threshold
        self.min_brightness = min_brightness
        self.max_brightness = max_brightness
        self.last_energy = 0.0

    def map(self, bass, mids, treble, amplitude=None, is_beat=False):
        """
        Map audio to strobe effect.

        Args:
            bass, mids, treble: Frequency intensities
            amplitude: Overall amplitude
            is_beat: Beat detection flag (if available)

        Returns:
            tuple: (r, g, b, brightness)
        """
        r, g, b = self.strobe_color

        # Calculate current energy
        current_energy = (
            amplitude if amplitude is not None else (bass + mids + treble) / 3
        )

        # Detect sudden energy increase (beat/transient)
        energy_ratio = (
            current_energy / self.last_energy if self.last_energy > 0.01 else 1.0
        )
        self.last_energy = (
            current_energy * 0.7 + self.last_energy * 0.3
        )  # Smooth tracking

        # Strobe flash on energy spike
        if energy_ratio > self.threshold or current_energy > 0.7:
            # Flash to max!
            brightness = self.max_brightness
        else:
            # Drop to low within range
            low_brightness = int(
                np.clip(
                    current_energy * 40, self.min_brightness, self.max_brightness * 0.3
                )
            )
            brightness = int(
                np.clip(low_brightness, self.min_brightness, self.max_brightness)
            )

        return r, g, b, brightness


class SpectrumPulseMapper:
    """
    Colors based on frequency content, but brightness is the main show.
    Best of both worlds - see the frequency colors but the pulse is obvious.
    """

    def __init__(
        self,
        brightness_emphasis=2.0,
        min_brightness=5,
        max_brightness=100,
        sensitivity=1.0,
    ):
        """
        Initialize spectrum pulse mapper.

        Args:
            brightness_emphasis: How much to emphasize brightness (default: 2.0)
            min_brightness: Minimum brightness level (default: 5)
            max_brightness: Maximum brightness level (default: 100)
            sensitivity: How dramatically brightness reacts (default: 1.0, higher = more dramatic)
        """
        self.brightness_emphasis = brightness_emphasis
        self.min_brightness = min_brightness
        self.max_brightness = max_brightness
        self.sensitivity = sensitivity

    def map(self, bass, mids, treble, amplitude=None):
        """
        Map frequencies to colors, energy to brightness.

        Args:
            bass, mids, treble: Frequency intensities
            amplitude: Overall amplitude

        Returns:
            tuple: (r, g, b, brightness)
        """
        # Find dominant frequency band
        bands = [bass, mids, treble]
        max_band = max(bands)

        # Color based on frequency but SUBTLE
        # We want the color to hint at the frequency, not dominate
        if bass > mids and bass > treble:
            # Bass dominant - red/purple tones
            base_color = (200, 50, 150)
        elif treble > bass and treble > mids:
            # Treble dominant - cyan/blue tones
            base_color = (50, 150, 255)
        else:
            # Mids dominant - yellow/orange tones
            base_color = (255, 180, 50)

        # Apply color at medium intensity (not full saturation)
        r, g, b = [int(c * 0.8) for c in base_color]

        # BRIGHTNESS is the star - driven by total energy
        energy = amplitude if amplitude is not None else (bass + mids + treble) / 3

        # Aggressive brightness scaling within user-defined range
        # Sensitivity modifies the power curve for more dramatic changes
        power = (
            (1.0 / self.brightness_emphasis) / self.sensitivity
            if self.sensitivity > 0
            else (1.0 / self.brightness_emphasis)
        )
        brightness_range = self.max_brightness - self.min_brightness
        brightness = int(
            np.clip(
                self.min_brightness + (energy**power) * brightness_range,
                self.min_brightness,
                self.max_brightness,
            )
        )

        return r, g, b, brightness
