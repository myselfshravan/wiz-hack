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


class SimplePulseMapper:
    """
    Minimal, punchy, safe brightness driver.
    - Auto-gain with decaying peak
    - Noise gate
    - Slew-rate limit (prevents flashblind spikes)
    """

    def __init__(
        self,
        min_brightness=10,
        max_brightness=70,
        peak_decay=0.985,  # slower decay = steadier AGC (lower = more volatile)
        gamma=0.9,  # <1 = punchier mid; >1 = calmer
        noise_gate=0.05,  # fraction of peak under which we output min brightness
        max_step=8,
    ):  # max brightness change per update (in % points)
        self.min_b = int(min_brightness)
        self.max_b = int(max_brightness)
        self.peak_decay = float(peak_decay)
        self.gamma = float(gamma)
        self.noise_gate = float(noise_gate)
        self.max_step = int(max_step)
        self._peak = 0.2  # start with a sane peak
        self._prev_b = self.min_b
        self._last_rgb = (220, 120, 60)  # warm default

    def _pick_color(self, bass, mids, treble):
        # Dominant band hint, but with stronger, more aggressive colors
        if bass >= mids and bass >= treble:  # bass -> deep red
            base = (255, 40, 40)
        elif treble >= mids:  # treble -> vivid blue
            base = (50, 100, 255)
        else:  # mids -> bright green
            base = (60, 255, 80)
        # Light smoothing of hue changes
        r = int(0.8 * base[0] + 0.2 * self._last_rgb[0])
        g = int(0.8 * base[1] + 0.2 * self._last_rgb[1])
        b = int(0.8 * base[2] + 0.2 * self._last_rgb[2])
        self._last_rgb = (r, g, b)
        return self._last_rgb

    def map(self, bass, mids, treble, amplitude):
        # 1) Auto-gain peak tracking (decays slowly)
        level = float(np.clip(amplitude, 0.0, 1.0))
        self._peak = max(level, self._peak * self.peak_decay)

        # 2) Noise gate relative to peak
        if self._peak <= 1e-6 or level < self.noise_gate * self._peak:
            target_b = self.min_b
        else:
            norm = np.clip(level / (self._peak + 1e-6), 0.0, 1.0)
            shaped = norm**self.gamma
            target_b = int(self.min_b + shaped * (self.max_b - self.min_b))

        # 3) Slew-rate limit (cap how fast brightness can move)
        delta = np.clip(target_b - self._prev_b, -self.max_step, self.max_step)
        brightness = int(np.clip(self._prev_b + delta, self.min_b, self.max_b))
        self._prev_b = brightness

        r, g, b = self._pick_color(bass, mids, treble)
        return r, g, b, brightness


# ==================== DUAL-LIGHT CREATIVE MAPPERS ====================


class StereoSplitMapper:
    """
    🎸 Stereo-like frequency separation mapper.
    Light 1: Bass + Mids (warm spectrum: red→orange→yellow)
    Light 2: Mids + Treble (cool spectrum: cyan→blue→purple)
    Creates visual stereo separation effect.
    """

    def __init__(
        self,
        min_brightness=10,
        max_brightness=70,
        peak_decay=0.985,
        gamma=0.9,
        noise_gate=0.05,
        max_step=8,
    ):
        self.min_b = int(min_brightness)
        self.max_b = int(max_brightness)
        self.peak_decay = float(peak_decay)
        self.gamma = float(gamma)
        self.noise_gate = float(noise_gate)
        self.max_step = int(max_step)
        self._peak = 0.2
        self._prev_b1 = self.min_b
        self._prev_b2 = self.min_b

    def map_lights(self, bass, mids, treble, num_lights=2):
        """Map to two lights with stereo frequency split."""
        # Light 1: Bass + Mids (warm side)
        warm_energy = bass * 0.6 + mids * 0.4

        # Pick warm color based on dominance
        if bass > mids * 1.2:
            color1 = (255, 60, 30)  # Deep red for bass
        elif bass > mids * 0.8:
            color1 = (255, 120, 40)  # Orange for bass-mid blend
        else:
            color1 = (255, 200, 80)  # Yellow for mid-heavy

        # Light 2: Mids + Treble (cool side)
        cool_energy = mids * 0.4 + treble * 0.6

        # Pick cool color based on dominance
        if treble > mids * 1.2:
            color2 = (80, 100, 255)  # Deep blue for treble
        elif treble > mids * 0.8:
            color2 = (80, 180, 255)  # Cyan-blue blend
        else:
            color2 = (100, 255, 200)  # Cyan for mid-heavy

        # Calculate brightness for each light with AGC
        level1 = float(np.clip(warm_energy, 0.0, 1.0))
        level2 = float(np.clip(cool_energy, 0.0, 1.0))

        self._peak = max(max(level1, level2), self._peak * self.peak_decay)

        # Apply noise gate and brightness calculation for Light 1
        if self._peak <= 1e-6 or level1 < self.noise_gate * self._peak:
            target_b1 = self.min_b
        else:
            norm1 = np.clip(level1 / (self._peak + 1e-6), 0.0, 1.0)
            shaped1 = norm1**self.gamma
            target_b1 = int(self.min_b + shaped1 * (self.max_b - self.min_b))

        # Apply slew-rate limiting for Light 1
        delta1 = np.clip(target_b1 - self._prev_b1, -self.max_step, self.max_step)
        brightness1 = int(np.clip(self._prev_b1 + delta1, self.min_b, self.max_b))
        self._prev_b1 = brightness1

        # Apply noise gate and brightness calculation for Light 2
        if self._peak <= 1e-6 or level2 < self.noise_gate * self._peak:
            target_b2 = self.min_b
        else:
            norm2 = np.clip(level2 / (self._peak + 1e-6), 0.0, 1.0)
            shaped2 = norm2**self.gamma
            target_b2 = int(self.min_b + shaped2 * (self.max_b - self.min_b))

        # Apply slew-rate limiting for Light 2
        delta2 = np.clip(target_b2 - self._prev_b2, -self.max_step, self.max_step)
        brightness2 = int(np.clip(self._prev_b2 + delta2, self.min_b, self.max_b))
        self._prev_b2 = brightness2

        return [
            (color1[0], color1[1], color1[2], brightness1),
            (color2[0], color2[1], color2[2], brightness2),
        ]

    def map(self, bass, mids, treble, amplitude):
        """Fallback for single-light mode."""
        colors = self.map_lights(bass, mids, treble, 1)
        return colors[0]


class ComplementaryPulseMapper:
    """
    🌈 Complementary color mapper with inverse brightness.
    Light 1: Dominant frequency color at high brightness
    Light 2: Complementary color at inverse brightness
    Creates balanced, artistic color play - never total darkness.
    """

    def __init__(
        self,
        min_brightness=15,
        max_brightness=70,
        peak_decay=0.985,
        gamma=0.9,
        noise_gate=0.05,
        max_step=8,
    ):
        self.min_b = int(min_brightness)
        self.max_b = int(max_brightness)
        self.peak_decay = float(peak_decay)
        self.gamma = float(gamma)
        self.noise_gate = float(noise_gate)
        self.max_step = int(max_step)
        self._peak = 0.2
        self._prev_b = self.min_b

    def _get_complementary_color(self, r, g, b):
        """Calculate complementary color (opposite on color wheel)."""
        # Simple complementary: invert RGB
        return (255 - r, 255 - g, 255 - b)

    def map_lights(self, bass, mids, treble, num_lights=2):
        """Map to two lights with complementary colors."""
        # Determine dominant frequency and main color
        total_energy = bass + mids + treble
        if total_energy < 1e-6:
            total_energy = 1e-6

        if bass >= mids and bass >= treble:
            # Bass dominant → Red
            main_color = (255, 50, 50)
        elif treble >= mids:
            # Treble dominant → Blue
            main_color = (50, 100, 255)
        else:
            # Mids dominant → Green
            main_color = (80, 255, 100)

        # Get complementary color
        comp_color = self._get_complementary_color(*main_color)

        # Calculate overall energy for brightness
        level = float(np.clip(total_energy / 3.0, 0.0, 1.0))
        self._peak = max(level, self._peak * self.peak_decay)

        # Calculate main brightness
        if self._peak <= 1e-6 or level < self.noise_gate * self._peak:
            target_b = self.min_b
        else:
            norm = np.clip(level / (self._peak + 1e-6), 0.0, 1.0)
            shaped = norm**self.gamma
            target_b = int(self.min_b + shaped * (self.max_b - self.min_b))

        # Apply slew-rate limiting
        delta = np.clip(target_b - self._prev_b, -self.max_step, self.max_step)
        brightness_main = int(np.clip(self._prev_b + delta, self.min_b, self.max_b))
        self._prev_b = brightness_main

        # Inverse brightness for complementary light (always sums to constant)
        brightness_comp = int(
            np.clip(self.max_b - (brightness_main - self.min_b), self.min_b, self.max_b)
        )

        return [
            (main_color[0], main_color[1], main_color[2], brightness_main),
            (comp_color[0], comp_color[1], comp_color[2], brightness_comp),
        ]

    def map(self, bass, mids, treble, amplitude):
        """Fallback for single-light mode."""
        colors = self.map_lights(bass, mids, treble, 1)
        return colors[0]


class BeatLeaderFollowerMapper:
    """
    🥁 Leader-follower beat mapper with motion effect.
    Light 1 (Leader): Fast response to beats, high sensitivity, bright whites
    Light 2 (Follower): Delayed response (~200ms lag), colored trails
    Simulates sound waves traveling through space.
    """

    def __init__(
        self,
        min_brightness=10,
        max_brightness=70,
        peak_decay=0.985,
        gamma=0.7,  # Punchier for leader
        noise_gate=0.05,
        max_step=15,  # Faster response for leader
        delay_frames=4,  # ~200ms delay at 20fps
    ):
        self.min_b = int(min_brightness)
        self.max_b = int(max_brightness)
        self.peak_decay = float(peak_decay)
        self.gamma = float(gamma)
        self.noise_gate = float(noise_gate)
        self.max_step = int(max_step)
        self.delay_frames = delay_frames

        self._peak = 0.2
        self._prev_b1 = self.min_b
        self._prev_b2 = self.min_b

        # History buffer for delay effect
        self._history = []
        self._last_color = (60, 255, 80)

    def map_lights(self, bass, mids, treble, num_lights=2):
        """Map to leader and follower lights."""
        total_energy = bass + mids + treble
        level = float(np.clip(total_energy / 3.0, 0.0, 1.0))

        # Determine color based on frequency for follower
        if bass >= mids and bass >= treble:
            follower_color = (255, 60, 60)  # Red
        elif treble >= mids:
            follower_color = (80, 120, 255)  # Blue
        else:
            follower_color = (80, 255, 120)  # Green

        # Smooth color transitions
        r = int(0.7 * follower_color[0] + 0.3 * self._last_color[0])
        g = int(0.7 * follower_color[1] + 0.3 * self._last_color[1])
        b = int(0.7 * follower_color[2] + 0.3 * self._last_color[2])
        self._last_color = (r, g, b)

        # Leader: bright white, fast response
        leader_color = (255, 240, 220)

        # Update peak
        self._peak = max(level, self._peak * self.peak_decay)

        # Calculate leader brightness (current frame)
        if self._peak <= 1e-6 or level < self.noise_gate * self._peak:
            target_b1 = self.min_b
        else:
            norm = np.clip(level / (self._peak + 1e-6), 0.0, 1.0)
            shaped = norm**self.gamma
            target_b1 = int(self.min_b + shaped * (self.max_b - self.min_b))

        # Fast slew for leader
        delta1 = np.clip(target_b1 - self._prev_b1, -self.max_step, self.max_step)
        brightness1 = int(np.clip(self._prev_b1 + delta1, self.min_b, self.max_b))
        self._prev_b1 = brightness1

        # Add current state to history
        self._history.append((level, r, g, b))
        if len(self._history) > self.delay_frames:
            self._history.pop(0)

        # Calculate follower brightness (delayed frame)
        if len(self._history) >= self.delay_frames:
            delayed_level, delayed_r, delayed_g, delayed_b = self._history[0]
        else:
            delayed_level = level
            delayed_r, delayed_g, delayed_b = r, g, b

        if self._peak <= 1e-6 or delayed_level < self.noise_gate * self._peak:
            target_b2 = self.min_b
        else:
            norm2 = np.clip(delayed_level / (self._peak + 1e-6), 0.0, 1.0)
            shaped2 = norm2**1.1  # Smoother for follower
            target_b2 = int(self.min_b + shaped2 * (self.max_b - self.min_b))

        # Slower slew for follower
        delta2 = np.clip(target_b2 - self._prev_b2, -5, 5)
        brightness2 = int(np.clip(self._prev_b2 + delta2, self.min_b, self.max_b))
        self._prev_b2 = brightness2

        return [
            (leader_color[0], leader_color[1], leader_color[2], brightness1),
            (delayed_r, delayed_g, delayed_b, brightness2),
        ]

    def map(self, bass, mids, treble, amplitude):
        """Fallback for single-light mode."""
        colors = self.map_lights(bass, mids, treble, 1)
        return colors[0]


class FrequencyDanceMapper:
    """
    💃 Frequency competition mapper - lights battle for dominance.
    Lights alternate dominance based on which frequency band is stronger.
    When Bass dominates: Light 1 bright red, Light 2 dim blue
    When Treble dominates: Light 2 bright blue, Light 1 dim red
    Smooth crossfade with color blending creates dynamic dance effect.
    """

    def __init__(
        self,
        min_brightness=15,
        max_brightness=70,
        peak_decay=0.985,
        gamma=0.9,
        noise_gate=0.05,
        max_step=8,
    ):
        self.min_b = int(min_brightness)
        self.max_b = int(max_brightness)
        self.peak_decay = float(peak_decay)
        self.gamma = float(gamma)
        self.noise_gate = float(noise_gate)
        self.max_step = int(max_step)
        self._peak = 0.2
        self._prev_b1 = self.min_b
        self._prev_b2 = self.min_b

    def map_lights(self, bass, mids, treble, num_lights=2):
        """Map to competing lights based on frequency dominance."""
        # Calculate total energy
        total_energy = bass + mids + treble
        if total_energy < 1e-6:
            total_energy = 1e-6

        # Determine dominance ratio (0 = all bass, 1 = all treble)
        bass_weight = (bass + mids * 0.3) / total_energy
        treble_weight = (treble + mids * 0.3) / total_energy

        # Normalize to 0-1 range where 0.5 is balanced
        if bass_weight + treble_weight > 0:
            dominance = treble_weight / (bass_weight + treble_weight)
        else:
            dominance = 0.5

        # Light 1: Strong when bass dominates (dominance close to 0)
        # Color transitions from deep red (bass) to purple (mid) to dim blue (treble)
        bass_influence = 1.0 - dominance
        color1_r = int(np.clip(180 + bass_influence * 75, 80, 255))
        color1_g = int(np.clip(50 + (1 - abs(dominance - 0.5) * 2) * 80, 50, 130))
        color1_b = int(np.clip(50 + (1 - bass_influence) * 100, 50, 150))

        # Light 2: Strong when treble dominates (dominance close to 1)
        # Color transitions from dim red (bass) to purple (mid) to bright blue (treble)
        treble_influence = dominance
        color2_r = int(np.clip(80 + (1 - treble_influence) * 100, 50, 180))
        color2_g = int(np.clip(80 + (1 - abs(dominance - 0.5) * 2) * 80, 80, 160))
        color2_b = int(np.clip(150 + treble_influence * 105, 150, 255))

        # Calculate overall energy level
        level = float(np.clip(total_energy / 3.0, 0.0, 1.0))
        self._peak = max(level, self._peak * self.peak_decay)

        # Base brightness from energy
        if self._peak <= 1e-6 or level < self.noise_gate * self._peak:
            base_brightness = self.min_b
        else:
            norm = np.clip(level / (self._peak + 1e-6), 0.0, 1.0)
            shaped = norm**self.gamma
            base_brightness = int(self.min_b + shaped * (self.max_b - self.min_b))

        # Distribute brightness based on dominance
        # When bass dominates (dominance=0), Light 1 gets full, Light 2 gets minimum
        # When balanced (dominance=0.5), both get medium
        # When treble dominates (dominance=1), Light 2 gets full, Light 1 gets minimum
        brightness_range = base_brightness - self.min_b

        target_b1 = int(self.min_b + brightness_range * (1.0 - dominance))
        target_b2 = int(self.min_b + brightness_range * dominance)

        # Apply slew-rate limiting
        delta1 = np.clip(target_b1 - self._prev_b1, -self.max_step, self.max_step)
        brightness1 = int(np.clip(self._prev_b1 + delta1, self.min_b, self.max_b))
        self._prev_b1 = brightness1

        delta2 = np.clip(target_b2 - self._prev_b2, -self.max_step, self.max_step)
        brightness2 = int(np.clip(self._prev_b2 + delta2, self.min_b, self.max_b))
        self._prev_b2 = brightness2

        return [
            (color1_r, color1_g, color1_b, brightness1),
            (color2_r, color2_g, color2_b, brightness2),
        ]

    def map(self, bass, mids, treble, amplitude):
        """Fallback for single-light mode."""
        colors = self.map_lights(bass, mids, treble, 1)
        return colors[0]


class SpectrumGradientMapper:
    """
    🌊 Spectrum gradient mapper - visual frequency gradient.
    Light 1: Low frequencies (Bass: 20-500Hz) → Red/Orange spectrum
    Light 2: High frequencies (Treble: 4000-20000Hz) → Blue/Purple spectrum
    Both pulse with overall energy but colored by their frequency range.
    Creates a visual frequency gradient across physical space.
    """

    def __init__(
        self,
        min_brightness=10,
        max_brightness=70,
        peak_decay=0.985,
        gamma=0.9,
        noise_gate=0.05,
        max_step=8,
    ):
        self.min_b = int(min_brightness)
        self.max_b = int(max_brightness)
        self.peak_decay = float(peak_decay)
        self.gamma = float(gamma)
        self.noise_gate = float(noise_gate)
        self.max_step = int(max_step)
        self._peak_low = 0.2
        self._peak_high = 0.2
        self._prev_b1 = self.min_b
        self._prev_b2 = self.min_b

    def map_lights(self, bass, mids, treble, num_lights=2):
        """Map to gradient lights representing spectrum ends."""
        # Light 1: Low frequency end (bass-focused)
        low_energy = bass + mids * 0.3

        # Color varies with bass intensity: dark red → bright orange
        if bass > mids:
            # More bass → deeper red
            color1 = (255, int(40 + bass * 80), 30)
        else:
            # More mids → orange
            color1 = (255, int(100 + mids * 100), 50)

        # Light 2: High frequency end (treble-focused)
        high_energy = treble + mids * 0.3

        # Color varies with treble intensity: purple → bright blue
        if treble > mids:
            # More treble → brighter blue
            color2 = (int(60 + treble * 40), int(80 + treble * 100), 255)
        else:
            # More mids → purple
            color2 = (int(120 + mids * 80), int(80 + mids * 120), 255)

        # Independent AGC for each frequency range
        level_low = float(np.clip(low_energy, 0.0, 1.0))
        level_high = float(np.clip(high_energy, 0.0, 1.0))

        self._peak_low = max(level_low, self._peak_low * self.peak_decay)
        self._peak_high = max(level_high, self._peak_high * self.peak_decay)

        # Calculate brightness for Light 1 (low freq)
        if self._peak_low <= 1e-6 or level_low < self.noise_gate * self._peak_low:
            target_b1 = self.min_b
        else:
            norm1 = np.clip(level_low / (self._peak_low + 1e-6), 0.0, 1.0)
            shaped1 = norm1**self.gamma
            target_b1 = int(self.min_b + shaped1 * (self.max_b - self.min_b))

        # Apply slew-rate limiting for Light 1
        delta1 = np.clip(target_b1 - self._prev_b1, -self.max_step, self.max_step)
        brightness1 = int(np.clip(self._prev_b1 + delta1, self.min_b, self.max_b))
        self._prev_b1 = brightness1

        # Calculate brightness for Light 2 (high freq)
        if self._peak_high <= 1e-6 or level_high < self.noise_gate * self._peak_high:
            target_b2 = self.min_b
        else:
            norm2 = np.clip(level_high / (self._peak_high + 1e-6), 0.0, 1.0)
            shaped2 = norm2**self.gamma
            target_b2 = int(self.min_b + shaped2 * (self.max_b - self.min_b))

        # Apply slew-rate limiting for Light 2
        delta2 = np.clip(target_b2 - self._prev_b2, -self.max_step, self.max_step)
        brightness2 = int(np.clip(self._prev_b2 + delta2, self.min_b, self.max_b))
        self._prev_b2 = brightness2

        return [
            (color1[0], color1[1], color1[2], brightness1),
            (color2[0], color2[1], color2[2], brightness2),
        ]

    def map(self, bass, mids, treble, amplitude):
        """Fallback for single-light mode."""
        colors = self.map_lights(bass, mids, treble, 1)
        return colors[0]
