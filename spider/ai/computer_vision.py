"""
Computer Vision Processor

Advanced computer vision capabilities for image processing,
OCR, object detection, and image classification.

Author: SPIDER Development Team
Version: 1.0.0
"""

import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio
from pathlib import Path

import numpy as np
import pandas as pd

# Set up logger
logger = logging.getLogger(__name__)

# Optional imports for computer vision
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    logger.warning("OpenCV not available. Some features will be limited.")

try:
    from PIL import Image, ImageEnhance, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("PIL not available. Some features will be limited.")

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logger.warning("Tesseract not available. OCR features will be limited.")

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    logger.warning("EasyOCR not available. Some OCR features will be limited.")

try:
    from transformers import pipeline
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers not available. Some advanced features will be limited.")

logger = logging.getLogger(__name__)


class ImageFormat(str, Enum):
    """Image format enumeration."""
    JPEG = "jpeg"
    PNG = "png"
    BMP = "bmp"
    TIFF = "tiff"
    WEBP = "webp"


class ObjectType(str, Enum):
    """Object type enumeration."""
    PERSON = "person"
    VEHICLE = "vehicle"
    ANIMAL = "animal"
    BUILDING = "building"
    FOOD = "food"
    FURNITURE = "furniture"
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    SPORTS = "sports"
    NATURE = "nature"


@dataclass
class ImageInfo:
    """Image information container."""
    width: int
    height: int
    channels: int
    format: ImageFormat
    file_size: int
    has_transparency: bool
    color_space: str
    dpi: Tuple[int, int]


@dataclass
class OCRResult:
    """OCR result container."""
    text: str
    confidence: float
    bounding_boxes: List[Tuple[int, int, int, int]]
    words: List[Dict[str, Any]]
    language: str


@dataclass
class ObjectDetectionResult:
    """Object detection result container."""
    class_name: str
    confidence: float
    bounding_box: Tuple[int, int, int, int]  # x, y, width, height
    object_type: ObjectType


@dataclass
class ImageClassificationResult:
    """Image classification result container."""
    predicted_class: str
    confidence: float
    class_probabilities: Dict[str, float]


class ImageProcessor:
    """Advanced image processing utilities."""
    
    def __init__(self):
        """Initialize image processor."""
        self.supported_formats = [fmt.value for fmt in ImageFormat]
    
    def load_image(self, image_path: Union[str, Path]) -> Optional[np.ndarray]:
        """
        Load image from file.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Image as numpy array or None
        """
        if not OPENCV_AVAILABLE:
            logger.error("OpenCV not available for image loading")
            return None
        
        try:
            image = cv2.imread(str(image_path))
            if image is None:
                logger.error(f"Could not load image: {image_path}")
                return None
            return image
        except Exception as e:
            logger.error(f"Error loading image {image_path}: {e}")
            return None
    
    def save_image(self, image: np.ndarray, output_path: Union[str, Path], 
                   format: ImageFormat = ImageFormat.JPEG) -> bool:
        """
        Save image to file.
        
        Args:
            image: Image as numpy array
            output_path: Output file path
            format: Image format
            
        Returns:
            True if successful
        """
        if not OPENCV_AVAILABLE:
            logger.error("OpenCV not available for image saving")
            return False
        
        try:
            success = cv2.imwrite(str(output_path), image)
            if not success:
                logger.error(f"Could not save image: {output_path}")
            return success
        except Exception as e:
            logger.error(f"Error saving image {output_path}: {e}")
            return False
    
    def get_image_info(self, image: np.ndarray) -> ImageInfo:
        """
        Get image information.
        
        Args:
            image: Image as numpy array
            
        Returns:
            Image information
        """
        height, width = image.shape[:2]
        channels = image.shape[2] if len(image.shape) > 2 else 1
        
        return ImageInfo(
            width=width,
            height=height,
            channels=channels,
            format=ImageFormat.JPEG,  # Default
            file_size=0,  # Would need file path for this
            has_transparency=channels == 4,
            color_space="BGR" if channels == 3 else "GRAY",
            dpi=(72, 72)  # Default
        )
    
    def resize_image(self, image: np.ndarray, width: int, height: int, 
                    maintain_aspect_ratio: bool = True) -> np.ndarray:
        """
        Resize image.
        
        Args:
            image: Input image
            width: Target width
            height: Target height
            maintain_aspect_ratio: Whether to maintain aspect ratio
            
        Returns:
            Resized image
        """
        if not OPENCV_AVAILABLE:
            return image
        
        if maintain_aspect_ratio:
            h, w = image.shape[:2]
            aspect_ratio = w / h
            
            if width / height > aspect_ratio:
                new_width = int(height * aspect_ratio)
                new_height = height
            else:
                new_width = width
                new_height = int(width / aspect_ratio)
        else:
            new_width = width
            new_height = height
        
        return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
    
    def enhance_image(self, image: np.ndarray, 
                     brightness: float = 1.0,
                     contrast: float = 1.0,
                     saturation: float = 1.0,
                     sharpness: float = 1.0) -> np.ndarray:
        """
        Enhance image quality.
        
        Args:
            image: Input image
            brightness: Brightness factor
            contrast: Contrast factor
            saturation: Saturation factor
            sharpness: Sharpness factor
            
        Returns:
            Enhanced image
        """
        if not PIL_AVAILABLE:
            return image
        
        try:
            # Convert to PIL Image
            if len(image.shape) == 3:
                pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            else:
                pil_image = Image.fromarray(image)
            
            # Apply enhancements
            if brightness != 1.0:
                enhancer = ImageEnhance.Brightness(pil_image)
                pil_image = enhancer.enhance(brightness)
            
            if contrast != 1.0:
                enhancer = ImageEnhance.Contrast(pil_image)
                pil_image = enhancer.enhance(contrast)
            
            if saturation != 1.0 and len(image.shape) == 3:
                enhancer = ImageEnhance.Color(pil_image)
                pil_image = enhancer.enhance(saturation)
            
            if sharpness != 1.0:
                enhancer = ImageEnhance.Sharpness(pil_image)
                pil_image = enhancer.enhance(sharpness)
            
            # Convert back to numpy array
            if len(image.shape) == 3:
                return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            else:
                return np.array(pil_image)
        except Exception as e:
            logger.error(f"Error enhancing image: {e}")
            return image
    
    def apply_filters(self, image: np.ndarray, 
                     blur: bool = False,
                     edge_detection: bool = False,
                     grayscale: bool = False) -> np.ndarray:
        """
        Apply image filters.
        
        Args:
            image: Input image
            blur: Apply blur filter
            edge_detection: Apply edge detection
            grayscale: Convert to grayscale
            
        Returns:
            Filtered image
        """
        if not OPENCV_AVAILABLE:
            return image
        
        result = image.copy()
        
        if grayscale:
            if len(result.shape) == 3:
                result = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
        
        if blur:
            result = cv2.GaussianBlur(result, (15, 15), 0)
        
        if edge_detection:
            if len(result.shape) == 3:
                result = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
            result = cv2.Canny(result, 50, 150)
        
        return result
    
    def extract_features(self, image: np.ndarray, 
                        method: str = "orb") -> List[Any]:
        """
        Extract image features.
        
        Args:
            image: Input image
            method: Feature extraction method ("orb", "sift", "surf")
            
        Returns:
            List of features
        """
        if not OPENCV_AVAILABLE:
            return []
        
        try:
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            if method == "orb":
                detector = cv2.ORB_create()
            elif method == "sift":
                detector = cv2.SIFT_create()
            elif method == "surf":
                detector = cv2.xfeatures2d.SURF_create()
            else:
                detector = cv2.ORB_create()
            
            keypoints, descriptors = detector.detectAndCompute(gray, None)
            return keypoints, descriptors
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return [], None


class OCRProcessor:
    """Optical Character Recognition processor."""
    
    def __init__(self, engine: str = "tesseract"):
        """
        Initialize OCR processor.
        
        Args:
            engine: OCR engine ("tesseract", "easyocr")
        """
        self.engine = engine
        self.tesseract_config = "--oem 3 --psm 6"
        self.easyocr_reader = None
        
        if engine == "easyocr" and EASYOCR_AVAILABLE:
            try:
                self.easyocr_reader = easyocr.Reader(['en'])
            except Exception as e:
                logger.warning(f"Failed to initialize EasyOCR: {e}")
                self.engine = "tesseract"
    
    def extract_text(self, image: np.ndarray, 
                    language: str = "eng",
                    confidence_threshold: float = 0.5) -> OCRResult:
        """
        Extract text from image.
        
        Args:
            image: Input image
            language: Language code
            confidence_threshold: Minimum confidence threshold
            
        Returns:
            OCR result
        """
        if self.engine == "tesseract" and TESSERACT_AVAILABLE:
            return self._tesseract_ocr(image, language, confidence_threshold)
        elif self.engine == "easyocr" and self.easyocr_reader:
            return self._easyocr_ocr(image, confidence_threshold)
        else:
            return OCRResult(
                text="",
                confidence=0.0,
                bounding_boxes=[],
                words=[],
                language=language
            )
    
    def _tesseract_ocr(self, image: np.ndarray, language: str, 
                      confidence_threshold: float) -> OCRResult:
        """Extract text using Tesseract."""
        try:
            # Get detailed data
            data = pytesseract.image_to_data(image, lang=language, output_type=pytesseract.Output.DICT)
            
            # Extract text and confidence
            texts = []
            confidences = []
            bounding_boxes = []
            words = []
            
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                conf = int(data['conf'][i])
                
                if text and conf > confidence_threshold * 100:
                    texts.append(text)
                    confidences.append(conf / 100.0)
                    
                    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                    bounding_boxes.append((x, y, x + w, y + h))
                    words.append({
                        'text': text,
                        'confidence': conf / 100.0,
                        'bounding_box': (x, y, w, h)
                    })
            
            full_text = ' '.join(texts)
            avg_confidence = np.mean(confidences) if confidences else 0.0
            
            return OCRResult(
                text=full_text,
                confidence=avg_confidence,
                bounding_boxes=bounding_boxes,
                words=words,
                language=language
            )
        except Exception as e:
            logger.error(f"Tesseract OCR failed: {e}")
            return OCRResult(
                text="",
                confidence=0.0,
                bounding_boxes=[],
                words=[],
                language=language
            )
    
    def _easyocr_ocr(self, image: np.ndarray, confidence_threshold: float) -> OCRResult:
        """Extract text using EasyOCR."""
        try:
            results = self.easyocr_reader.readtext(image)
            
            texts = []
            confidences = []
            bounding_boxes = []
            words = []
            
            for (bbox, text, conf) in results:
                if conf > confidence_threshold:
                    texts.append(text)
                    confidences.append(conf)
                    
                    # Convert bbox to (x1, y1, x2, y2) format
                    x_coords = [point[0] for point in bbox]
                    y_coords = [point[1] for point in bbox]
                    x1, y1 = min(x_coords), min(y_coords)
                    x2, y2 = max(x_coords), max(y_coords)
                    
                    bounding_boxes.append((int(x1), int(y1), int(x2), int(y2)))
                    words.append({
                        'text': text,
                        'confidence': conf,
                        'bounding_box': (int(x1), int(y1), int(x2-x1), int(y2-y1))
                    })
            
            full_text = ' '.join(texts)
            avg_confidence = np.mean(confidences) if confidences else 0.0
            
            return OCRResult(
                text=full_text,
                confidence=avg_confidence,
                bounding_boxes=bounding_boxes,
                words=words,
                language="en"
            )
        except Exception as e:
            logger.error(f"EasyOCR failed: {e}")
            return OCRResult(
                text="",
                confidence=0.0,
                bounding_boxes=[],
                words=[],
                language="en"
            )


class ObjectDetector:
    """Object detection using various methods."""
    
    def __init__(self, model_type: str = "yolo"):
        """
        Initialize object detector.
        
        Args:
            model_type: Detection model type ("yolo", "opencv", "transformers")
        """
        self.model_type = model_type
        self.model = None
        self.class_names = []
        
        if model_type == "yolo" and OPENCV_AVAILABLE:
            self._load_yolo_model()
        elif model_type == "transformers" and TRANSFORMERS_AVAILABLE:
            self._load_transformer_model()
    
    def _load_yolo_model(self):
        """Load YOLO model."""
        try:
            # This would load a pre-trained YOLO model
            # For now, we'll use a placeholder
            self.class_names = [
                "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck",
                "boat", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench",
                "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe"
            ]
        except Exception as e:
            logger.warning(f"Failed to load YOLO model: {e}")
    
    def _load_transformer_model(self):
        """Load transformer-based object detection model."""
        try:
            self.model = pipeline("object-detection", model="facebook/detr-resnet-50")
        except Exception as e:
            logger.warning(f"Failed to load transformer model: {e}")
    
    def detect_objects(self, image: np.ndarray, 
                      confidence_threshold: float = 0.5) -> List[ObjectDetectionResult]:
        """
        Detect objects in image.
        
        Args:
            image: Input image
            confidence_threshold: Minimum confidence threshold
            
        Returns:
            List of detected objects
        """
        if self.model_type == "yolo":
            return self._yolo_detection(image, confidence_threshold)
        elif self.model_type == "transformers" and self.model:
            return self._transformer_detection(image, confidence_threshold)
        else:
            return []
    
    def _yolo_detection(self, image: np.ndarray, confidence_threshold: float) -> List[ObjectDetectionResult]:
        """YOLO-based object detection."""
        # Placeholder implementation
        # In a real implementation, this would use a trained YOLO model
        return []
    
    def _transformer_detection(self, image: np.ndarray, confidence_threshold: float) -> List[ObjectDetectionResult]:
        """Transformer-based object detection."""
        try:
            # Convert BGR to RGB for transformers
            if len(image.shape) == 3:
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                image_rgb = image
            
            # Convert to PIL Image
            pil_image = Image.fromarray(image_rgb)
            
            # Run detection
            results = self.model(pil_image)
            
            detections = []
            for result in results:
                if result['score'] > confidence_threshold:
                    # Convert bounding box format
                    bbox = result['box']
                    x, y, w, h = bbox['xmin'], bbox['ymin'], bbox['xmax'] - bbox['xmin'], bbox['ymax'] - bbox['ymin']
                    
                    # Map to object type
                    object_type = ObjectType.PERSON  # Default
                    class_name = result['label'].lower()
                    if 'person' in class_name:
                        object_type = ObjectType.PERSON
                    elif any(vehicle in class_name for vehicle in ['car', 'truck', 'bus', 'motorcycle']):
                        object_type = ObjectType.VEHICLE
                    elif any(animal in class_name for animal in ['dog', 'cat', 'bird', 'horse']):
                        object_type = ObjectType.ANIMAL
                    
                    detections.append(ObjectDetectionResult(
                        class_name=result['label'],
                        confidence=result['score'],
                        bounding_box=(int(x), int(y), int(w), int(h)),
                        object_type=object_type
                    ))
            
            return detections
        except Exception as e:
            logger.error(f"Transformer object detection failed: {e}")
            return []


class ImageClassifier:
    """Image classification using various methods."""
    
    def __init__(self, model_type: str = "transformers"):
        """
        Initialize image classifier.
        
        Args:
            model_type: Classification model type ("transformers", "opencv")
        """
        self.model_type = model_type
        self.model = None
        self.class_names = []
        
        if model_type == "transformers" and TRANSFORMERS_AVAILABLE:
            self._load_transformer_model()
    
    def _load_transformer_model(self):
        """Load transformer-based classification model."""
        try:
            self.model = pipeline("image-classification", model="google/vit-base-patch16-224")
        except Exception as e:
            logger.warning(f"Failed to load transformer model: {e}")
    
    def classify_image(self, image: np.ndarray, 
                      top_k: int = 5) -> ImageClassificationResult:
        """
        Classify image.
        
        Args:
            image: Input image
            top_k: Number of top predictions to return
            
        Returns:
            Classification result
        """
        if self.model_type == "transformers" and self.model:
            return self._transformer_classification(image, top_k)
        else:
            return ImageClassificationResult(
                predicted_class="unknown",
                confidence=0.0,
                class_probabilities={}
            )
    
    def _transformer_classification(self, image: np.ndarray, top_k: int) -> ImageClassificationResult:
        """Transformer-based image classification."""
        try:
            # Convert BGR to RGB for transformers
            if len(image.shape) == 3:
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                image_rgb = image
            
            # Convert to PIL Image
            pil_image = Image.fromarray(image_rgb)
            
            # Run classification
            results = self.model(pil_image, top_k=top_k)
            
            # Extract results
            predicted_class = results[0]['label']
            confidence = results[0]['score']
            class_probabilities = {result['label']: result['score'] for result in results}
            
            return ImageClassificationResult(
                predicted_class=predicted_class,
                confidence=confidence,
                class_probabilities=class_probabilities
            )
        except Exception as e:
            logger.error(f"Transformer image classification failed: {e}")
            return ImageClassificationResult(
                predicted_class="unknown",
                confidence=0.0,
                class_probabilities={}
            )


class ComputerVisionProcessor:
    """Main computer vision processor combining all capabilities."""
    
    def __init__(self):
        """Initialize computer vision processor."""
        self.image_processor = ImageProcessor()
        self.ocr_processor = OCRProcessor()
        self.object_detector = ObjectDetector()
        self.image_classifier = ImageClassifier()
    
    async def process_image(self, image: np.ndarray,
                           ocr: bool = True,
                           object_detection: bool = True,
                           classification: bool = True,
                           enhancement: bool = False) -> Dict[str, Any]:
        """
        Process image with multiple computer vision techniques.
        
        Args:
            image: Input image
            ocr: Whether to perform OCR
            object_detection: Whether to detect objects
            classification: Whether to classify image
            enhancement: Whether to enhance image
            
        Returns:
            Processing results
        """
        results = {
            "image_info": self.image_processor.get_image_info(image),
            "ocr": None,
            "objects": [],
            "classification": None,
            "enhanced_image": None
        }
        
        # Image enhancement
        if enhancement:
            results["enhanced_image"] = self.image_processor.enhance_image(image)
        
        # OCR
        if ocr:
            results["ocr"] = self.ocr_processor.extract_text(image)
        
        # Object detection
        if object_detection:
            results["objects"] = self.object_detector.detect_objects(image)
        
        # Image classification
        if classification:
            results["classification"] = self.image_classifier.classify_image(image)
        
        return results
    
    def get_supported_formats(self) -> List[str]:
        """Get supported image formats."""
        return self.image_processor.supported_formats
    
    def get_available_engines(self) -> Dict[str, List[str]]:
        """Get available processing engines."""
        return {
            "ocr": ["tesseract", "easyocr"],
            "object_detection": ["yolo", "opencv", "transformers"],
            "classification": ["transformers", "opencv"]
        }
