"""
Browser fingerprint randomization for anti-detection.

This module provides comprehensive browser fingerprint randomization to make
web scraping appear more natural and avoid detection by fingerprinting systems.
"""

import random
import hashlib
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import platform
import sys
from urllib.parse import urlparse


class BrowserType(Enum):
    """Supported browser types."""
    CHROME = "chrome"
    FIREFOX = "firefox"
    SAFARI = "safari"
    EDGE = "edge"
    OPERA = "opera"


class OSFamily(Enum):
    """Operating system families."""
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"
    ANDROID = "android"
    IOS = "ios"


@dataclass
class BrowserFingerprint:
    """Represents a browser fingerprint."""
    user_agent: str
    screen_resolution: Tuple[int, int]
    timezone: str
    language: str
    platform: str
    hardware_concurrency: int
    device_memory: Optional[int]
    webgl_vendor: str
    webgl_renderer: str
    canvas_fingerprint: str
    audio_fingerprint: str
    fonts: List[str]
    plugins: List[str]
    webgl_extensions: List[str]
    touch_support: bool
    do_not_track: str
    cookie_enabled: bool
    local_storage_enabled: bool
    session_storage_enabled: bool
    indexed_db_enabled: bool
    web_sql_enabled: bool
    ad_blocker: bool
    battery_level: Optional[float]
    connection_type: str
    effective_type: str
    downlink: float
    rtt: int
    save_data: bool
    color_depth: int
    pixel_ratio: float
    orientation: str
    media_devices: List[str]
    permissions: Dict[str, str]
    geolocation: Optional[Tuple[float, float]]
    browser_version: str
    os_version: str
    architecture: str
    cpu_cores: int
    ram_gb: int
    gpu_vendor: str
    gpu_model: str


class FingerprintRandomizer:
    """Randomizes browser fingerprints for anti-detection."""
    
    def __init__(self, browser_type: BrowserType = BrowserType.CHROME):
        """Initialize the fingerprint randomizer.
        
        Args:
            browser_type: The browser type to simulate
        """
        self.browser_type = browser_type
        self.fingerprint_history = []
        self.current_fingerprint = None
        
        # Load fingerprint data
        self._load_fingerprint_data()
    
    def _load_fingerprint_data(self):
        """Load realistic fingerprint data for randomization."""
        self.user_agents = {
            BrowserType.CHROME: [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            ],
            BrowserType.FIREFOX: [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
                "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
            ],
            BrowserType.SAFARI: [
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15"
            ],
            BrowserType.EDGE: [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
            ],
            BrowserType.OPERA: [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0"
            ]
        }
        
        self.screen_resolutions = [
            (1920, 1080), (1366, 768), (1536, 864), (1440, 900), (1280, 720),
            (1600, 900), (1024, 768), (1280, 800), (2560, 1440), (3840, 2160),
            (1680, 1050), (1920, 1200), (2560, 1600), (2880, 1800), (3200, 1800)
        ]
        
        self.timezones = [
            "America/New_York", "America/Los_Angeles", "America/Chicago", "America/Denver",
            "Europe/London", "Europe/Paris", "Europe/Berlin", "Europe/Rome",
            "Asia/Tokyo", "Asia/Shanghai", "Asia/Seoul", "Asia/Kolkata",
            "Australia/Sydney", "Australia/Melbourne", "Pacific/Auckland"
        ]
        
        self.languages = [
            "en-US", "en-GB", "en-CA", "en-AU", "en-NZ",
            "es-ES", "es-MX", "es-AR", "fr-FR", "fr-CA",
            "de-DE", "it-IT", "pt-BR", "pt-PT", "ru-RU",
            "ja-JP", "ko-KR", "zh-CN", "zh-TW", "ar-SA"
        ]
        
        self.webgl_vendors = [
            "Google Inc.", "NVIDIA Corporation", "AMD", "Intel Inc.",
            "Microsoft Corporation", "Apple Inc.", "Mozilla"
        ]
        
        self.webgl_renderers = [
            "ANGLE (NVIDIA GeForce GTX 1060 Direct3D11 vs_5_0 ps_5_0)",
            "ANGLE (Intel(R) HD Graphics 620 Direct3D11 vs_5_0 ps_5_0)",
            "ANGLE (AMD Radeon RX 580 Direct3D11 vs_5_0 ps_5_0)",
            "WebKit WebGL", "Mozilla WebGL"
        ]
        
        self.fonts = [
            "Arial", "Helvetica", "Times New Roman", "Courier New", "Verdana",
            "Georgia", "Palatino", "Garamond", "Bookman", "Comic Sans MS",
            "Trebuchet MS", "Arial Black", "Impact", "Tahoma", "Calibri",
            "Cambria", "Candara", "Consolas", "Constantia", "Corbel"
        ]
        
        self.plugins = [
            "Chrome PDF Plugin", "Chrome PDF Viewer", "Native Client",
            "Widevine Content Decryption Module", "Shockwave Flash",
            "Adobe Acrobat", "Java Deployment Toolkit", "Silverlight Plug-In"
        ]
        
        self.webgl_extensions = [
            "ANGLE_instanced_arrays", "EXT_blend_minmax", "EXT_color_buffer_half_float",
            "EXT_disjoint_timer_query", "EXT_frag_depth", "EXT_shader_texture_lod",
            "EXT_texture_filter_anisotropic", "WEBKIT_EXT_texture_filter_anisotropic",
            "EXT_sRGB", "OES_element_index_uint", "OES_standard_derivatives",
            "OES_texture_float", "OES_texture_half_float", "OES_vertex_array_object",
            "WEBGL_color_buffer_float", "WEBGL_compressed_texture_s3tc",
            "WEBGL_debug_renderer_info", "WEBGL_debug_shaders", "WEBGL_depth_texture",
            "WEBGL_draw_buffers", "WEBGL_lose_context"
        ]
        
        self.media_devices = [
            "microphone", "camera", "speaker", "audioinput", "audiooutput",
            "videoinput", "videooutput"
        ]
        
        self.connection_types = [
            "wifi", "ethernet", "cellular", "bluetooth", "wimax", "other"
        ]
        
        self.effective_types = [
            "slow-2g", "2g", "3g", "4g", "5g"
        ]
    
    def generate_fingerprint(self) -> BrowserFingerprint:
        """Generate a randomized browser fingerprint.
        
        Returns:
            BrowserFingerprint object with randomized values
        """
        # Select random user agent
        user_agent = random.choice(self.user_agents[self.browser_type])
        
        # Extract OS and browser info from user agent
        os_family, os_version = self._extract_os_info(user_agent)
        browser_version = self._extract_browser_version(user_agent)
        
        # Generate randomized values
        screen_resolution = random.choice(self.screen_resolutions)
        timezone = random.choice(self.timezones)
        language = random.choice(self.languages)
        platform = self._generate_platform_string(os_family, os_version)
        
        # Hardware specs
        hardware_concurrency = random.choice([2, 4, 6, 8, 12, 16, 24, 32])
        device_memory = random.choice([2, 4, 8, 16, 32, 64]) if random.random() > 0.3 else None
        cpu_cores = hardware_concurrency
        ram_gb = device_memory or random.choice([4, 8, 16, 32, 64])
        
        # WebGL info
        webgl_vendor = random.choice(self.webgl_vendors)
        webgl_renderer = random.choice(self.webgl_renderers)
        
        # Generate fingerprints
        canvas_fingerprint = self._generate_canvas_fingerprint()
        audio_fingerprint = self._generate_audio_fingerprint()
        
        # Fonts and plugins
        fonts = random.sample(self.fonts, min(random.randint(10, 20), len(self.fonts)))
        plugins = random.sample(self.plugins, min(random.randint(3, 8), len(self.plugins)))
        webgl_extensions = random.sample(self.webgl_extensions, min(random.randint(15, 25), len(self.webgl_extensions)))
        
        # Device capabilities
        touch_support = random.random() > 0.7  # 30% chance of touch support
        do_not_track = random.choice(["1", "0", "null"])
        cookie_enabled = random.random() > 0.05  # 95% chance
        local_storage_enabled = random.random() > 0.1  # 90% chance
        session_storage_enabled = random.random() > 0.1  # 90% chance
        indexed_db_enabled = random.random() > 0.2  # 80% chance
        web_sql_enabled = random.random() > 0.5  # 50% chance
        ad_blocker = random.random() > 0.8  # 20% chance
        
        # Battery and connection
        battery_level = random.uniform(0.1, 1.0) if random.random() > 0.3 else None
        connection_type = random.choice(self.connection_types)
        effective_type = random.choice(self.effective_types)
        downlink = random.uniform(0.5, 100.0)
        rtt = random.randint(50, 500)
        save_data = random.random() > 0.9  # 10% chance
        
        # Display properties
        color_depth = random.choice([24, 32])
        pixel_ratio = random.choice([1.0, 1.25, 1.5, 2.0, 3.0])
        orientation = random.choice(["portrait", "landscape"])
        
        # Media devices
        media_devices = random.sample(self.media_devices, min(random.randint(2, 5), len(self.media_devices)))
        
        # Permissions
        permissions = {
            "geolocation": random.choice(["granted", "denied", "prompt"]),
            "camera": random.choice(["granted", "denied", "prompt"]),
            "microphone": random.choice(["granted", "denied", "prompt"]),
            "notifications": random.choice(["granted", "denied", "prompt"])
        }
        
        # Geolocation (optional)
        geolocation = None
        if permissions["geolocation"] == "granted" and random.random() > 0.7:
            geolocation = (
                random.uniform(-90, 90),  # latitude
                random.uniform(-180, 180)  # longitude
            )
        
        # GPU info
        gpu_vendor = random.choice(["NVIDIA", "AMD", "Intel", "Apple", "Microsoft"])
        gpu_model = self._generate_gpu_model(gpu_vendor)
        
        # Architecture
        architecture = random.choice(["x64", "x86", "arm64", "arm"])
        
        fingerprint = BrowserFingerprint(
            user_agent=user_agent,
            screen_resolution=screen_resolution,
            timezone=timezone,
            language=language,
            platform=platform,
            hardware_concurrency=hardware_concurrency,
            device_memory=device_memory,
            webgl_vendor=webgl_vendor,
            webgl_renderer=webgl_renderer,
            canvas_fingerprint=canvas_fingerprint,
            audio_fingerprint=audio_fingerprint,
            fonts=fonts,
            plugins=plugins,
            webgl_extensions=webgl_extensions,
            touch_support=touch_support,
            do_not_track=do_not_track,
            cookie_enabled=cookie_enabled,
            local_storage_enabled=local_storage_enabled,
            session_storage_enabled=session_storage_enabled,
            indexed_db_enabled=indexed_db_enabled,
            web_sql_enabled=web_sql_enabled,
            ad_blocker=ad_blocker,
            battery_level=battery_level,
            connection_type=connection_type,
            effective_type=effective_type,
            downlink=downlink,
            rtt=rtt,
            save_data=save_data,
            color_depth=color_depth,
            pixel_ratio=pixel_ratio,
            orientation=orientation,
            media_devices=media_devices,
            permissions=permissions,
            geolocation=geolocation,
            browser_version=browser_version,
            os_version=os_version,
            architecture=architecture,
            cpu_cores=cpu_cores,
            ram_gb=ram_gb,
            gpu_vendor=gpu_vendor,
            gpu_model=gpu_model
        )
        
        self.current_fingerprint = fingerprint
        self.fingerprint_history.append(fingerprint)
        
        # Keep only last 100 fingerprints
        if len(self.fingerprint_history) > 100:
            self.fingerprint_history = self.fingerprint_history[-100:]
        
        return fingerprint
    
    def _extract_os_info(self, user_agent: str) -> Tuple[OSFamily, str]:
        """Extract OS family and version from user agent."""
        user_agent_lower = user_agent.lower()
        
        if "windows nt 10.0" in user_agent_lower:
            return OSFamily.WINDOWS, "10"
        elif "windows nt 6.3" in user_agent_lower:
            return OSFamily.WINDOWS, "8.1"
        elif "windows nt 6.1" in user_agent_lower:
            return OSFamily.WINDOWS, "7"
        elif "mac os x 10_15" in user_agent_lower:
            return OSFamily.MACOS, "10.15"
        elif "mac os x 10_14" in user_agent_lower:
            return OSFamily.MACOS, "10.14"
        elif "linux" in user_agent_lower:
            return OSFamily.LINUX, "Ubuntu 20.04"
        elif "android" in user_agent_lower:
            return OSFamily.ANDROID, "11"
        elif "iphone" in user_agent_lower or "ipad" in user_agent_lower:
            return OSFamily.IOS, "15.0"
        else:
            return OSFamily.WINDOWS, "10"
    
    def _extract_browser_version(self, user_agent: str) -> str:
        """Extract browser version from user agent."""
        if "chrome/" in user_agent:
            start = user_agent.find("chrome/") + 7
            end = user_agent.find(" ", start)
            return user_agent[start:end] if end != -1 else user_agent[start:]
        elif "firefox/" in user_agent:
            start = user_agent.find("firefox/") + 8
            end = user_agent.find(" ", start)
            return user_agent[start:end] if end != -1 else user_agent[start:]
        elif "safari/" in user_agent and "version/" in user_agent:
            start = user_agent.find("version/") + 8
            end = user_agent.find(" ", start)
            return user_agent[start:end] if end != -1 else user_agent[start:]
        else:
            return "120.0.0.0"
    
    def _generate_platform_string(self, os_family: OSFamily, os_version: str) -> str:
        """Generate platform string."""
        if os_family == OSFamily.WINDOWS:
            return f"Win32; x64"
        elif os_family == OSFamily.MACOS:
            return f"MacIntel; x64"
        elif os_family == OSFamily.LINUX:
            return "Linux x86_64"
        elif os_family == OSFamily.ANDROID:
            return "Linux; Android"
        elif os_family == OSFamily.IOS:
            return "iPhone; CPU iPhone OS"
        else:
            return "Win32; x64"
    
    def _generate_canvas_fingerprint(self) -> str:
        """Generate a canvas fingerprint."""
        # Simulate canvas fingerprinting
        canvas_data = f"canvas_{random.randint(100000, 999999)}"
        return hashlib.md5(canvas_data.encode()).hexdigest()
    
    def _generate_audio_fingerprint(self) -> str:
        """Generate an audio fingerprint."""
        # Simulate audio fingerprinting
        audio_data = f"audio_{random.randint(100000, 999999)}"
        return hashlib.md5(audio_data.encode()).hexdigest()
    
    def _generate_gpu_model(self, vendor: str) -> str:
        """Generate GPU model based on vendor."""
        gpu_models = {
            "NVIDIA": ["GeForce GTX 1060", "GeForce GTX 1070", "GeForce GTX 1080", "GeForce RTX 2060", "GeForce RTX 3070"],
            "AMD": ["Radeon RX 580", "Radeon RX 6600", "Radeon RX 6700 XT", "Radeon RX 6800 XT"],
            "Intel": ["HD Graphics 620", "UHD Graphics 630", "Iris Xe Graphics", "Arc A380"],
            "Apple": ["Apple M1", "Apple M2", "Apple M3", "Intel Iris Pro"],
            "Microsoft": ["Microsoft Basic Render Driver", "Microsoft Remote Display Adapter"]
        }
        return random.choice(gpu_models.get(vendor, ["Unknown GPU"]))
    
    def get_headers(self, fingerprint: Optional[BrowserFingerprint] = None) -> Dict[str, str]:
        """Generate HTTP headers based on fingerprint.
        
        Args:
            fingerprint: Browser fingerprint to use (uses current if None)
            
        Returns:
            Dictionary of HTTP headers
        """
        if fingerprint is None:
            fingerprint = self.current_fingerprint or self.generate_fingerprint()
        
        headers = {
            "User-Agent": fingerprint.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": f"{fingerprint.language},en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": fingerprint.do_not_track,
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0"
        }
        
        # Add browser-specific headers
        if self.browser_type == BrowserType.CHROME:
            headers["Sec-Ch-Ua"] = f'"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'
            headers["Sec-Ch-Ua-Mobile"] = "?0"
            headers["Sec-Ch-Ua-Platform"] = f'"{fingerprint.platform.split(";")[0]}"'
        elif self.browser_type == BrowserType.FIREFOX:
            headers["Sec-Fetch-Dest"] = "document"
            headers["Sec-Fetch-Mode"] = "navigate"
            headers["Sec-Fetch-Site"] = "none"
            headers["Sec-Fetch-User"] = "?1"
        
        return headers
    
    def get_javascript_fingerprint(self, fingerprint: Optional[BrowserFingerprint] = None) -> str:
        """Generate JavaScript code to set fingerprint properties.
        
        Args:
            fingerprint: Browser fingerprint to use (uses current if None)
            
        Returns:
            JavaScript code as string
        """
        if fingerprint is None:
            fingerprint = self.current_fingerprint or self.generate_fingerprint()
        
        js_code = f"""
        // Override navigator properties
        Object.defineProperty(navigator, 'userAgent', {{
            get: () => '{fingerprint.user_agent}'
        }});
        
        Object.defineProperty(navigator, 'platform', {{
            get: () => '{fingerprint.platform}'
        }});
        
        Object.defineProperty(navigator, 'language', {{
            get: () => '{fingerprint.language}'
        }});
        
        Object.defineProperty(navigator, 'languages', {{
            get: () => ['{fingerprint.language}', 'en']
        }});
        
        Object.defineProperty(navigator, 'hardwareConcurrency', {{
            get: () => {fingerprint.hardware_concurrency}
        }});
        
        Object.defineProperty(navigator, 'deviceMemory', {{
            get: () => {fingerprint.device_memory or 'undefined'}
        }});
        
        Object.defineProperty(navigator, 'cookieEnabled', {{
            get: () => {str(fingerprint.cookie_enabled).lower()}
        }});
        
        Object.defineProperty(navigator, 'doNotTrack', {{
            get: () => '{fingerprint.do_not_track}'
        }});
        
        // Override screen properties
        Object.defineProperty(screen, 'width', {{
            get: () => {fingerprint.screen_resolution[0]}
        }});
        
        Object.defineProperty(screen, 'height', {{
            get: () => {fingerprint.screen_resolution[1]}
        }});
        
        Object.defineProperty(screen, 'colorDepth', {{
            get: () => {fingerprint.color_depth}
        }});
        
        Object.defineProperty(screen, 'pixelDepth', {{
            get: () => {fingerprint.color_depth}
        }});
        
        // Override devicePixelRatio
        Object.defineProperty(window, 'devicePixelRatio', {{
            get: () => {fingerprint.pixel_ratio}
        }});
        
        // Override WebGL properties
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {{
            if (parameter === 37445) {{
                return '{fingerprint.webgl_vendor}';
            }}
            if (parameter === 37446) {{
                return '{fingerprint.webgl_renderer}';
            }}
            return getParameter.call(this, parameter);
        }};
        
        // Override timezone
        const originalDate = Date;
        Date = function(...args) {{
            const date = new originalDate(...args);
            const offset = {self._get_timezone_offset(fingerprint.timezone)};
            date.getTimezoneOffset = () => -offset;
            return date;
        }};
        Date.prototype = originalDate.prototype;
        Date.now = originalDate.now;
        Date.UTC = originalDate.UTC;
        Date.parse = originalDate.parse;
        
        // Override battery API
        if ('getBattery' in navigator) {{
            navigator.getBattery = () => Promise.resolve({{
                level: {fingerprint.battery_level or 0.8},
                charging: true,
                chargingTime: 0,
                dischargingTime: Infinity
            }});
        }}
        
        // Override connection API
        if ('connection' in navigator) {{
            Object.defineProperty(navigator, 'connection', {{
                get: () => ({{
                    effectiveType: '{fingerprint.effective_type}',
                    downlink: {fingerprint.downlink},
                    rtt: {fingerprint.rtt},
                    saveData: {str(fingerprint.save_data).lower()}
                }})
            }});
        }}
        
        // Override media devices
        if ('mediaDevices' in navigator) {{
            navigator.mediaDevices.enumerateDevices = () => Promise.resolve([
                {{ kind: 'audioinput', deviceId: 'default' }},
                {{ kind: 'audiooutput', deviceId: 'default' }},
                {{ kind: 'videoinput', deviceId: 'default' }}
            ]);
        }}
        
        // Override permissions API
        if ('permissions' in navigator) {{
            navigator.permissions.query = (permission) => Promise.resolve({{
                state: '{fingerprint.permissions.get("geolocation", "prompt")}'
            }});
        }}
        """
        
        return js_code
    
    def _get_timezone_offset(self, timezone: str) -> int:
        """Get timezone offset in minutes."""
        # Simplified timezone offset calculation
        timezone_offsets = {
            "America/New_York": -300,  # EST
            "America/Los_Angeles": -480,  # PST
            "America/Chicago": -360,  # CST
            "America/Denver": -420,  # MST
            "Europe/London": 0,  # GMT
            "Europe/Paris": 60,  # CET
            "Europe/Berlin": 60,  # CET
            "Asia/Tokyo": 540,  # JST
            "Asia/Shanghai": 480,  # CST
            "Asia/Seoul": 540,  # KST
            "Asia/Kolkata": 330,  # IST
            "Australia/Sydney": 660,  # AEDT
            "Australia/Melbourne": 660,  # AEDT
            "Pacific/Auckland": 780  # NZDT
        }
        return timezone_offsets.get(timezone, 0)
    
    def get_fingerprint_hash(self, fingerprint: Optional[BrowserFingerprint] = None) -> str:
        """Generate a hash of the fingerprint for identification.
        
        Args:
            fingerprint: Browser fingerprint to use (uses current if None)
            
        Returns:
            MD5 hash of the fingerprint
        """
        if fingerprint is None:
            fingerprint = self.current_fingerprint or self.generate_fingerprint()
        
        # Create a string representation of key fingerprint properties
        fingerprint_string = f"{fingerprint.user_agent}|{fingerprint.screen_resolution}|{fingerprint.timezone}|{fingerprint.language}|{fingerprint.platform}|{fingerprint.hardware_concurrency}|{fingerprint.webgl_vendor}|{fingerprint.webgl_renderer}"
        
        return hashlib.md5(fingerprint_string.encode()).hexdigest()
    
    def is_fingerprint_unique(self, fingerprint: Optional[BrowserFingerprint] = None) -> bool:
        """Check if the fingerprint is unique in the history.
        
        Args:
            fingerprint: Browser fingerprint to check (uses current if None)
            
        Returns:
            True if fingerprint is unique, False otherwise
        """
        if fingerprint is None:
            fingerprint = self.current_fingerprint
        
        if not fingerprint:
            return True
        
        fingerprint_hash = self.get_fingerprint_hash(fingerprint)
        
        for historical_fingerprint in self.fingerprint_history[:-1]:  # Exclude current
            if self.get_fingerprint_hash(historical_fingerprint) == fingerprint_hash:
                return False
        
        return True
    
    def get_fingerprint_statistics(self) -> Dict[str, Any]:
        """Get statistics about generated fingerprints.
        
        Returns:
            Dictionary of fingerprint statistics
        """
        if not self.fingerprint_history:
            return {
                "total_fingerprints": 0,
                "unique_fingerprints": 0,
                "browser_types": {},
                "os_families": {},
                "screen_resolutions": {},
                "timezones": {},
                "languages": {}
            }
        
        stats = {
            "total_fingerprints": len(self.fingerprint_history),
            "unique_fingerprints": len(set(self.get_fingerprint_hash(fp) for fp in self.fingerprint_history)),
            "browser_types": {},
            "os_families": {},
            "screen_resolutions": {},
            "timezones": {},
            "languages": {}
        }
        
        for fingerprint in self.fingerprint_history:
            # Count browser types
            browser_type = self.browser_type.value
            stats["browser_types"][browser_type] = stats["browser_types"].get(browser_type, 0) + 1
            
            # Count OS families
            os_family, _ = self._extract_os_info(fingerprint.user_agent)
            stats["os_families"][os_family.value] = stats["os_families"].get(os_family.value, 0) + 1
            
            # Count screen resolutions
            resolution = f"{fingerprint.screen_resolution[0]}x{fingerprint.screen_resolution[1]}"
            stats["screen_resolutions"][resolution] = stats["screen_resolutions"].get(resolution, 0) + 1
            
            # Count timezones
            stats["timezones"][fingerprint.timezone] = stats["timezones"].get(fingerprint.timezone, 0) + 1
            
            # Count languages
            stats["languages"][fingerprint.language] = stats["languages"].get(fingerprint.language, 0) + 1
        
        return stats


class FingerprintManager:
    """Manages multiple fingerprint randomizers."""
    
    def __init__(self):
        """Initialize the fingerprint manager."""
        self.randomizers: Dict[str, FingerprintRandomizer] = {}
        self.session_fingerprints: Dict[str, BrowserFingerprint] = {}
    
    def create_randomizer(self, session_id: str, browser_type: BrowserType = BrowserType.CHROME) -> FingerprintRandomizer:
        """Create a new fingerprint randomizer for a session.
        
        Args:
            session_id: Unique identifier for the session
            browser_type: Browser type to simulate
            
        Returns:
            FingerprintRandomizer instance
        """
        randomizer = FingerprintRandomizer(browser_type)
        self.randomizers[session_id] = randomizer
        return randomizer
    
    def get_randomizer(self, session_id: str) -> Optional[FingerprintRandomizer]:
        """Get a fingerprint randomizer by session ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            FingerprintRandomizer instance or None
        """
        return self.randomizers.get(session_id)
    
    def generate_session_fingerprint(self, session_id: str, browser_type: BrowserType = BrowserType.CHROME) -> BrowserFingerprint:
        """Generate a fingerprint for a session.
        
        Args:
            session_id: Session identifier
            browser_type: Browser type to simulate
            
        Returns:
            BrowserFingerprint instance
        """
        randomizer = self.get_randomizer(session_id)
        if not randomizer:
            randomizer = self.create_randomizer(session_id, browser_type)
        
        fingerprint = randomizer.generate_fingerprint()
        self.session_fingerprints[session_id] = fingerprint
        
        return fingerprint
    
    def get_session_headers(self, session_id: str) -> Dict[str, str]:
        """Get HTTP headers for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary of HTTP headers
        """
        fingerprint = self.session_fingerprints.get(session_id)
        if not fingerprint:
            fingerprint = self.generate_session_fingerprint(session_id)
        
        randomizer = self.get_randomizer(session_id)
        return randomizer.get_headers(fingerprint)
    
    def get_session_javascript(self, session_id: str) -> str:
        """Get JavaScript fingerprint code for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            JavaScript code as string
        """
        fingerprint = self.session_fingerprints.get(session_id)
        if not fingerprint:
            fingerprint = self.generate_session_fingerprint(session_id)
        
        randomizer = self.get_randomizer(session_id)
        return randomizer.get_javascript_fingerprint(fingerprint)
    
    def cleanup_session(self, session_id: str):
        """Clean up a session and remove its data.
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.randomizers:
            del self.randomizers[session_id]
        if session_id in self.session_fingerprints:
            del self.session_fingerprints[session_id]
    
    def get_all_statistics(self) -> Dict[str, Any]:
        """Get statistics for all sessions.
        
        Returns:
            Dictionary of session statistics
        """
        all_stats = {}
        for session_id, randomizer in self.randomizers.items():
            all_stats[session_id] = randomizer.get_fingerprint_statistics()
        return all_stats
