#!/usr/bin/env python3
"""
Audio analysis module for extracting frequency bands from audio signals.
Uses FFT to split audio into bass, mids, and treble for light visualization.
"""

import numpy as np
from collections import deque


class AudioAnalyzer:
    """Analyzes audio signals and extracts frequency band information."""

    def __init__(self, sample_rate=22050, buffer_size=2048, smoothing=0.3):
        """
        Initialize the audio analyzer.

        Args:
            sample_rate: Audio sample rate in Hz (default: 22050)
            buffer_size: Number of samples per analysis (default: 2048)
            smoothing: Exponential smoothing factor (0-1, higher = smoother)
        """
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.smoothing = smoothing

        # Smoothed values for preventing jitter
        self.smoothed_bass = 0.0
        self.smoothed_mids = 0.0
        self.smoothed_treble = 0.0
        self.smoothed_amplitude = 0.0

        # Auto-gain control
        self.max_bass = 1.0
        self.max_mids = 1.0
        self.max_treble = 1.0
        self.gain_decay = 0.995  # Slowly decay max values

    def analyze(self, audio_chunk):
        """
        Analyze an audio chunk and extract frequency bands.

        Args:
            audio_chunk: numpy array of audio samples

        Returns:
            tuple: (bass, mids, treble) normalized to 0.0-1.0 range
        """
        # Compute FFT
        fft_data = np.fft.rfft(audio_chunk)
        fft_magnitude = np.abs(fft_data)

        # Get frequency bins
        frequencies = np.fft.rfftfreq(len(audio_chunk), 1 / self.sample_rate)

        # Extract frequency bands
        # Bass: 20-250 Hz (kick drums, bass guitar)
        bass_mask = (frequencies >= 20) & (frequencies < 250)
        bass = np.mean(fft_magnitude[bass_mask]) if bass_mask.any() else 0

        # Mids: 250-4000 Hz (vocals, most instruments)
        mids_mask = (frequencies >= 250) & (frequencies < 4000)
        mids = np.mean(fft_magnitude[mids_mask]) if mids_mask.any() else 0

        # Treble: 4000-20000 Hz (cymbals, hi-hats)
        treble_mask = (frequencies >= 4000) & (frequencies < 20000)
        treble = np.mean(fft_magnitude[treble_mask]) if treble_mask.any() else 0

        # Update max values for auto-gain
        self.max_bass = max(bass, self.max_bass * self.gain_decay)
        self.max_mids = max(mids, self.max_mids * self.gain_decay)
        self.max_treble = max(treble, self.max_treble * self.gain_decay)

        # Normalize to 0-1 range
        bass_norm = bass / self.max_bass if self.max_bass > 0 else 0
        mids_norm = mids / self.max_mids if self.max_mids > 0 else 0
        treble_norm = treble / self.max_treble if self.max_treble > 0 else 0

        # Apply exponential smoothing
        self.smoothed_bass = (
            self.smoothing * bass_norm + (1 - self.smoothing) * self.smoothed_bass
        )
        self.smoothed_mids = (
            self.smoothing * mids_norm + (1 - self.smoothing) * self.smoothed_mids
        )
        self.smoothed_treble = (
            self.smoothing * treble_norm + (1 - self.smoothing) * self.smoothed_treble
        )

        # Clamp to 0-1 range
        self.smoothed_bass = np.clip(self.smoothed_bass, 0.0, 1.0)
        self.smoothed_mids = np.clip(self.smoothed_mids, 0.0, 1.0)
        self.smoothed_treble = np.clip(self.smoothed_treble, 0.0, 1.0)

        return self.smoothed_bass, self.smoothed_mids, self.smoothed_treble

    def get_amplitude(self, audio_chunk):
        """
        Calculate the RMS amplitude of an audio chunk.

        Args:
            audio_chunk: numpy array of audio samples

        Returns:
            float: RMS amplitude normalized to 0.0-1.0 range
        """
        rms = np.sqrt(np.mean(audio_chunk**2))

        # Smooth the amplitude
        self.smoothed_amplitude = (
            self.smoothing * rms + (1 - self.smoothing) * self.smoothed_amplitude
        )

        # Normalize (assuming max RMS of ~0.5 for typical audio)
        return np.clip(self.smoothed_amplitude * 2, 0.0, 1.0)

    def detect_beat(self, audio_chunk, threshold=1.5):
        """
        Simple energy-based beat detection.

        Args:
            audio_chunk: numpy array of audio samples
            threshold: Energy ratio needed to trigger beat (default: 1.5)

        Returns:
            bool: True if beat detected
        """
        # Calculate instantaneous energy
        energy = np.sum(audio_chunk**2)

        # Check against recent average (simplified version)
        # In production, you'd maintain a buffer of recent energies
        is_beat = energy > threshold * np.mean(audio_chunk**2)

        return is_beat


class AudioAnalyzerV2:
    """
    Advanced audio analyzer with spectral flux detection and dual-time smoothing.
    Sharper, more volatile analysis with real-time dynamics for snappier light response.
    """

    def __init__(
        self,
        sample_rate=22050,
        buffer_size=1024,
        smoothing_attack=0.55,
        smoothing_release=0.15,
        gain_decay=0.997,
    ):
        """
        Initialize the V2 audio analyzer.

        Args:
            sample_rate: Audio sample rate in Hz (default: 22050)
            buffer_size: Number of samples per analysis - smaller = lower latency (default: 1024)
            smoothing_attack: Attack smoothing (0-1, higher = slower rise, default: 0.55)
            smoothing_release: Release smoothing (0-1, higher = slower fall, default: 0.15)
            gain_decay: How fast auto-gain adapts (default: 0.997)
        """
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.win = np.hanning(buffer_size)
        self.s_attack = float(np.clip(smoothing_attack, 0.0, 1.0))
        self.s_release = float(np.clip(smoothing_release, 0.0, 1.0))
        self.gain_decay = gain_decay

        # Band setup (log-ish split for punchier response)
        freqs = np.fft.rfftfreq(buffer_size, 1 / sample_rate)
        self._bass_mask = (freqs >= 30) & (freqs < 200)
        self._mids_mask = (freqs >= 200) & (freqs < 2500)
        self._treble_mask = (freqs >= 2500) & (freqs < 12000)

        # State
        self.prev_mag = np.zeros_like(freqs)
        self.max_bass = 1.0
        self.max_mids = 1.0
        self.max_treble = 1.0
        self.bass = 0.0
        self.mids = 0.0
        self.treble = 0.0
        self.level = 0.0

        # Rolling normals for RMS/Flux auto-gain
        self._rms_hist = deque(maxlen=50)
        self._flux_hist = deque(maxlen=50)

    def _dual_ema(self, value, prev):
        """
        Dual exponential moving average: quick rise, slower fall.
        Makes changes jump up and decay naturally.
        """
        if value >= prev:
            return self.s_attack * value + (1 - self.s_attack) * prev
        else:
            return self.s_release * value + (1 - self.s_release) * prev

    def analyze(self, audio_chunk):
        """
        Analyze audio chunk with spectral flux detection.

        Args:
            audio_chunk: numpy array of audio samples

        Returns:
            tuple: (bass, mids, treble) normalized to 0.0-1.0+ range
        """
        x = audio_chunk[: self.buffer_size]
        if len(x) < self.buffer_size:
            x = np.pad(x, (0, self.buffer_size - len(x)))

        # Windowed FFT magnitude (Hann window reduces FFT smear)
        mag = np.abs(np.fft.rfft(x * self.win))

        # Band energies (mean magnitude per band)
        bass = float(mag[self._bass_mask].mean() if self._bass_mask.any() else 0.0)
        mids = float(mag[self._mids_mask].mean() if self._mids_mask.any() else 0.0)
        treble = (
            float(mag[self._treble_mask].mean() if self._treble_mask.any() else 0.0)
        )

        # Slow gain decay so normalization adapts to the room
        self.max_bass = max(bass, self.max_bass * self.gain_decay)
        self.max_mids = max(mids, self.max_mids * self.gain_decay)
        self.max_treble = max(treble, self.max_treble * self.gain_decay)

        # Normalize 0..1
        bn = bass / (self.max_bass + 1e-12)
        mn = mids / (self.max_mids + 1e-12)
        tn = treble / (self.max_treble + 1e-12)

        # Dual-EMA smooth (attack faster than release)
        self.bass = self._dual_ema(bn, self.bass)
        self.mids = self._dual_ema(mn, self.mids)
        self.treble = self._dual_ema(tn, self.treble)

        # Spectral flux (positive deltas only) → transients
        flux = np.maximum(mag - self.prev_mag, 0.0).sum() / (mag.size + 1e-12)
        self.prev_mag = mag

        # Normalize RMS and flux by rolling medians (robust to outliers)
        rms = float(np.sqrt(np.mean(x**2)))
        self._rms_hist.append(rms)
        self._flux_hist.append(flux)

        # Use percentile instead of median for better dynamic range
        rms_norm = rms / (np.percentile(list(self._rms_hist), 75) + 1e-6) if len(self._rms_hist) > 10 else rms * 10
        flux_norm = flux / (np.percentile(list(self._flux_hist), 75) + 1e-6) if len(self._flux_hist) > 10 else flux * 10

        # Combined level: mostly loudness, with transient spice
        lvl = 0.6 * np.clip(rms_norm, 0, 1.5) + 0.4 * np.clip(flux_norm, 0, 1.5)
        self.level = self._dual_ema(lvl, self.level)

        return self.bass, self.mids, self.treble

    def get_level(self):
        """
        Get normalized level (0-1) for normal brightness driving.

        Returns:
            float: Level clamped to 0.0-1.0
        """
        return float(np.clip(self.level, 0.0, 1.0))

    def get_flux_boost(self):
        """
        Get transient/beat boost portion above 1.0 for momentary strobe/pop.

        Returns:
            float: Boost amount (0.0 if no boost)
        """
        return float(max(0.0, self.level - 1.0))
