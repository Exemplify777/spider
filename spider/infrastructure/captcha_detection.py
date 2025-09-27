"""
Advanced CAPTCHA detection and classification system.

This module provides intelligent CAPTCHA detection, classification, and solving
capabilities with support for multiple CAPTCHA types and providers.
"""

import asyncio
import base64
import io
import json
import time
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum
import hashlib
import requests
from PIL import Image
try:
    import cv2
    import numpy as np
    from sklearn.cluster import KMeans
    from sklearn.feature_extraction.text import TfidfVectorizer
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    # Create dummy classes for when dependencies are not available
    class cv2:
        @staticmethod
        def cvtColor(img, code):
            return img
        @staticmethod
        def threshold(img, thresh, maxval, type):
            return None, img
        @staticmethod
        def morphologyEx(img, op, kernel):
            return img
        @staticmethod
        def findContours(img, mode, method):
            return [], None
        @staticmethod
        def contourArea(contour):
            return 100
        @staticmethod
        def boundingRect(contour):
            return 0, 0, 50, 20
        @staticmethod
        def GaussianBlur(img, ksize, sigma):
            return img
        @staticmethod
        def rectangle(img, pt1, pt2, color, thickness):
            return img
        RETR_EXTERNAL = 0
        CHAIN_APPROX_SIMPLE = 0
        THRESH_BINARY = 0
        THRESH_OTSU = 0
        MORPH_CLOSE = 0
        COLOR_RGB2GRAY = 0
    
    class np:
        @staticmethod
        def array(data):
            return data
        @staticmethod
        def var(data):
            return 1000
        @staticmethod
        def std(data):
            return 50
        @staticmethod
        def ones(shape, dtype):
            return [[128] * shape[1] for _ in range(shape[0])]
        @staticmethod
        def uint8():
            return int
        @staticmethod
        def random():
            class Random:
                @staticmethod
                def randint(low, high, size, dtype):
                    return [[128] * size[1] for _ in range(size[0])]
            return Random()
    
    class KMeans:
        def __init__(self, n_clusters):
            self.n_clusters = n_clusters
    
    class TfidfVectorizer:
        def __init__(self):
            pass
import re


class CAPTCHAType(Enum):
    """Types of CAPTCHAs that can be detected."""
    TEXT_BASED = "text_based"
    IMAGE_BASED = "image_based"
    MATH_EQUATION = "math_equation"
    RECAPTCHA_V2 = "recaptcha_v2"
    RECAPTCHA_V3 = "recaptcha_v3"
    HCAPTCHA = "hcaptcha"
    FUNCAPTCHA = "funcaptcha"
    GEETEST = "geetest"
    UNKNOWN = "unknown"


class CAPTCHADifficulty(Enum):
    """CAPTCHA difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    VERY_HARD = "very_hard"


@dataclass
class CAPTCHADetection:
    """Represents a detected CAPTCHA."""
    captcha_type: CAPTCHAType
    difficulty: CAPTCHADifficulty
    confidence: float
    location: Tuple[int, int, int, int]  # x, y, width, height
    image_data: Optional[bytes] = None
    text_content: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class CAPTCHASolution:
    """Represents a CAPTCHA solution."""
    solution: str
    confidence: float
    solving_time: float
    provider: str
    cost: float = 0.0


class CAPTCHADetector:
    """Advanced CAPTCHA detection and classification system."""
    
    def __init__(self):
        """Initialize the CAPTCHA detector."""
        self.detection_patterns = {
            CAPTCHAType.TEXT_BASED: [
                r'captcha',
                r'verify.*human',
                r'prove.*not.*robot',
                r'security.*check',
                r'anti.*bot'
            ],
            CAPTCHAType.RECAPTCHA_V2: [
                r'g-recaptcha',
                r'data-sitekey',
                r'google.*recaptcha',
                r'rc-anchor'
            ],
            CAPTCHAType.RECAPTCHA_V3: [
                r'grecaptcha',
                r'recaptcha.*v3',
                r'data-action'
            ],
            CAPTCHAType.HCAPTCHA: [
                r'h-captcha',
                r'hcaptcha',
                r'data-hcaptcha'
            ],
            CAPTCHAType.FUNCAPTCHA: [
                r'funcaptcha',
                r'arkoselabs',
                r'data-pkey'
            ],
            CAPTCHAType.GEETEST: [
                r'geetest',
                r'gt-.*captcha',
                r'geetest.*captcha'
            ]
        }
        
        self.image_patterns = {
            CAPTCHAType.TEXT_BASED: self._detect_text_captcha,
            CAPTCHAType.MATH_EQUATION: self._detect_math_captcha,
            CAPTCHAType.IMAGE_BASED: self._detect_image_based_captcha
        }
        
        self.difficulty_indicators = {
            CAPTCHADifficulty.EASY: {
                'text_length': (3, 5),
                'distortion': 0.1,
                'noise_level': 0.1,
                'color_complexity': 0.2
            },
            CAPTCHADifficulty.MEDIUM: {
                'text_length': (4, 7),
                'distortion': 0.3,
                'noise_level': 0.3,
                'color_complexity': 0.4
            },
            CAPTCHADifficulty.HARD: {
                'text_length': (5, 10),
                'distortion': 0.5,
                'noise_level': 0.5,
                'color_complexity': 0.6
            },
            CAPTCHADifficulty.VERY_HARD: {
                'text_length': (6, 15),
                'distortion': 0.7,
                'noise_level': 0.7,
                'color_complexity': 0.8
            }
        }
    
    async def detect_captcha(self, html_content: str, page_url: str = None) -> List[CAPTCHADetection]:
        """Detect CAPTCHAs in HTML content.
        
        Args:
            html_content: The HTML content to analyze
            page_url: Optional URL of the page
            
        Returns:
            List of detected CAPTCHAs
        """
        detections = []
        
        # Detect by HTML patterns
        html_detections = await self._detect_by_html_patterns(html_content)
        detections.extend(html_detections)
        
        # Detect by image analysis
        image_detections = await self._detect_by_image_analysis(html_content)
        detections.extend(image_detections)
        
        # Remove duplicates and merge similar detections
        detections = self._merge_detections(detections)
        
        return detections
    
    async def _detect_by_html_patterns(self, html_content: str) -> List[CAPTCHADetection]:
        """Detect CAPTCHAs using HTML pattern matching."""
        detections = []
        html_lower = html_content.lower()
        
        for captcha_type, patterns in self.detection_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, html_lower, re.IGNORECASE)
                for match in matches:
                    confidence = self._calculate_pattern_confidence(match.group(), pattern)
                    
                    detection = CAPTCHADetection(
                        captcha_type=captcha_type,
                        difficulty=CAPTCHADifficulty.MEDIUM,  # Default
                        confidence=confidence,
                        location=(0, 0, 0, 0),  # Will be updated if element found
                        text_content=match.group(),
                        metadata={'pattern': pattern, 'match_position': match.span()}
                    )
                    detections.append(detection)
        
        return detections
    
    async def _detect_by_image_analysis(self, html_content: str) -> List[CAPTCHADetection]:
        """Detect CAPTCHAs by analyzing images in the HTML."""
        detections = []
        
        # Extract image URLs from HTML
        img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
        img_matches = re.finditer(img_pattern, html_content, re.IGNORECASE)
        
        for match in img_matches:
            img_url = match.group(1)
            try:
                # Download and analyze image
                image_data = await self._download_image(img_url)
                if image_data:
                    image_detections = await self._analyze_image_for_captcha(image_data)
                    detections.extend(image_detections)
            except Exception as e:
                # Skip images that can't be downloaded
                continue
        
        return detections
    
    async def _analyze_image_for_captcha(self, image_data: bytes) -> List[CAPTCHADetection]:
        """Analyze an image to detect if it's a CAPTCHA."""
        detections = []
        
        if not CV2_AVAILABLE:
            # Return empty list if dependencies are not available
            return detections
        
        try:
            # Convert to PIL Image
            image = Image.open(io.BytesIO(image_data))
            image_array = np.array(image)
            
            # Analyze with different methods
            for captcha_type, detector_func in self.image_patterns.items():
                result = await detector_func(image_array)
                if result:
                    detection = CAPTCHADetection(
                        captcha_type=captcha_type,
                        difficulty=result['difficulty'],
                        confidence=result['confidence'],
                        location=(0, 0, image.width, image.height),
                        image_data=image_data,
                        metadata=result.get('metadata', {})
                    )
                    detections.append(detection)
        
        except Exception as e:
            # Skip images that can't be analyzed
            pass
        
        return detections
    
    async def _detect_text_captcha(self, image_array: np.ndarray) -> Optional[Dict[str, Any]]:
        """Detect text-based CAPTCHAs."""
        # Convert to grayscale
        if len(image_array.shape) == 3:
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = image_array
        
        # Apply preprocessing
        processed = self._preprocess_captcha_image(gray)
        
        # Detect text regions
        text_regions = self._find_text_regions(processed)
        
        if len(text_regions) > 0:
            # Analyze text characteristics
            text_length = self._estimate_text_length(text_regions)
            distortion = self._calculate_distortion(processed)
            noise_level = self._calculate_noise_level(processed)
            
            # Determine difficulty
            difficulty = self._classify_difficulty({
                'text_length': text_length,
                'distortion': distortion,
                'noise_level': noise_level
            })
            
            confidence = min(0.9, 0.5 + (len(text_regions) * 0.1))
            
            return {
                'confidence': confidence,
                'difficulty': difficulty,
                'metadata': {
                    'text_regions': len(text_regions),
                    'text_length': text_length,
                    'distortion': distortion,
                    'noise_level': noise_level
                }
            }
        
        return None
    
    async def _detect_math_captcha(self, image_array: np.ndarray) -> Optional[Dict[str, Any]]:
        """Detect math equation CAPTCHAs."""
        # Look for mathematical symbols
        math_symbols = ['+', '-', '×', '÷', '=', '?']
        
        # Convert to grayscale and preprocess
        if len(image_array.shape) == 3:
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = image_array
        
        processed = self._preprocess_captcha_image(gray)
        
        # Use OCR to detect text (simplified)
        text_content = self._extract_text_from_image(processed)
        
        # Check for math symbols
        math_symbol_count = sum(1 for symbol in math_symbols if symbol in text_content)
        
        if math_symbol_count > 0:
            confidence = min(0.9, 0.6 + (math_symbol_count * 0.1))
            difficulty = CAPTCHADifficulty.MEDIUM  # Math CAPTCHAs are usually medium difficulty
            
            return {
                'confidence': confidence,
                'difficulty': difficulty,
                'metadata': {
                    'math_symbols': math_symbol_count,
                    'text_content': text_content
                }
            }
        
        return None
    
    async def _detect_image_based_captcha(self, image_array: np.ndarray) -> Optional[Dict[str, Any]]:
        """Detect image-based CAPTCHAs (like "select all images with cars")."""
        # Look for multiple distinct objects
        if len(image_array.shape) == 3:
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = image_array
        
        # Detect contours
        contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by size
        significant_contours = [c for c in contours if cv2.contourArea(c) > 100]
        
        if len(significant_contours) >= 3:  # Multiple objects suggest image CAPTCHA
            confidence = min(0.9, 0.4 + (len(significant_contours) * 0.05))
            difficulty = CAPTCHADifficulty.HARD  # Image CAPTCHAs are usually harder
            
            return {
                'confidence': confidence,
                'difficulty': difficulty,
                'metadata': {
                    'object_count': len(significant_contours),
                    'contours': significant_contours
                }
            }
        
        return None
    
    def _preprocess_captcha_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for CAPTCHA analysis."""
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(image, (3, 3), 0)
        
        # Apply threshold
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Morphological operations
        kernel = np.ones((2, 2), np.uint8)
        processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        return processed
    
    def _find_text_regions(self, image: np.ndarray) -> List[np.ndarray]:
        """Find text regions in the image."""
        # Find contours
        contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        text_regions = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if 50 < area < 2000:  # Filter by area
                x, y, w, h = cv2.boundingRect(contour)
                if 10 < w < 100 and 10 < h < 50:  # Filter by dimensions
                    text_regions.append(contour)
        
        return text_regions
    
    def _estimate_text_length(self, text_regions: List[np.ndarray]) -> int:
        """Estimate the length of text in CAPTCHA."""
        return len(text_regions)
    
    def _calculate_distortion(self, image: np.ndarray) -> float:
        """Calculate the distortion level of the image."""
        # Calculate the variance of the image
        variance = np.var(image)
        return min(1.0, variance / 10000)  # Normalize
    
    def _calculate_noise_level(self, image: np.ndarray) -> float:
        """Calculate the noise level in the image."""
        # Calculate the standard deviation
        std_dev = np.std(image)
        return min(1.0, std_dev / 100)  # Normalize
    
    def _classify_difficulty(self, characteristics: Dict[str, Any]) -> CAPTCHADifficulty:
        """Classify CAPTCHA difficulty based on characteristics."""
        text_length = characteristics.get('text_length', 0)
        distortion = characteristics.get('distortion', 0)
        noise_level = characteristics.get('noise_level', 0)
        
        # Calculate difficulty score
        difficulty_score = (
            (text_length - 3) * 0.2 +
            distortion * 0.4 +
            noise_level * 0.4
        )
        
        if difficulty_score < 0.3:
            return CAPTCHADifficulty.EASY
        elif difficulty_score < 0.6:
            return CAPTCHADifficulty.MEDIUM
        elif difficulty_score < 0.8:
            return CAPTCHADifficulty.HARD
        else:
            return CAPTCHADifficulty.VERY_HARD
    
    def _extract_text_from_image(self, image: np.ndarray) -> str:
        """Extract text from image using basic OCR techniques."""
        # This is a simplified OCR implementation
        # In production, you would use libraries like Tesseract
        
        # For now, return a placeholder
        return "CAPTCHA_TEXT"
    
    def _calculate_pattern_confidence(self, match_text: str, pattern: str) -> float:
        """Calculate confidence based on pattern match."""
        # Longer matches are more confident
        length_factor = min(1.0, len(match_text) / 20)
        
        # Exact pattern matches are more confident
        exact_match = 1.0 if match_text.lower() == pattern.lower() else 0.8
        
        return min(0.95, length_factor * exact_match)
    
    async def _download_image(self, url: str) -> Optional[bytes]:
        """Download image from URL."""
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.content
        except Exception:
            pass
        return None
    
    def _merge_detections(self, detections: List[CAPTCHADetection]) -> List[CAPTCHADetection]:
        """Merge similar detections to avoid duplicates."""
        if not detections:
            return []
        
        # Group by type and confidence
        merged = []
        seen_types = set()
        
        for detection in sorted(detections, key=lambda x: x.confidence, reverse=True):
            if detection.captcha_type not in seen_types:
                merged.append(detection)
                seen_types.add(detection.captcha_type)
        
        return merged


class CAPTCHAClassifier:
    """Advanced CAPTCHA classification system."""
    
    def __init__(self):
        """Initialize the CAPTCHA classifier."""
        self.classifier_models = {}
        self.training_data = []
    
    async def classify_captcha(self, detection: CAPTCHADetection) -> Dict[str, Any]:
        """Classify a detected CAPTCHA."""
        classification = {
            'type': detection.captcha_type,
            'difficulty': detection.difficulty,
            'confidence': detection.confidence,
            'solving_strategy': self._get_solving_strategy(detection),
            'estimated_solving_time': self._estimate_solving_time(detection),
            'success_probability': self._calculate_success_probability(detection),
            'recommended_providers': self._get_recommended_providers(detection)
        }
        
        return classification
    
    def _get_solving_strategy(self, detection: CAPTCHADetection) -> str:
        """Get the recommended solving strategy for the CAPTCHA."""
        if detection.captcha_type == CAPTCHAType.TEXT_BASED:
            if detection.difficulty in [CAPTCHADifficulty.EASY, CAPTCHADifficulty.MEDIUM]:
                return "ocr_based"
            else:
                return "ml_based"
        
        elif detection.captcha_type == CAPTCHAType.MATH_EQUATION:
            return "math_solver"
        
        elif detection.captcha_type in [CAPTCHAType.RECAPTCHA_V2, CAPTCHAType.RECAPTCHA_V3]:
            return "recaptcha_solver"
        
        elif detection.captcha_type == CAPTCHAType.HCAPTCHA:
            return "hcaptcha_solver"
        
        elif detection.captcha_type == CAPTCHAType.IMAGE_BASED:
            return "image_classification"
        
        else:
            return "generic_solver"
    
    def _estimate_solving_time(self, detection: CAPTCHADetection) -> float:
        """Estimate the time required to solve the CAPTCHA."""
        base_times = {
            CAPTCHAType.TEXT_BASED: 5.0,
            CAPTCHAType.MATH_EQUATION: 3.0,
            CAPTCHAType.RECAPTCHA_V2: 15.0,
            CAPTCHAType.RECAPTCHA_V3: 10.0,
            CAPTCHAType.HCAPTCHA: 12.0,
            CAPTCHAType.IMAGE_BASED: 20.0
        }
        
        base_time = base_times.get(detection.captcha_type, 10.0)
        
        # Adjust for difficulty
        difficulty_multipliers = {
            CAPTCHADifficulty.EASY: 0.5,
            CAPTCHADifficulty.MEDIUM: 1.0,
            CAPTCHADifficulty.HARD: 2.0,
            CAPTCHADifficulty.VERY_HARD: 3.0
        }
        
        multiplier = difficulty_multipliers.get(detection.difficulty, 1.0)
        
        return base_time * multiplier
    
    def _calculate_success_probability(self, detection: CAPTCHADetection) -> float:
        """Calculate the probability of successfully solving the CAPTCHA."""
        base_probabilities = {
            CAPTCHAType.TEXT_BASED: 0.8,
            CAPTCHAType.MATH_EQUATION: 0.9,
            CAPTCHAType.RECAPTCHA_V2: 0.7,
            CAPTCHAType.RECAPTCHA_V3: 0.6,
            CAPTCHAType.HCAPTCHA: 0.7,
            CAPTCHAType.IMAGE_BASED: 0.5
        }
        
        base_prob = base_probabilities.get(detection.captcha_type, 0.6)
        
        # Adjust for difficulty
        difficulty_adjustments = {
            CAPTCHADifficulty.EASY: 0.2,
            CAPTCHADifficulty.MEDIUM: 0.0,
            CAPTCHADifficulty.HARD: -0.2,
            CAPTCHADifficulty.VERY_HARD: -0.4
        }
        
        adjustment = difficulty_adjustments.get(detection.difficulty, 0.0)
        
        return max(0.1, min(0.95, base_prob + adjustment))
    
    def _get_recommended_providers(self, detection: CAPTCHADetection) -> List[str]:
        """Get recommended solving providers for the CAPTCHA."""
        provider_mapping = {
            CAPTCHAType.TEXT_BASED: ["2captcha", "anticaptcha", "capmonster"],
            CAPTCHAType.MATH_EQUATION: ["2captcha", "anticaptcha"],
            CAPTCHAType.RECAPTCHA_V2: ["2captcha", "anticaptcha", "capmonster"],
            CAPTCHAType.RECAPTCHA_V3: ["2captcha", "anticaptcha"],
            CAPTCHAType.HCAPTCHA: ["2captcha", "anticaptcha"],
            CAPTCHAType.IMAGE_BASED: ["2captcha", "anticaptcha"]
        }
        
        return provider_mapping.get(detection.captcha_type, ["2captcha", "anticaptcha"])


class CAPTCHAManager:
    """Main CAPTCHA management system."""
    
    def __init__(self):
        """Initialize the CAPTCHA manager."""
        self.detector = CAPTCHADetector()
        self.classifier = CAPTCHAClassifier()
        self.solving_history = []
    
    async def detect_and_classify(self, html_content: str, page_url: str = None) -> List[Dict[str, Any]]:
        """Detect and classify CAPTCHAs in HTML content.
        
        Args:
            html_content: The HTML content to analyze
            page_url: Optional URL of the page
            
        Returns:
            List of classified CAPTCHAs
        """
        # Detect CAPTCHAs
        detections = await self.detector.detect_captcha(html_content, page_url)
        
        # Classify each detection
        classified_captchas = []
        for detection in detections:
            classification = await self.classifier.classify_captcha(detection)
            classified_captchas.append({
                'detection': detection,
                'classification': classification
            })
        
        return classified_captchas
    
    async def get_captcha_statistics(self) -> Dict[str, Any]:
        """Get statistics about detected CAPTCHAs."""
        if not self.solving_history:
            return {
                'total_detected': 0,
                'by_type': {},
                'by_difficulty': {},
                'average_solving_time': 0.0,
                'success_rate': 0.0
            }
        
        # Calculate statistics
        total_detected = len(self.solving_history)
        
        by_type = {}
        by_difficulty = {}
        solving_times = []
        successful_solves = 0
        
        for record in self.solving_history:
            captcha_type = record.get('type', 'unknown')
            difficulty = record.get('difficulty', 'unknown')
            solving_time = record.get('solving_time', 0)
            success = record.get('success', False)
            
            by_type[captcha_type] = by_type.get(captcha_type, 0) + 1
            by_difficulty[difficulty] = by_difficulty.get(difficulty, 0) + 1
            
            if solving_time > 0:
                solving_times.append(solving_time)
            
            if success:
                successful_solves += 1
        
        return {
            'total_detected': total_detected,
            'by_type': by_type,
            'by_difficulty': by_difficulty,
            'average_solving_time': sum(solving_times) / len(solving_times) if solving_times else 0.0,
            'success_rate': successful_solves / total_detected if total_detected > 0 else 0.0
        }
    
    def record_solving_attempt(self, captcha_type: str, difficulty: str, 
                              solving_time: float, success: bool, provider: str = None):
        """Record a CAPTCHA solving attempt."""
        self.solving_history.append({
            'type': captcha_type,
            'difficulty': difficulty,
            'solving_time': solving_time,
            'success': success,
            'provider': provider,
            'timestamp': time.time()
        })
        
        # Keep only last 1000 records
        if len(self.solving_history) > 1000:
            self.solving_history = self.solving_history[-1000:]
