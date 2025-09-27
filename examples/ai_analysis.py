#!/usr/bin/env python3
"""
SPIDER Framework - AI Analysis Example

This example demonstrates AI-powered data analysis using the SPIDER framework.
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from spider.core.ai import AIProcessor
from spider.core.config import Config
from spider.core.logger import Logger
from spider.core.storage import Storage

async def main():
    """Main function demonstrating AI analysis."""
    
    # Initialize configuration
    config = Config()
    config.load_from_file('config/spider.yaml')
    
    # Initialize logger
    logger = Logger(config)
    logger.info("Starting AI analysis example")
    
    try:
        # Initialize AI processor
        ai_processor = AIProcessor(config)
        
        # Initialize storage
        storage = Storage(config)
        
        # Sample data for analysis
        sample_data = [
            {
                'text': 'This is a great product! I love it.',
                'category': 'review',
                'timestamp': datetime.now().isoformat()
            },
            {
                'text': 'The service was terrible. Very disappointed.',
                'category': 'review',
                'timestamp': datetime.now().isoformat()
            },
            {
                'text': 'Average quality, nothing special.',
                'category': 'review',
                'timestamp': datetime.now().isoformat()
            },
            {
                'text': 'Excellent customer support and fast delivery.',
                'category': 'review',
                'timestamp': datetime.now().isoformat()
            },
            {
                'text': 'Poor quality, would not recommend.',
                'category': 'review',
                'timestamp': datetime.now().isoformat()
            }
        ]
        
        # Analyze sentiment
        logger.info("Analyzing sentiment...")
        sentiment_results = []
        for item in sample_data:
            sentiment = await ai_processor.analyze_sentiment(item['text'])
            sentiment_results.append({
                'text': item['text'],
                'sentiment': sentiment
            })
            logger.info(f"Text: {item['text'][:50]}...")
            logger.info(f"Sentiment: {sentiment}")
        
        # Analyze entities
        logger.info("\nAnalyzing entities...")
        entity_results = []
        for item in sample_data:
            entities = await ai_processor.extract_entities(item['text'])
            entity_results.append({
                'text': item['text'],
                'entities': entities
            })
            logger.info(f"Text: {item['text'][:50]}...")
            logger.info(f"Entities: {entities}")
        
        # Analyze language
        logger.info("\nAnalyzing language...")
        language_results = []
        for item in sample_data:
            language = await ai_processor.detect_language(item['text'])
            language_results.append({
                'text': item['text'],
                'language': language
            })
            logger.info(f"Text: {item['text'][:50]}...")
            logger.info(f"Language: {language}")
        
        # Analyze topics
        logger.info("\nAnalyzing topics...")
        topic_results = []
        for item in sample_data:
            topics = await ai_processor.extract_topics(item['text'])
            topic_results.append({
                'text': item['text'],
                'topics': topics
            })
            logger.info(f"Text: {item['text'][:50]}...")
            logger.info(f"Topics: {topics}")
        
        # Analyze keywords
        logger.info("\nAnalyzing keywords...")
        keyword_results = []
        for item in sample_data:
            keywords = await ai_processor.extract_keywords(item['text'])
            keyword_results.append({
                'text': item['text'],
                'keywords': keywords
            })
            logger.info(f"Text: {item['text'][:50]}...")
            logger.info(f"Keywords: {keywords}")
        
        # Analyze text classification
        logger.info("\nAnalyzing text classification...")
        classification_results = []
        for item in sample_data:
            classification = await ai_processor.classify_text(item['text'])
            classification_results.append({
                'text': item['text'],
                'classification': classification
            })
            logger.info(f"Text: {item['text'][:50]}...")
            logger.info(f"Classification: {classification}")
        
        # Analyze text summarization
        logger.info("\nAnalyzing text summarization...")
        summarization_results = []
        for item in sample_data:
            summary = await ai_processor.summarize_text(item['text'])
            summarization_results.append({
                'text': item['text'],
                'summary': summary
            })
            logger.info(f"Text: {item['text'][:50]}...")
            logger.info(f"Summary: {summary}")
        
        # Analyze text translation
        logger.info("\nAnalyzing text translation...")
        translation_results = []
        for item in sample_data:
            translation = await ai_processor.translate_text(item['text'], target_language='es')
            translation_results.append({
                'text': item['text'],
                'translation': translation
            })
            logger.info(f"Text: {item['text'][:50]}...")
            logger.info(f"Translation: {translation}")
        
        # Analyze text generation
        logger.info("\nAnalyzing text generation...")
        generation_results = []
        for item in sample_data:
            generated_text = await ai_processor.generate_text(
                prompt=f"Write a response to this review: {item['text']}",
                max_length=100
            )
            generation_results.append({
                'text': item['text'],
                'generated_text': generated_text
            })
            logger.info(f"Text: {item['text'][:50]}...")
            logger.info(f"Generated: {generated_text}")
        
        # Analyze text similarity
        logger.info("\nAnalyzing text similarity...")
        similarity_results = []
        for i, item1 in enumerate(sample_data):
            for j, item2 in enumerate(sample_data[i+1:], i+1):
                similarity = await ai_processor.calculate_similarity(
                    item1['text'], item2['text']
                )
                similarity_results.append({
                    'text1': item1['text'],
                    'text2': item2['text'],
                    'similarity': similarity
                })
                logger.info(f"Text 1: {item1['text'][:30]}...")
                logger.info(f"Text 2: {item2['text'][:30]}...")
                logger.info(f"Similarity: {similarity}")
        
        # Analyze text clustering
        logger.info("\nAnalyzing text clustering...")
        texts = [item['text'] for item in sample_data]
        clusters = await ai_processor.cluster_texts(texts, n_clusters=2)
        cluster_results = []
        for i, (text, cluster) in enumerate(zip(texts, clusters)):
            cluster_results.append({
                'text': text,
                'cluster': cluster
            })
            logger.info(f"Text: {text[:50]}...")
            logger.info(f"Cluster: {cluster}")
        
        # Analyze text anomaly detection
        logger.info("\nAnalyzing text anomaly detection...")
        anomaly_results = []
        for item in sample_data:
            is_anomaly = await ai_processor.detect_anomaly(item['text'])
            anomaly_results.append({
                'text': item['text'],
                'is_anomaly': is_anomaly
            })
            logger.info(f"Text: {item['text'][:50]}...")
            logger.info(f"Is Anomaly: {is_anomaly}")
        
        # Analyze text trend analysis
        logger.info("\nAnalyzing text trend analysis...")
        trend_results = await ai_processor.analyze_trends(sample_data)
        logger.info(f"Trend analysis: {trend_results}")
        
        # Analyze text prediction
        logger.info("\nAnalyzing text prediction...")
        prediction_results = []
        for item in sample_data:
            prediction = await ai_processor.predict_text(item['text'])
            prediction_results.append({
                'text': item['text'],
                'prediction': prediction
            })
            logger.info(f"Text: {item['text'][:50]}...")
            logger.info(f"Prediction: {prediction}")
        
        # Compile all results
        all_results = {
            'sentiment_analysis': sentiment_results,
            'entity_extraction': entity_results,
            'language_detection': language_results,
            'topic_extraction': topic_results,
            'keyword_extraction': keyword_results,
            'text_classification': classification_results,
            'text_summarization': summarization_results,
            'text_translation': translation_results,
            'text_generation': generation_results,
            'text_similarity': similarity_results,
            'text_clustering': cluster_results,
            'anomaly_detection': anomaly_results,
            'trend_analysis': trend_results,
            'text_prediction': prediction_results,
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        # Export results
        export_file = f"ai_analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(export_file, 'w') as f:
            json.dump(all_results, f, indent=2, default=str)
        
        logger.info(f"AI analysis results exported to: {export_file}")
        logger.info("AI analysis example completed successfully")
        
    except Exception as e:
        logger.error(f"Error in AI analysis example: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
