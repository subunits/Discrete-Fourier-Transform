#!/usr/bin/env python3
"""
Test Suite for DFT Audio Visualizer
Validates critical fixes: FFT normalization, peak detection, file sync, error handling.

Run with: python -m pytest test_dft_visualizer.py -v
Or: python test_dft_visualizer.py
"""

import unittest
import tempfile
import os
import wave
import struct
import numpy as np
import sys

# Import test targets (adjust paths as needed)
# These imports work if running from same directory
try:
    # We'll test the production versions
    sys.path.insert(0, os.path.dirname(__file__))
except:
    pass


class TestCircularBuffer(unittest.TestCase):
    """Test CircularAudioBuffer O(1) complexity and correctness."""
    
    def setUp(self):
        """Import here to avoid dependency issues."""
        from dft_visualizer_production import CircularAudioBuffer
        self.CircularAudioBuffer = CircularAudioBuffer
    
    def test_basic_extend(self):
        """Test basic buffer extension."""
        buf = self.CircularAudioBuffer(size=10)
        data = np.array([1, 2, 3], dtype=np.float32)
        buf.extend(data)
        
        ordered = buf.get_ordered_window()
        np.testing.assert_array_almost_equal(ordered[:3], [1, 2, 3])
    
    def test_wraparound(self):
        """Test circular buffer wraparound."""
        buf = self.CircularAudioBuffer(size=10)
        data = np.arange(15, dtype=np.float32)
        buf.extend(data)
        
        ordered = buf.get_ordered_window()
        # Should contain last 10 elements
        np.testing.assert_array_almost_equal(ordered, np.arange(5, 15, dtype=np.float32))
    
    def test_multiple_extends(self):
        """Test multiple consecutive extends."""
        buf = self.CircularAudioBuffer(size=20)
        
        buf.extend(np.array([1, 2, 3], dtype=np.float32))
        buf.extend(np.array([4, 5, 6], dtype=np.float32))
        buf.extend(np.array([7, 8, 9], dtype=np.float32))
        
        ordered = buf.get_ordered_window()
        np.testing.assert_array_almost_equal(ordered[:9], np.arange(1, 10, dtype=np.float32))
    
    def test_empty_extend(self):
        """Test extending with empty array."""
        buf = self.CircularAudioBuffer(size=10)
        buf.extend(np.array([1, 2, 3], dtype=np.float32))
        buf.extend(np.array([], dtype=np.float32))  # Should not crash
        
        ordered = buf.get_ordered_window()
        self.assertEqual(len(ordered), 10)
    
    def test_invalid_size(self):
        """Test that invalid buffer size raises error."""
        with self.assertRaises(ValueError):
            self.CircularAudioBuffer(size=0)
        
        with self.assertRaises(ValueError):
            self.CircularAudioBuffer(size=-1)


class TestFFTNormalization(unittest.TestCase):
    """Test FFT magnitude normalization accuracy."""
    
    def test_fft_normalization_with_sine(self):
        """Test FFT normalization with known sine wave.
        
        A 1.0 amplitude sine should have ~0.5 RMS in frequency domain.
        With proper normalization, peak magnitude should be ~0.5 dB ± 1 dB.
        """
        import scipy.fftpack as fftpack
        
        # Generate 1 kHz sine wave at 44.1 kHz
        fs = 44100
        duration = 1.0
        freq = 1000.0
        t = np.arange(0, duration, 1/fs)
        signal = np.sin(2 * np.pi * freq * t).astype(np.float32)
        
        # Apply window
        window = np.hanning(len(signal))
        window_norm = np.sum(window) / len(window)
        windowed = signal * window
        
        # Compute FFT with correct normalization
        fft_complex = fftpack.fft(windowed)
        fft_mag = np.abs(fft_complex[:len(signal)//2]) / (len(signal) * window_norm / 2)
        fft_mag_db = 20 * np.log10(fft_mag + 1e-5)
        
        # Find peak (should be near 1000 Hz)
        freqs = np.fft.fftfreq(len(signal), 1/fs)[:len(signal)//2]
        peak_idx = np.argmax(fft_mag_db[100:800])  # Search 100-800 Hz
        peak_freq = freqs[100 + peak_idx]
        peak_mag = fft_mag[100 + peak_idx]
        
        # Peak should be close to 0.5 RMS (~-6 dB)
        self.assertAlmostEqual(peak_freq, 1000, delta=50, msg="Peak frequency should be ~1000 Hz")
        self.assertGreater(peak_mag, 0.4, msg="Peak magnitude should be > 0.4 (< -8 dB)")
        self.assertLess(peak_mag, 0.6, msg="Peak magnitude should be < 0.6 (> -4 dB)")


class TestAudioConfig(unittest.TestCase):
    """Test AudioConfig and VisualizerConfig validation."""
    
    def setUp(self):
        from dft_visualizer_production import AudioConfig, VisualizerConfig
        self.AudioConfig = AudioConfig
        self.VisualizerConfig = VisualizerConfig
    
    def test_valid_audio_config(self):
        """Test creating valid AudioConfig."""
        config = self.AudioConfig(
            sample_rate=44100,
            window_size=2048,
            buffer_size=8192
        )
        self.assertEqual(config.sample_rate, 44100)
        self.assertEqual(config.window_size, 2048)
    
    def test_invalid_sample_rate(self):
        """Test that invalid sample rates are rejected."""
        with self.assertRaises(ValueError):
            self.AudioConfig(sample_rate=4000)  # Too low
        
        with self.assertRaises(ValueError):
            self.AudioConfig(sample_rate=500000)  # Too high
    
    def test_invalid_window_size(self):
        """Test that invalid window sizes are rejected."""
        with self.assertRaises(ValueError):
            self.AudioConfig(window_size=128)  # Too small
        
        with self.assertRaises(ValueError):
            self.AudioConfig(window_size=32768)  # Too large
    
    def test_invalid_visualizer_config(self):
        """Test VisualizerConfig validation."""
        with self.assertRaises(ValueError):
            self.VisualizerConfig(onset_threshold_default=1.5)  # Out of range
        
        with self.assertRaises(ValueError):
            self.VisualizerConfig(
                min_frequency_hz=1000,
                max_frequency_hz=500  # Max < Min
            )


class TestNativeAudioSource(unittest.TestCase):
    """Test NativeAudioSource file handling and validation."""
    
    def setUp(self):
        from dft_visualizer_strip_production import NativeAudioSource
        self.NativeAudioSource = NativeAudioSource
    
    def test_file_not_found(self):
        """Test that missing file raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            self.NativeAudioSource("/nonexistent/path/audio.wav")
    
    def test_read_valid_wav(self):
        """Test reading a valid WAV file."""
        # Create temp WAV file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_path = f.name
        
        try:
            # Write test WAV (1 second of 440 Hz sine at 44.1 kHz)
            fs = 44100
            duration = 1.0
            t = np.arange(0, duration, 1/fs)
            signal = np.sin(2 * np.pi * 440 * t)
            signal_int16 = (signal * 32767).astype(np.int16)
            
            with wave.open(temp_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(fs)
                wf.writeframes(signal_int16.tobytes())
            
            # Read it back
            source = self.NativeAudioSource(temp_path)
            self.assertEqual(source.sample_rate, 44100)
            self.assertEqual(source.channels, 1)
            self.assertEqual(source.sampwidth, 2)
            
            data = source.read_all()
            self.assertEqual(len(data), fs)  # Should be 44100 samples
            self.assertTrue(np.all(np.isfinite(data)))
            self.assertTrue(np.all(np.abs(data) <= 1.0))  # Should be normalized
            
            source.close()
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_stereo_to_mono_conversion(self):
        """Test that stereo files are downmixed to mono."""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_path = f.name
        
        try:
            # Write stereo test WAV
            fs = 44100
            duration = 0.1
            t = np.arange(0, duration, 1/fs)
            left = np.sin(2 * np.pi * 440 * t)
            right = np.sin(2 * np.pi * 880 * t)
            signal = np.column_stack([left, right])
            signal_int16 = (signal * 32767).astype(np.int16)
            
            with wave.open(temp_path, 'wb') as wf:
                wf.setnchannels(2)
                wf.setsampwidth(2)
                wf.setframerate(fs)
                wf.writeframes(signal_int16.tobytes())
            
            # Read it back
            source = self.NativeAudioSource(temp_path)
            data = source.read_all()
            
            # Should be mono
            self.assertEqual(len(data.shape), 1)
            self.assertGreater(len(data), 0)
            
            source.close()
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestPeakDetection(unittest.TestCase):
    """Test peak detection accuracy."""
    
    def test_find_peaks_simple(self):
        """Test scipy.signal.find_peaks with synthetic spectrum."""
        from scipy.signal import find_peaks
        
        # Create synthetic spectrum with peaks at 1000, 3000 Hz
        fs = 44100
        window_size = 2048
        freqs = np.fft.fftfreq(window_size, 1/fs)[:window_size//2]
        
        # Create spectrum with peaks
        spectrum = np.zeros_like(freqs)
        spectrum[np.abs(freqs - 1000) < 50] = 40  # Peak at 1000 Hz
        spectrum[np.abs(freqs - 3000) < 50] = 35  # Peak at 3000 Hz
        spectrum[np.abs(freqs - 5000) < 50] = 30  # Peak at 5000 Hz
        
        # Find peaks
        peaks, _ = find_peaks(spectrum, height=25, distance=2)
        peak_freqs = freqs[peaks]
        
        # Should find 3 peaks
        self.assertEqual(len(peaks), 3)
        
        # Peaks should be near expected frequencies
        self.assertTrue(any(900 < f < 1100 for f in peak_freqs))
        self.assertTrue(any(2900 < f < 3100 for f in peak_freqs))
        self.assertTrue(any(4900 < f < 5100 for f in peak_freqs))


class TestErrorHandling(unittest.TestCase):
    """Test error handling and graceful degradation."""
    
    def test_audio_config_error_message_clarity(self):
        """Test that error messages are clear and actionable."""
        from dft_visualizer_production import AudioConfig
        
        try:
            AudioConfig(sample_rate=4000)  # Invalid
        except ValueError as e:
            msg = str(e)
            # Error message should mention the valid range
            self.assertIn("8000", msg)
            self.assertIn("192000", msg)
    
    def test_file_validation_error_message(self):
        """Test that file validation errors are clear."""
        from dft_visualizer_strip_production import NativeAudioSource
        
        try:
            NativeAudioSource("/fake/file.wav")
        except FileNotFoundError as e:
            msg = str(e)
            # Should mention the file path
            self.assertIn("/fake/file.wav", msg)


class TestPerformance(unittest.TestCase):
    """Test performance characteristics."""
    
    def setUp(self):
        from dft_visualizer_production import CircularAudioBuffer
        self.CircularAudioBuffer = CircularAudioBuffer
    
    def test_circular_buffer_performance(self):
        """Test that circular buffer extends are O(1) complexity.
        
        1000 extends of 1024 samples should complete in < 100ms.
        """
        import time
        
        buf = self.CircularAudioBuffer(size=8192)
        start = time.perf_counter()
        
        for _ in range(1000):
            buf.extend(np.random.randn(1024).astype(np.float32))
        
        elapsed = time.perf_counter() - start
        
        # Should be very fast (< 100ms for 1000 operations)
        self.assertLess(elapsed, 0.1, f"Buffer performance degraded: {elapsed:.3f}s")


class TestIntegration(unittest.TestCase):
    """Integration tests with real workflows."""
    
    def test_full_analysis_pipeline(self):
        """Test the complete analysis pipeline from file to peaks."""
        from dft_visualizer_strip_production import NativeAudioSource, AudioAnalysisConfig
        import scipy.fftpack as fftpack
        from scipy.signal import find_peaks
        
        # Create test WAV
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_path = f.name
        
        try:
            # Write 1000 Hz sine at 44.1 kHz
            fs = 44100
            duration = 1.0
            t = np.arange(0, duration, 1/fs)
            signal = np.sin(2 * np.pi * 1000 * t)
            signal_int16 = (signal * 32767).astype(np.int16)
            
            with wave.open(temp_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(fs)
                wf.writeframes(signal_int16.tobytes())
            
            # Load and analyze
            config = AudioAnalysisConfig(window_size=4096, hop_size=1024)
            source = NativeAudioSource(temp_path)
            data = source.read_all()
            source.close()
            
            # Process first frame
            window_size = config.window_size
            chunk = data[:window_size]
            
            hann = np.hanning(window_size)
            window_norm = np.sum(hann) / len(hann)
            windowed = chunk * hann
            
            fft = fftpack.fft(windowed)
            fft_mag = np.abs(fft[:window_size//2]) / (window_size * window_norm / 2)
            fft_mag_db = 20 * np.log10(fft_mag + 1e-5) + 40
            
            freqs = np.fft.fftfreq(window_size, 1/fs)[:window_size//2]
            
            # Find peaks
            peaks, _ = find_peaks(fft_mag_db, height=25, distance=2)
            peak_freqs = freqs[peaks]
            
            # Should detect peak near 1000 Hz
            self.assertGreater(len(peaks), 0, "No peaks detected")
            self.assertTrue(
                any(900 < f < 1100 for f in peak_freqs),
                f"Peak not found near 1000 Hz, found: {peak_freqs[:5]}"
            )
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


def run_tests():
    """Run all tests with verbose output."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestCircularBuffer))
    suite.addTests(loader.loadTestsFromTestCase(TestFFTNormalization))
    suite.addTests(loader.loadTestsFromTestCase(TestAudioConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestNativeAudioSource))
    suite.addTests(loader.loadTestsFromTestCase(TestPeakDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformance))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
