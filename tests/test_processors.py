"""Tests for SPIDER processors."""

import pytest
import json
from unittest.mock import Mock, patch

from spider.processors.extractors import HTMLExtractor, JSONExtractor, XMLExtractor, RegexExtractor
from spider.processors.transformers import DataCleaner, DataNormalizer, DataEnricher
from spider.processors.storage import FileStorage, DatabaseStorage
from spider.core.exceptions import ValidationError, StorageError


class TestHTMLExtractor:
    """Test HTML extractor."""
    
    def test_html_extractor_creation(self):
        """Test HTML extractor creation."""
        config = {
            'selectors': {
                'title': 'title',
                'links': {
                    'selector': 'a[href]',
                    'multiple': True
                }
            }
        }
        extractor = HTMLExtractor(config)
        
        assert extractor.config == config
        assert extractor.selectors == config['selectors']
        assert extractor.parser == 'html.parser'
    
    def test_html_extraction(self):
        """Test HTML data extraction."""
        html_content = """
        <html>
            <head>
                <title>Test Page</title>
                <meta name="description" content="Test description">
            </head>
            <body>
                <h1>Main Title</h1>
                <a href="/link1">Link 1</a>
                <a href="/link2">Link 2</a>
                <img src="/image1.jpg" alt="Image 1">
            </body>
        </html>
        """
        
        config = {
            'selectors': {
                'title': 'title',
                'meta_description': {
                    'selector': 'meta[name="description"]',
                    'attribute': 'content'
                },
                'links': {
                    'selector': 'a[href]',
                    'multiple': True
                },
                'images': {
                    'selector': 'img[src]',
                    'multiple': True
                }
            }
        }
        
        extractor = HTMLExtractor(config)
        result = extractor.extract(html_content)
        
        assert result['title'] == 'Test Page'
        assert result['meta_description'] == 'Test description'
        assert len(result['links']) == 2
        assert '/link1' in result['links']
        assert '/link2' in result['links']
        assert len(result['images']) == 1
        assert result['images'][0]['src'] == '/image1.jpg'
        assert '_metadata' in result
    
    def test_invalid_content(self):
        """Test extraction with invalid content."""
        extractor = HTMLExtractor()
        
        with pytest.raises(ValidationError):
            extractor.extract("")
        
        with pytest.raises(ValidationError):
            extractor.extract(None)


class TestJSONExtractor:
    """Test JSON extractor."""
    
    def test_json_extraction(self):
        """Test JSON data extraction."""
        json_content = json.dumps({
            "id": 1,
            "name": "Test Item",
            "description": "Test description",
            "status": "active",
            "price": 19.99
        })
        
        config = {
            'field_mapping': {
                'item_id': 'id',
                'item_name': 'name',
                'item_description': 'description'
            },
            'filters': {
                'status': {
                    'include': ['active', 'published']
                }
            }
        }
        
        extractor = JSONExtractor(config)
        result = extractor.extract(json_content)
        
        assert result['item_id'] == 1
        assert result['item_name'] == 'Test Item'
        assert result['item_description'] == 'Test description'
        assert result['status'] == 'active'
        assert result['price'] == 19.99
        assert '_metadata' in result
    
    def test_invalid_json(self):
        """Test extraction with invalid JSON."""
        extractor = JSONExtractor()
        
        with pytest.raises(ValidationError):
            extractor.extract("invalid json")
    
    def test_field_filtering(self):
        """Test field filtering."""
        json_content = json.dumps({
            "id": 1,
            "name": "Test Item",
            "status": "inactive"
        })
        
        config = {
            'filters': {
                'status': {
                    'exclude': ['inactive']
                }
            }
        }
        
        extractor = JSONExtractor(config)
        result = extractor.extract(json_content)
        
        # Status should be filtered out
        assert 'status' not in result
        assert result['id'] == 1
        assert result['name'] == 'Test Item'


class TestDataCleaner:
    """Test data cleaner transformer."""
    
    def test_string_cleaning(self):
        """Test string cleaning."""
        cleaner = DataCleaner()
        
        # Test basic cleaning
        dirty_text = "  Hello   World  \n\t  "
        clean_text = cleaner._clean_string(dirty_text)
        assert clean_text == "Hello World"
        
        # Test HTML entity decoding
        html_text = "Hello &amp; World &lt;tag&gt;"
        clean_text = cleaner._clean_string(html_text)
        assert clean_text == "Hello & World <tag>"
    
    def test_data_cleaning(self):
        """Test data cleaning."""
        cleaner = DataCleaner()
        
        dirty_data = {
            'title': '  Test Title  ',
            'description': 'Test &amp; Description',
            'tags': ['  tag1  ', '  tag2  '],
            'metadata': {
                'created': '2023-01-01',
                'updated': ' 2023-01-02  '
            },
            '_preserve': 'This should be preserved'
        }
        
        clean_data = cleaner.transform(dirty_data)
        
        assert clean_data['title'] == 'Test Title'
        assert clean_data['description'] == 'Test & Description'
        assert clean_data['tags'] == ['tag1', 'tag2']
        assert clean_data['metadata']['created'] == '2023-01-01'
        assert clean_data['metadata']['updated'] == '2023-01-02'
        assert clean_data['_preserve'] == 'This should be preserved'


class TestDataNormalizer:
    """Test data normalizer transformer."""
    
    def test_key_normalization(self):
        """Test key normalization."""
        normalizer = DataNormalizer()
        
        # Test key normalization
        assert normalizer._normalize_key('Title Case') == 'title_case'
        assert normalizer._normalize_key('UPPER_CASE') == 'upper_case'
        assert normalizer._normalize_key('mixed-Case123') == 'mixed_case123'
        assert normalizer._normalize_key('  spaced  ') == 'spaced'
        assert normalizer._normalize_key('special@#$chars') == 'special_chars'
    
    def test_value_normalization(self):
        """Test value normalization."""
        normalizer = DataNormalizer()
        
        # Test string normalization
        assert normalizer._normalize_string('  Hello World  ') == 'hello world'
        assert normalizer._normalize_string('UPPER CASE') == 'upper case'
        
        # Test number normalization
        assert normalizer._normalize_number(3.14159) == 3.14159
        assert normalizer._normalize_number(42) == 42
    
    def test_data_normalization(self):
        """Test data normalization."""
        config = {'decimal_places': 2}
        normalizer = DataNormalizer(config)
        
        data = {
            'Title': 'Test Title',
            'Price': 19.999,
            'Tags': ['Tag1', 'Tag2'],
            'Metadata': {
                'Created': '2023-01-01',
                'Status': 'ACTIVE'
            },
            '_preserve': 'This should be preserved'
        }
        
        normalized_data = normalizer.transform(data)
        
        assert normalized_data['title'] == 'test title'
        assert normalized_data['price'] == 20.0  # Rounded to 2 decimal places
        assert normalized_data['tags'] == ['tag1', 'tag2']
        assert normalized_data['metadata']['created'] == '2023-01-01'
        assert normalized_data['metadata']['status'] == 'active'
        assert normalized_data['_preserve'] == 'This should be preserved'


class TestDataEnricher:
    """Test data enricher transformer."""
    
    def test_data_enrichment(self):
        """Test data enrichment."""
        config = {
            'enrichment_rules': {
                'full_name': {
                    'type': 'concat',
                    'fields': ['first_name', 'last_name'],
                    'separator': ' '
                },
                'display_price': {
                    'type': 'format',
                    'template': '${price:.2f} USD'
                },
                'status_display': {
                    'type': 'lookup',
                    'field': 'status',
                    'mapping': {
                        'active': 'Active',
                        'inactive': 'Inactive'
                    }
                }
            }
        }
        
        enricher = DataEnricher(config)
        
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'price': 19.99,
            'status': 'active'
        }
        
        enriched_data = enricher.transform(data)
        
        assert enriched_data['full_name'] == 'John Doe'
        assert enriched_data['display_price'] == '19.99 USD'
        assert enriched_data['status_display'] == 'Active'
        assert '_enriched_at' in enriched_data
        assert '_quality_metrics' in enriched_data
    
    def test_quality_metrics(self):
        """Test quality metrics calculation."""
        enricher = DataEnricher()
        
        data = {
            'field1': 'value1',
            'field2': 'value2',
            'field3': '',  # Empty field
            'field4': None  # None field
        }
        
        enriched_data = enricher.transform(data)
        metrics = enriched_data['_quality_metrics']
        
        assert metrics['total_fields'] == 4
        assert metrics['empty_fields'] == 2
        assert metrics['completeness_ratio'] == 0.5


class TestFileStorage:
    """Test file storage."""
    
    def test_file_storage_creation(self):
        """Test file storage creation."""
        config = {
            'data_dir': 'test_data',
            'format': 'json',
            'encoding': 'utf-8'
        }
        
        storage = FileStorage(config)
        
        assert storage.data_dir == Path('test_data')
        assert storage.format == 'json'
        assert storage.encoding == 'utf-8'
    
    @pytest.mark.asyncio
    async def test_save_and_load_json(self):
        """Test saving and loading JSON data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                'data_dir': temp_dir,
                'format': 'json'
            }
            
            storage = FileStorage(config)
            
            test_data = [
                {'id': 1, 'name': 'Test 1'},
                {'id': 2, 'name': 'Test 2'}
            ]
            
            # Save data
            await storage.save(test_data, 'test.json')
            
            # Check if file exists
            assert await storage.exists('test.json')
            
            # Load data
            loaded_data = await storage.load('test.json')
            
            assert loaded_data == test_data
    
    @pytest.mark.asyncio
    async def test_save_and_load_csv(self):
        """Test saving and loading CSV data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                'data_dir': temp_dir,
                'format': 'csv'
            }
            
            storage = FileStorage(config)
            
            test_data = [
                {'id': 1, 'name': 'Test 1', 'value': 10.5},
                {'id': 2, 'name': 'Test 2', 'value': 20.0}
            ]
            
            # Save data
            await storage.save(test_data, 'test.csv')
            
            # Load data
            loaded_data = await storage.load('test.csv')
            
            # CSV loads as strings, so we need to convert
            assert len(loaded_data) == 2
            assert loaded_data[0]['id'] == '1'
            assert loaded_data[0]['name'] == 'Test 1'
    
    @pytest.mark.asyncio
    async def test_file_not_found(self):
        """Test loading non-existent file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {'data_dir': temp_dir}
            storage = FileStorage(config)
            
            with pytest.raises(StorageError):
                await storage.load('nonexistent.json')


class TestDatabaseStorage:
    """Test database storage."""
    
    @pytest.mark.asyncio
    async def test_database_storage(self):
        """Test database storage operations."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db_path = temp_db.name
        
        try:
            config = {
                'url': f'sqlite:///{db_path}',
                'table_name': 'test_results'
            }
            
            storage = DatabaseStorage(config)
            
            test_data = [
                {
                    'url': 'https://example.com',
                    'status_code': 200,
                    'success': True,
                    'content_length': 1024,
                    'extracted_data': {'title': 'Test'},
                    'error': None
                }
            ]
            
            # Save data
            await storage.save(test_data, 'test_results')
            
            # Check if table exists
            assert await storage.exists('test_results')
            
            # Load data
            loaded_data = await storage.load('test_results')
            
            assert len(loaded_data) == 1
            assert loaded_data[0]['url'] == 'https://example.com'
            assert loaded_data[0]['status_code'] == 200
            assert loaded_data[0]['success'] == 1  # SQLite stores boolean as int
            
        finally:
            os.unlink(db_path)


# Integration tests
class TestProcessorIntegration:
    """Test processor integration."""
    
    def test_extraction_and_transformation_pipeline(self):
        """Test complete extraction and transformation pipeline."""
        # HTML content
        html_content = """
        <html>
            <head><title>  Test Page  </title></head>
            <body>
                <h1>Main Title</h1>
                <p>Description &amp; content</p>
            </body>
        </html>
        """
        
        # Extract data
        extractor = HTMLExtractor({
            'selectors': {
                'title': 'title',
                'description': 'p'
            }
        })
        
        extracted_data = extractor.extract(html_content)
        
        # Clean data
        cleaner = DataCleaner()
        cleaned_data = cleaner.transform(extracted_data)
        
        # Normalize data
        normalizer = DataNormalizer()
        normalized_data = normalizer.transform(cleaned_data)
        
        # Enrich data
        enricher = DataEnricher({
            'enrichment_rules': {
                'display_title': {
                    'type': 'format',
                    'template': 'Title: {title}'
                }
            }
        })
        
        enriched_data = enricher.transform(normalized_data)
        
        # Verify results
        assert enriched_data['title'] == 'test page'
        assert enriched_data['description'] == 'description & content'
        assert enriched_data['display_title'] == 'Title: test page'
        assert '_metadata' in enriched_data
        assert '_enriched_at' in enriched_data
        assert '_quality_metrics' in enriched_data
