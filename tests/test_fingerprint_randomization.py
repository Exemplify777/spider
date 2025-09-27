"""
Tests for browser fingerprint randomization system.

This module tests the fingerprint randomization functionality for anti-detection.
"""

import pytest
import hashlib
from unittest.mock import Mock, patch

from spider.infrastructure.fingerprint_randomization import (
    FingerprintRandomizer, FingerprintManager, BrowserFingerprint,
    BrowserType, OSFamily
)


class TestBrowserFingerprint:
    """Test BrowserFingerprint data structure."""
    
    def test_fingerprint_creation(self):
        """Test creating a browser fingerprint."""
        fingerprint = BrowserFingerprint(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            screen_resolution=(1920, 1080),
            timezone="America/New_York",
            language="en-US",
            platform="Win32; x64",
            hardware_concurrency=8,
            device_memory=16,
            webgl_vendor="NVIDIA Corporation",
            webgl_renderer="GeForce GTX 1060",
            canvas_fingerprint="abc123",
            audio_fingerprint="def456",
            fonts=["Arial", "Helvetica"],
            plugins=["Chrome PDF Plugin"],
            webgl_extensions=["ANGLE_instanced_arrays"],
            touch_support=False,
            do_not_track="1",
            cookie_enabled=True,
            local_storage_enabled=True,
            session_storage_enabled=True,
            indexed_db_enabled=True,
            web_sql_enabled=False,
            ad_blocker=False,
            battery_level=0.8,
            connection_type="wifi",
            effective_type="4g",
            downlink=10.0,
            rtt=100,
            save_data=False,
            color_depth=24,
            pixel_ratio=1.0,
            orientation="landscape",
            media_devices=["microphone", "camera"],
            permissions={"geolocation": "granted"},
            geolocation=(40.7128, -74.0060),
            browser_version="120.0.0.0",
            os_version="10",
            architecture="x64",
            cpu_cores=8,
            ram_gb=16,
            gpu_vendor="NVIDIA",
            gpu_model="GeForce GTX 1060"
        )
        
        assert fingerprint.user_agent == "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        assert fingerprint.screen_resolution == (1920, 1080)
        assert fingerprint.timezone == "America/New_York"
        assert fingerprint.language == "en-US"
        assert fingerprint.hardware_concurrency == 8
        assert fingerprint.device_memory == 16
        assert fingerprint.cookie_enabled is True
        assert fingerprint.touch_support is False
        assert fingerprint.battery_level == 0.8
        assert fingerprint.geolocation == (40.7128, -74.0060)


class TestFingerprintRandomizer:
    """Test fingerprint randomizer functionality."""
    
    def test_randomizer_initialization(self):
        """Test randomizer initialization."""
        randomizer = FingerprintRandomizer(BrowserType.CHROME)
        
        assert randomizer.browser_type == BrowserType.CHROME
        assert randomizer.fingerprint_history == []
        assert randomizer.current_fingerprint is None
        assert randomizer.user_agents is not None
        assert BrowserType.CHROME in randomizer.user_agents
    
    def test_generate_fingerprint(self):
        """Test fingerprint generation."""
        randomizer = FingerprintRandomizer(BrowserType.CHROME)
        
        fingerprint = randomizer.generate_fingerprint()
        
        assert isinstance(fingerprint, BrowserFingerprint)
        assert fingerprint.user_agent in randomizer.user_agents[BrowserType.CHROME]
        assert fingerprint.screen_resolution in randomizer.screen_resolutions
        assert fingerprint.timezone in randomizer.timezones
        assert fingerprint.language in randomizer.languages
        assert fingerprint.hardware_concurrency > 0
        assert fingerprint.color_depth in [24, 32]
        assert fingerprint.pixel_ratio > 0
        assert len(fingerprint.fonts) > 0
        assert len(fingerprint.plugins) > 0
        assert len(fingerprint.webgl_extensions) > 0
        
        # Check that fingerprint is stored
        assert randomizer.current_fingerprint == fingerprint
        assert fingerprint in randomizer.fingerprint_history
    
    def test_generate_multiple_fingerprints(self):
        """Test generating multiple fingerprints."""
        randomizer = FingerprintRandomizer(BrowserType.CHROME)
        
        fingerprints = []
        for _ in range(5):
            fingerprint = randomizer.generate_fingerprint()
            fingerprints.append(fingerprint)
        
        assert len(fingerprints) == 5
        assert len(randomizer.fingerprint_history) == 5
        
        # All fingerprints should be different (very high probability)
        fingerprint_hashes = [randomizer.get_fingerprint_hash(fp) for fp in fingerprints]
        assert len(set(fingerprint_hashes)) > 1  # At least some should be different
    
    def test_extract_os_info(self):
        """Test OS info extraction from user agent."""
        randomizer = FingerprintRandomizer(BrowserType.CHROME)
        
        # Test Windows user agent
        os_family, os_version = randomizer._extract_os_info(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        assert os_family == OSFamily.WINDOWS
        assert os_version == "10"
        
        # Test macOS user agent
        os_family, os_version = randomizer._extract_os_info(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        assert os_family == OSFamily.MACOS
        assert os_version == "10.15"
        
        # Test Linux user agent
        os_family, os_version = randomizer._extract_os_info(
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        )
        assert os_family == OSFamily.LINUX
    
    def test_extract_browser_version(self):
        """Test browser version extraction."""
        randomizer = FingerprintRandomizer(BrowserType.CHROME)
        
        # Test Chrome version
        version = randomizer._extract_browser_version(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        assert version == "120.0.0.0"
        
        # Test Firefox version
        version = randomizer._extract_browser_version(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
        )
        assert version == "120.0.0.0"  # Default fallback
    
    def test_generate_platform_string(self):
        """Test platform string generation."""
        randomizer = FingerprintRandomizer(BrowserType.CHROME)
        
        platform = randomizer._generate_platform_string(OSFamily.WINDOWS, "10")
        assert "Win32" in platform
        
        platform = randomizer._generate_platform_string(OSFamily.MACOS, "10.15")
        assert "MacIntel" in platform
        
        platform = randomizer._generate_platform_string(OSFamily.LINUX, "Ubuntu")
        assert "Linux" in platform
    
    def test_generate_canvas_fingerprint(self):
        """Test canvas fingerprint generation."""
        randomizer = FingerprintRandomizer(BrowserType.CHROME)
        
        fingerprint1 = randomizer._generate_canvas_fingerprint()
        fingerprint2 = randomizer._generate_canvas_fingerprint()
        
        assert isinstance(fingerprint1, str)
        assert len(fingerprint1) == 32  # MD5 hash length
        assert fingerprint1 != fingerprint2  # Should be different
    
    def test_generate_audio_fingerprint(self):
        """Test audio fingerprint generation."""
        randomizer = FingerprintRandomizer(BrowserType.CHROME)
        
        fingerprint1 = randomizer._generate_audio_fingerprint()
        fingerprint2 = randomizer._generate_audio_fingerprint()
        
        assert isinstance(fingerprint1, str)
        assert len(fingerprint1) == 32  # MD5 hash length
        assert fingerprint1 != fingerprint2  # Should be different
    
    def test_generate_gpu_model(self):
        """Test GPU model generation."""
        randomizer = FingerprintRandomizer(BrowserType.CHROME)
        
        nvidia_model = randomizer._generate_gpu_model("NVIDIA")
        assert "GeForce" in nvidia_model or "RTX" in nvidia_model
        
        amd_model = randomizer._generate_gpu_model("AMD")
        assert "Radeon" in amd_model
        
        intel_model = randomizer._generate_gpu_model("Intel")
        assert "Graphics" in intel_model or "Arc" in intel_model
    
    def test_get_headers(self):
        """Test HTTP headers generation."""
        randomizer = FingerprintRandomizer(BrowserType.CHROME)
        fingerprint = randomizer.generate_fingerprint()
        
        headers = randomizer.get_headers(fingerprint)
        
        assert "User-Agent" in headers
        assert "Accept" in headers
        assert "Accept-Language" in headers
        assert "Accept-Encoding" in headers
        assert "DNT" in headers
        assert "Connection" in headers
        
        assert headers["User-Agent"] == fingerprint.user_agent
        assert fingerprint.language in headers["Accept-Language"]
        assert headers["DNT"] == fingerprint.do_not_track
    
    def test_get_headers_chrome_specific(self):
        """Test Chrome-specific headers."""
        randomizer = FingerprintRandomizer(BrowserType.CHROME)
        fingerprint = randomizer.generate_fingerprint()
        
        headers = randomizer.get_headers(fingerprint)
        
        assert "Sec-Ch-Ua" in headers
        assert "Sec-Ch-Ua-Mobile" in headers
        assert "Sec-Ch-Ua-Platform" in headers
        assert "Chrome" in headers["Sec-Ch-Ua"]
    
    def test_get_headers_firefox_specific(self):
        """Test Firefox-specific headers."""
        randomizer = FingerprintRandomizer(BrowserType.FIREFOX)
        fingerprint = randomizer.generate_fingerprint()
        
        headers = randomizer.get_headers(fingerprint)
        
        # Firefox doesn't have Sec-Ch-Ua headers
        assert "Sec-Ch-Ua" not in headers
        assert "Sec-Fetch-Dest" in headers
        assert "Sec-Fetch-Mode" in headers
    
    def test_get_javascript_fingerprint(self):
        """Test JavaScript fingerprint code generation."""
        randomizer = FingerprintRandomizer(BrowserType.CHROME)
        fingerprint = randomizer.generate_fingerprint()
        
        js_code = randomizer.get_javascript_fingerprint(fingerprint)
        
        assert isinstance(js_code, str)
        assert "navigator" in js_code
        assert "userAgent" in js_code
        assert "screen" in js_code
        assert "WebGL" in js_code
        assert fingerprint.user_agent in js_code
        assert str(fingerprint.screen_resolution[0]) in js_code
        assert str(fingerprint.screen_resolution[1]) in js_code
    
    def test_get_fingerprint_hash(self):
        """Test fingerprint hash generation."""
        randomizer = FingerprintRandomizer(BrowserType.CHROME)
        fingerprint = randomizer.generate_fingerprint()
        
        hash1 = randomizer.get_fingerprint_hash(fingerprint)
        hash2 = randomizer.get_fingerprint_hash(fingerprint)
        
        assert isinstance(hash1, str)
        assert len(hash1) == 32  # MD5 hash length
        assert hash1 == hash2  # Same fingerprint should produce same hash
    
    def test_is_fingerprint_unique(self):
        """Test fingerprint uniqueness checking."""
        randomizer = FingerprintRandomizer(BrowserType.CHROME)
        
        # First fingerprint should be unique
        fingerprint1 = randomizer.generate_fingerprint()
        assert randomizer.is_fingerprint_unique(fingerprint1)
        
        # Generate another fingerprint
        fingerprint2 = randomizer.generate_fingerprint()
        assert randomizer.is_fingerprint_unique(fingerprint2)
        
        # Check that fingerprints are different
        hash1 = randomizer.get_fingerprint_hash(fingerprint1)
        hash2 = randomizer.get_fingerprint_hash(fingerprint2)
        assert hash1 != hash2
    
    def test_get_fingerprint_statistics(self):
        """Test fingerprint statistics generation."""
        randomizer = FingerprintRandomizer(BrowserType.CHROME)
        
        # Test with no fingerprints
        stats = randomizer.get_fingerprint_statistics()
        assert stats["total_fingerprints"] == 0
        assert stats["unique_fingerprints"] == 0
        
        # Generate some fingerprints
        for _ in range(5):
            randomizer.generate_fingerprint()
        
        stats = randomizer.get_fingerprint_statistics()
        assert stats["total_fingerprints"] == 5
        assert stats["unique_fingerprints"] > 0
        assert "browser_types" in stats
        assert "os_families" in stats
        assert "screen_resolutions" in stats
        assert "timezones" in stats
        assert "languages" in stats
    
    def test_fingerprint_history_limit(self):
        """Test that fingerprint history is limited."""
        randomizer = FingerprintRandomizer(BrowserType.CHROME)
        
        # Generate more than 100 fingerprints
        for _ in range(105):
            randomizer.generate_fingerprint()
        
        # Should only keep last 100
        assert len(randomizer.fingerprint_history) == 100
    
    def test_different_browser_types(self):
        """Test different browser types."""
        for browser_type in BrowserType:
            randomizer = FingerprintRandomizer(browser_type)
            fingerprint = randomizer.generate_fingerprint()
            
            assert fingerprint.user_agent in randomizer.user_agents[browser_type]
            # Check for browser-specific identifiers
            if browser_type == BrowserType.EDGE:
                assert "edg/" in fingerprint.user_agent.lower()
            elif browser_type == BrowserType.OPERA:
                assert "opr/" in fingerprint.user_agent.lower()
            else:
                assert browser_type.value in fingerprint.user_agent.lower()


class TestFingerprintManager:
    """Test fingerprint manager functionality."""
    
    def test_manager_initialization(self):
        """Test manager initialization."""
        manager = FingerprintManager()
        
        assert manager.randomizers == {}
        assert manager.session_fingerprints == {}
    
    def test_create_randomizer(self):
        """Test creating a randomizer."""
        manager = FingerprintManager()
        
        randomizer = manager.create_randomizer("session1", BrowserType.CHROME)
        
        assert isinstance(randomizer, FingerprintRandomizer)
        assert randomizer.browser_type == BrowserType.CHROME
        assert manager.get_randomizer("session1") == randomizer
    
    def test_get_randomizer_nonexistent(self):
        """Test getting a non-existent randomizer."""
        manager = FingerprintManager()
        
        randomizer = manager.get_randomizer("nonexistent")
        assert randomizer is None
    
    def test_generate_session_fingerprint(self):
        """Test generating session fingerprint."""
        manager = FingerprintManager()
        
        fingerprint = manager.generate_session_fingerprint("session1", BrowserType.CHROME)
        
        assert isinstance(fingerprint, BrowserFingerprint)
        assert "session1" in manager.session_fingerprints
        assert manager.session_fingerprints["session1"] == fingerprint
        assert "session1" in manager.randomizers
    
    def test_get_session_headers(self):
        """Test getting session headers."""
        manager = FingerprintManager()
        
        headers = manager.get_session_headers("session1")
        
        assert isinstance(headers, dict)
        assert "User-Agent" in headers
        assert "Accept" in headers
        assert "session1" in manager.session_fingerprints
    
    def test_get_session_javascript(self):
        """Test getting session JavaScript."""
        manager = FingerprintManager()
        
        js_code = manager.get_session_javascript("session1")
        
        assert isinstance(js_code, str)
        assert "navigator" in js_code
        assert "session1" in manager.session_fingerprints
    
    def test_cleanup_session(self):
        """Test session cleanup."""
        manager = FingerprintManager()
        
        # Create session data
        manager.generate_session_fingerprint("session1")
        assert "session1" in manager.randomizers
        assert "session1" in manager.session_fingerprints
        
        # Cleanup
        manager.cleanup_session("session1")
        assert "session1" not in manager.randomizers
        assert "session1" not in manager.session_fingerprints
    
    def test_get_all_statistics(self):
        """Test getting all session statistics."""
        manager = FingerprintManager()
        
        # Create multiple sessions
        manager.generate_session_fingerprint("session1", BrowserType.CHROME)
        manager.generate_session_fingerprint("session2", BrowserType.FIREFOX)
        
        stats = manager.get_all_statistics()
        
        assert "session1" in stats
        assert "session2" in stats
        assert isinstance(stats["session1"], dict)
        assert isinstance(stats["session2"], dict)


class TestFingerprintRandomizationIntegration:
    """Integration tests for fingerprint randomization."""
    
    def test_complete_fingerprint_workflow(self):
        """Test complete fingerprint workflow."""
        manager = FingerprintManager()
        
        # Generate fingerprint for session
        fingerprint = manager.generate_session_fingerprint("test_session", BrowserType.CHROME)
        
        # Get headers
        headers = manager.get_session_headers("test_session")
        assert headers["User-Agent"] == fingerprint.user_agent
        
        # Get JavaScript
        js_code = manager.get_session_javascript("test_session")
        assert fingerprint.user_agent in js_code
        
        # Get statistics
        stats = manager.get_all_statistics()
        assert "test_session" in stats
        assert stats["test_session"]["total_fingerprints"] > 0
    
    def test_fingerprint_consistency(self):
        """Test that fingerprints are consistent within a session."""
        manager = FingerprintManager()
        
        # Generate fingerprint
        fingerprint1 = manager.generate_session_fingerprint("session1")
        
        # Get headers multiple times
        headers1 = manager.get_session_headers("session1")
        headers2 = manager.get_session_headers("session1")
        
        # Should be the same
        assert headers1["User-Agent"] == headers2["User-Agent"]
        assert headers1["Accept-Language"] == headers2["Accept-Language"]
    
    def test_multiple_sessions_isolation(self):
        """Test that multiple sessions are isolated."""
        manager = FingerprintManager()
        
        # Create two sessions
        fingerprint1 = manager.generate_session_fingerprint("session1", BrowserType.CHROME)
        fingerprint2 = manager.generate_session_fingerprint("session2", BrowserType.FIREFOX)
        
        # Get headers for each
        headers1 = manager.get_session_headers("session1")
        headers2 = manager.get_session_headers("session2")
        
        # Should be different
        assert headers1["User-Agent"] != headers2["User-Agent"]
        assert fingerprint1.user_agent != fingerprint2.user_agent
    
    def test_fingerprint_realism(self):
        """Test that generated fingerprints are realistic."""
        randomizer = FingerprintRandomizer(BrowserType.CHROME)
        fingerprint = randomizer.generate_fingerprint()
        
        # Check realistic values
        assert 1 <= fingerprint.hardware_concurrency <= 32
        assert 1 <= fingerprint.color_depth <= 32
        assert 0.5 <= fingerprint.pixel_ratio <= 4.0
        assert fingerprint.screen_resolution[0] > 0
        assert fingerprint.screen_resolution[1] > 0
        assert len(fingerprint.fonts) >= 5
        assert len(fingerprint.plugins) >= 1
        assert fingerprint.battery_level is None or 0 <= fingerprint.battery_level <= 1
        assert fingerprint.downlink > 0
        assert fingerprint.rtt > 0
    
    def test_timezone_offset_calculation(self):
        """Test timezone offset calculation."""
        randomizer = FingerprintRandomizer(BrowserType.CHROME)
        
        # Test known timezones
        assert randomizer._get_timezone_offset("America/New_York") == -300
        assert randomizer._get_timezone_offset("America/Los_Angeles") == -480
        assert randomizer._get_timezone_offset("Europe/London") == 0
        assert randomizer._get_timezone_offset("Asia/Tokyo") == 540
        
        # Test unknown timezone
        assert randomizer._get_timezone_offset("Unknown/Timezone") == 0
