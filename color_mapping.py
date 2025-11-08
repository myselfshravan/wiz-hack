#!/usr/bin/env python3
"""
Color mapping module for converting audio features to RGB values.
Maps frequency bands to color channels for audio-reactive lighting.
"""

import numpy as np
import time
import random


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
        sensitivity=1.0,
    ):
        """
        Initialize pulse mode mapper.

        Args:
            base_color: RGB tuple for static color (default: warm white)
            sensitivity: How dramatically brightness reacts (default: 1.0, higher = more dramatic)
        """
        self.base_color = base_color
        self.min_brightness = 10
        self.max_brightness = 100
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
        sensitivity=1.0,
    ):
        """
        Initialize strobe mode mapper.

        Args:
            strobe_color: RGB tuple for strobe color (default: pure white)
            threshold: Beat detection sensitivity (lower = more sensitive)
            sensitivity: How dramatically brightness reacts (default: 1.0, higher = more dramatic)
        """
        self.strobe_color = strobe_color
        # Adjust threshold based on sensitivity: higher sensitivity = easier to trigger
        self.threshold = threshold / sensitivity if sensitivity > 0 else threshold
        self.min_brightness = 5
        self.max_brightness = 100
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
        sensitivity=1.0,
    ):
        """
        Initialize spectrum pulse mapper.

        Args:
            brightness_emphasis: How much to emphasize brightness (default: 2.0)
            sensitivity: How dramatically brightness reacts (default: 1.0, higher = more dramatic)
        """
        self.brightness_emphasis = brightness_emphasis
        self.min_brightness = 5
        self.max_brightness = 100
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
        bands = {"bass": bass, "mids": mids, "treble": treble}
        dominant = max(bands, key=bands.get)

        # Color based on frequency but SUBTLE
        # We want the color to hint at the frequency, not dominate
        if dominant == "bass":
            # Bass dominant - red/purple tones
            base_color = (200, 50, 150)
        elif dominant == "treble":
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


class SpectrumPulseMapperV2:
    """
    Volatile, beat-reactive mapper with snappier response.
    Features:
    - Brightness: fast attack, slower release, non-linear curve
    - Beat/transient: short-lived boost with optional strobe
    - Color: band-dominant hint with saturation tied to volatility
    - Micro-jitter: bounded flicker for "alive" feel between beats
    """

    def __init__(
        self,
        min_brightness=6,
        max_brightness=100,
        attack_ms=35,
        release_ms=180,
        volatility=1.3,
        beat_boost=0.35,
        strobe_on_boost=True,
        jitter_amount=0.06,
    ):
        """
        Initialize V2 mapper.

        Args:
            min_brightness: Minimum brightness (default: 6)
            max_brightness: Maximum brightness (default: 100)
            attack_ms: Attack time in milliseconds (default: 35)
            release_ms: Release time in milliseconds (default: 180)
            volatility: Swing intensity >1 = spicier (default: 1.3)
            beat_boost: Extra brightness on transients (default: 0.35)
            strobe_on_boost: Enable strobe flash on beats (default: True)
            jitter_amount: Brightness jitter fraction (default: 0.06)
        """
        self.min_b = min_brightness
        self.max_b = max_brightness
        self.volatility = volatility
        self.beat_boost = beat_boost
        self.strobe_on_boost = strobe_on_boost
        self.jitter_amount = jitter_amount

        # Convert ms to smoothing time constants
        self.attack_tau = attack_ms / 1000.0
        self.release_tau = release_ms / 1000.0
        self._last_t = time.monotonic()
        self._b_smooth = 0.0

        # Color memory (helps avoid abrupt hue jumps)
        self._last_rgb = (160, 80, 200)

    @staticmethod
    def _ease(x):
        """More punch around mid-levels; smooth near 0/1"""
        x = np.clip(x, 0.0, 2.0)  # allow some overdrive before clipping
        return (1 - np.cos(np.pi * np.clip(x, 0, 1))) / 2  # cosine ease-in-out

    @staticmethod
    def _lerp(a, b, t):
        """Linear interpolation"""
        return a + (b - a) * t

    def _smooth_step(self, current, target, dt):
        """Exponential smoothing based on dt"""
        tau = self.attack_tau if target >= current else self.release_tau
        if tau <= 0:
            return target
        alpha = 1 - np.exp(-dt / tau)
        return current + alpha * (target - current)

    def _pick_color(self, bass, mids, treble):
        """
        Weighted color based on frequency dominance.
        Pulls saturation down slightly so brightness stands out.
        """
        bands = np.array([bass, mids, treble]) + 1e-6
        w = bands / (bands.sum())

        # Base colors for bass/mids/treble
        Cb = np.array([220, 40, 140])  # magenta/red-ish
        Cm = np.array([255, 180, 60])  # amber
        Ct = np.array([60, 180, 255])  # cyan/blue

        rgb = w[0] * Cb + w[1] * Cm + w[2] * Ct

        # Pull saturation down slightly with inertia
        rgb = 0.85 * rgb + 0.15 * np.array(self._last_rgb)
        self._last_rgb = tuple(np.clip(rgb, 0, 255).astype(int))
        return self._last_rgb

    def map(self, bass, mids, treble, level, flux_boost=0.0):
        """
        Map audio to colors with volatile brightness response.

        Args:
            bass, mids, treble: Frequency intensities (0-1)
            level: Overall level (0-1+)
            flux_boost: Transient boost amount (default: 0.0)

        Returns:
            tuple: (r, g, b, brightness)
        """
        now = time.monotonic()
        dt = max(1e-3, now - self._last_t)
        self._last_t = now

        # Nonlinear brightness drive with power curve for better dynamics
        # Higher volatility = more aggressive curve
        power = 0.5 + (self.volatility - 1.0) * 0.3
        drive = np.power(np.clip(level, 0, 1), power)

        # Add transient/beat boost (short-lived)
        if flux_boost > 0.0:
            drive = np.clip(drive + self.beat_boost * flux_boost, 0, 1.5)

        # Smooth with attack/release
        self._b_smooth = self._smooth_step(self._b_smooth, drive, dt)

        # Micro-jitter for "alive" feel (bounded, perceptible but not annoying)
        if self.jitter_amount > 0:
            jitter = (random.random() - 0.5) * 2.0 * self.jitter_amount
        else:
            jitter = 0.0

        b_norm = float(np.clip(self._b_smooth + jitter, 0.0, 1.0))
        brightness = int(
            np.clip(
                self.min_b + b_norm * (self.max_b - self.min_b), self.min_b, self.max_b
            )
        )

        # Optional strobe tick on strong boost (quick single-frame nudge)
        if self.strobe_on_boost and flux_boost > 0.5:
            extra = min(30, int(flux_boost * 40))
            brightness = min(self.max_b, brightness + extra)

        r, g, b = self._pick_color(bass, mids, treble)
        return int(r), int(g), int(b), brightness

    def map_lights(self, bass, mids, treble, num_lights, level, flux_boost=0.0):
        """
        Map audio to multiple lights (for multi-light mode).

        Args:
            bass, mids, treble: Frequency intensities
            num_lights: Number of lights to control
            level: Overall level
            flux_boost: Transient boost amount

        Returns:
            list: List of (r, g, b, brightness) tuples
        """
        # For multi-light mode, use the same color for all lights
        # (can be customized to have different colors per light if desired)
        color = self.map(bass, mids, treble, level, flux_boost)
        return [color] * num_lights
