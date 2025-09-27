"""Data extractors for SPIDER framework."""

import json
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from xml.etree import ElementTree

from bs4 import BeautifulSoup

try:
    from pyquery import PyQuery
except ImportError:
    PyQuery = None

from ..core.exceptions import ValidationError
from ..core.logger import get_logger


class BaseExtractor(ABC):
    """Base class for all data extractors."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize extractor with configuration.
        
        Args:
            config: Extractor-specific configuration
        """
        self.config = config or {}
        self.logger = get_logger(self.__class__.__name__)
    
    @abstractmethod
    def extract(self, content: str, **kwargs) -> Dict[str, Any]:
        """Extract data from content.
        
        Args:
            content: Content to extract data from
            **kwargs: Additional extraction parameters
            
        Returns:
            Extracted data dictionary
        """
        pass
    
    def validate_content(self, content: str) -> bool:
        """Validate content before extraction.
        
        Args:
            content: Content to validate
            
        Returns:
            True if content is valid
        """
        if not content or not isinstance(content, str):
            return False
        return True


class HTMLExtractor(BaseExtractor):
    """HTML content extractor using BeautifulSoup and PyQuery."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize HTML extractor.
        
        Args:
            config: Configuration with selectors and extraction rules
        """
        super().__init__(config)
        self.selectors = self.config.get('selectors', {})
        self.parser = self.config.get('parser', 'html.parser')
    
    def extract(self, content: str, **kwargs) -> Dict[str, Any]:
        """Extract data from HTML content.
        
        Args:
            content: HTML content
            **kwargs: Additional parameters
            
        Returns:
            Extracted data dictionary
        """
        if not self.validate_content(content):
            raise ValidationError("Invalid HTML content")
        
        try:
            soup = BeautifulSoup(content, self.parser)
            pq = PyQuery(content)
            
            extracted_data = {}
            
            # Extract using CSS selectors
            for field, selector in self.selectors.items():
                if isinstance(selector, str):
                    # Simple CSS selector
                    elements = pq(selector)
                    if elements:
                        if len(elements) == 1:
                            extracted_data[field] = elements.text().strip()
                        else:
                            extracted_data[field] = [elem.text.strip() for elem in elements]
                elif isinstance(selector, dict):
                    # Complex selector with options
                    selector_config = selector
                    css_selector = selector_config.get('selector')
                    attribute = selector_config.get('attribute', 'text')
                    multiple = selector_config.get('multiple', False)
                    
                    elements = pq(css_selector)
                    if elements:
                        if multiple:
                            if attribute == 'text':
                                extracted_data[field] = [elem.text.strip() for elem in elements]
                            else:
                                extracted_data[field] = [elem.attr(attribute) for elem in elements]
                        else:
                            if attribute == 'text':
                                extracted_data[field] = elements.text().strip()
                            else:
                                extracted_data[field] = elements.attr(attribute)
            
            # Extract metadata
            extracted_data['_metadata'] = {
                'title': self._extract_title(soup),
                'meta_description': self._extract_meta_description(soup),
                'links': self._extract_links(soup),
                'images': self._extract_images(soup),
                'text_length': len(content),
                'extraction_timestamp': self._get_timestamp()
            }
            
            return extracted_data
            
        except Exception as e:
            self.logger.error(f"HTML extraction failed: {e}")
            raise ValidationError(f"HTML extraction failed: {e}")
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title."""
        title_tag = soup.find('title')
        return title_tag.text.strip() if title_tag else ""
    
    def _extract_meta_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description."""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        return meta_desc.get('content', '') if meta_desc else ""
    
    def _extract_links(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract all links."""
        links = []
        for link in soup.find_all('a', href=True):
            links.append({
                'url': link['href'],
                'text': link.text.strip(),
                'title': link.get('title', '')
            })
        return links
    
    def _extract_images(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract all images."""
        images = []
        for img in soup.find_all('img', src=True):
            images.append({
                'src': img['src'],
                'alt': img.get('alt', ''),
                'title': img.get('title', '')
            })
        return images
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.utcnow().isoformat()


class JSONExtractor(BaseExtractor):
    """JSON content extractor."""
    
    def extract(self, content: str, **kwargs) -> Dict[str, Any]:
        """Extract data from JSON content.
        
        Args:
            content: JSON content
            **kwargs: Additional parameters
            
        Returns:
            Extracted data dictionary
        """
        if not self.validate_content(content):
            raise ValidationError("Invalid JSON content")
        
        try:
            data = json.loads(content)
            
            # Apply field mapping if configured
            field_mapping = self.config.get('field_mapping', {})
            if field_mapping:
                data = self._apply_field_mapping(data, field_mapping)
            
            # Apply filters if configured
            filters = self.config.get('filters', {})
            if filters:
                data = self._apply_filters(data, filters)
            
            # Add metadata
            data['_metadata'] = {
                'extraction_timestamp': self._get_timestamp(),
                'content_length': len(content),
                'data_type': 'json'
            }
            
            return data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parsing failed: {e}")
            raise ValidationError(f"Invalid JSON format: {e}")
        except Exception as e:
            self.logger.error(f"JSON extraction failed: {e}")
            raise ValidationError(f"JSON extraction failed: {e}")
    
    def _apply_field_mapping(self, data: Dict[str, Any], mapping: Dict[str, str]) -> Dict[str, Any]:
        """Apply field mapping to data."""
        mapped_data = {}
        for new_field, old_field in mapping.items():
            if old_field in data:
                mapped_data[new_field] = data[old_field]
        return mapped_data
    
    def _apply_filters(self, data: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        """Apply filters to data."""
        filtered_data = data.copy()
        
        for field, filter_config in filters.items():
            if field in filtered_data:
                if 'exclude' in filter_config:
                    if filtered_data[field] in filter_config['exclude']:
                        del filtered_data[field]
                elif 'include' in filter_config:
                    if filtered_data[field] not in filter_config['include']:
                        del filtered_data[field]
        
        return filtered_data
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.utcnow().isoformat()


class XMLExtractor(BaseExtractor):
    """XML content extractor."""
    
    def extract(self, content: str, **kwargs) -> Dict[str, Any]:
        """Extract data from XML content.
        
        Args:
            content: XML content
            **kwargs: Additional parameters
            
        Returns:
            Extracted data dictionary
        """
        if not self.validate_content(content):
            raise ValidationError("Invalid XML content")
        
        try:
            root = ElementTree.fromstring(content)
            
            # Extract data using XPath expressions
            xpath_selectors = self.config.get('xpath_selectors', {})
            extracted_data = {}
            
            for field, xpath in xpath_selectors.items():
                elements = root.findall(xpath)
                if elements:
                    if len(elements) == 1:
                        extracted_data[field] = elements[0].text
                    else:
                        extracted_data[field] = [elem.text for elem in elements]
            
            # Add metadata
            extracted_data['_metadata'] = {
                'root_tag': root.tag,
                'extraction_timestamp': self._get_timestamp(),
                'content_length': len(content),
                'data_type': 'xml'
            }
            
            return extracted_data
            
        except ElementTree.ParseError as e:
            self.logger.error(f"XML parsing failed: {e}")
            raise ValidationError(f"Invalid XML format: {e}")
        except Exception as e:
            self.logger.error(f"XML extraction failed: {e}")
            raise ValidationError(f"XML extraction failed: {e}")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.utcnow().isoformat()


class RegexExtractor(BaseExtractor):
    """Regex-based content extractor."""
    
    def extract(self, content: str, **kwargs) -> Dict[str, Any]:
        """Extract data using regex patterns.
        
        Args:
            content: Content to extract from
            **kwargs: Additional parameters
            
        Returns:
            Extracted data dictionary
        """
        if not self.validate_content(content):
            raise ValidationError("Invalid content")
        
        try:
            patterns = self.config.get('patterns', {})
            extracted_data = {}
            
            for field, pattern_config in patterns.items():
                if isinstance(pattern_config, str):
                    # Simple regex pattern
                    pattern = pattern_config
                    flags = 0
                else:
                    # Complex pattern with flags
                    pattern = pattern_config['pattern']
                    flags = pattern_config.get('flags', 0)
                
                matches = re.findall(pattern, content, flags)
                
                if matches:
                    if len(matches) == 1:
                        extracted_data[field] = matches[0]
                    else:
                        extracted_data[field] = matches
            
            # Add metadata
            extracted_data['_metadata'] = {
                'extraction_timestamp': self._get_timestamp(),
                'content_length': len(content),
                'data_type': 'regex'
            }
            
            return extracted_data
            
        except re.error as e:
            self.logger.error(f"Regex compilation failed: {e}")
            raise ValidationError(f"Invalid regex pattern: {e}")
        except Exception as e:
            self.logger.error(f"Regex extraction failed: {e}")
            raise ValidationError(f"Regex extraction failed: {e}")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.utcnow().isoformat()
