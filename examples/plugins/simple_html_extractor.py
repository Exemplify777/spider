"""
Simple HTML Extractor Plugin Example

This example demonstrates how to create a custom HTML extractor plugin
for the SPIDER framework.
"""

import re
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup

from spider.plugins.extractor import HTMLExtractorPlugin
from spider.plugins.base import PluginMetadata, PluginType


class SimpleHTMLExtractor(HTMLExtractorPlugin):
    """Simple HTML extractor that extracts basic content from HTML."""
    
    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            name="SimpleHTMLExtractor",
            version="1.0.0",
            description="Simple HTML extractor for basic content extraction",
            author="SPIDER Framework",
            plugin_type=PluginType.EXTRACTOR,
            tags=["html", "extractor", "simple", "example"],
            config_schema=self._get_config_schema()
        )
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate plugin configuration."""
        try:
            return self._validate_extractor_config(config)
        except Exception:
            return False
    
    async def extract(self, data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Extract content from HTML data.
        
        Args:
            data: HTML content to extract from
            context: Additional context for extraction
            
        Returns:
            Extracted content as dictionary
        """
        if not isinstance(data, str):
            return {"error": "Input data must be a string"}
        
        try:
            soup = BeautifulSoup(data, 'html.parser')
            
            # Extract basic content
            result = {
                "title": self._extract_title(soup),
                "headings": self._extract_headings(soup),
                "paragraphs": self._extract_paragraphs(soup),
                "links": self._extract_links(soup),
                "images": self._extract_images(soup),
                "meta": self._extract_meta(soup),
                "text_content": self._extract_text_content(soup)
            }
            
            # Apply filters if configured
            if self.config.get("apply_filters", True):
                result = self._apply_filters(result)
            
            return result
            
        except Exception as e:
            return {"error": f"Failed to extract content: {str(e)}"}
    
    def get_supported_formats(self) -> List[str]:
        """Get supported HTML formats."""
        return ["html", "xhtml", "xml"]
    
    def get_extraction_fields(self) -> List[str]:
        """Get list of fields that can be extracted."""
        return [
            "title", "headings", "paragraphs", "links", 
            "images", "meta", "text_content"
        ]
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract page title."""
        title_tag = soup.find('title')
        return title_tag.get_text().strip() if title_tag else None
    
    def _extract_headings(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract all headings."""
        headings = []
        for level in range(1, 7):
            for heading in soup.find_all(f'h{level}'):
                headings.append({
                    "level": level,
                    "text": heading.get_text().strip(),
                    "id": heading.get('id', ''),
                    "class": heading.get('class', [])
                })
        return headings
    
    def _extract_paragraphs(self, soup: BeautifulSoup) -> List[str]:
        """Extract all paragraphs."""
        paragraphs = []
        for p in soup.find_all('p'):
            text = p.get_text().strip()
            if text:
                paragraphs.append(text)
        return paragraphs
    
    def _extract_links(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract all links."""
        links = []
        for link in soup.find_all('a', href=True):
            links.append({
                "text": link.get_text().strip(),
                "href": link['href'],
                "title": link.get('title', ''),
                "target": link.get('target', '')
            })
        return links
    
    def _extract_images(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract all images."""
        images = []
        for img in soup.find_all('img'):
            images.append({
                "src": img.get('src', ''),
                "alt": img.get('alt', ''),
                "title": img.get('title', ''),
                "width": img.get('width', ''),
                "height": img.get('height', '')
            })
        return images
    
    def _extract_meta(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract meta tags."""
        meta = {}
        for meta_tag in soup.find_all('meta'):
            name = meta_tag.get('name') or meta_tag.get('property')
            content = meta_tag.get('content')
            if name and content:
                meta[name] = content
        return meta
    
    def _extract_text_content(self, soup: BeautifulSoup) -> str:
        """Extract all text content."""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def _apply_filters(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Apply configured filters to the result."""
        filters = self.config.get("filters", {})
        
        # Filter out empty content
        if filters.get("remove_empty", True):
            result["paragraphs"] = [p for p in result["paragraphs"] if p]
            result["links"] = [l for l in result["links"] if l["text"]]
            result["images"] = [i for i in result["images"] if i["src"]]
        
        # Limit content length
        max_length = filters.get("max_text_length")
        if max_length and len(result["text_content"]) > max_length:
            result["text_content"] = result["text_content"][:max_length] + "..."
        
        # Filter links by domain
        allowed_domains = filters.get("allowed_domains", [])
        if allowed_domains:
            filtered_links = []
            for link in result["links"]:
                href = link["href"]
                if any(domain in href for domain in allowed_domains):
                    filtered_links.append(link)
            result["links"] = filtered_links
        
        return result
    
    def _get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema for this extractor."""
        schema = super()._get_config_schema()
        schema["properties"].update({
            "apply_filters": {"type": "boolean", "default": True},
            "filters": {
                "type": "object",
                "properties": {
                    "remove_empty": {"type": "boolean", "default": True},
                    "max_text_length": {"type": "integer"},
                    "allowed_domains": {"type": "array", "items": {"type": "string"}}
                }
            }
        })
        return schema


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Create plugin instance
        config = {
            "enabled": True,
            "apply_filters": True,
            "filters": {
                "remove_empty": True,
                "max_text_length": 1000,
                "allowed_domains": ["example.com", "test.com"]
            }
        }
        
        extractor = SimpleHTMLExtractor(config)
        
        # Initialize plugin
        await extractor.initialize()
        
        # Sample HTML content
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Page</title>
            <meta name="description" content="A test page">
        </head>
        <body>
            <h1>Welcome to Test Page</h1>
            <p>This is a test paragraph.</p>
            <p>Another paragraph with <a href="https://example.com">a link</a>.</p>
            <img src="test.jpg" alt="Test image">
        </body>
        </html>
        """
        
        # Extract content
        result = await extractor.extract(html_content)
        
        print("Extraction Result:")
        print(f"Title: {result.get('title')}")
        print(f"Headings: {len(result.get('headings', []))}")
        print(f"Paragraphs: {len(result.get('paragraphs', []))}")
        print(f"Links: {len(result.get('links', []))}")
        print(f"Images: {len(result.get('images', []))}")
        
        # Cleanup
        await extractor.cleanup()
    
    asyncio.run(main())
