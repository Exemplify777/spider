"""
NLP Processor

Advanced Natural Language Processing capabilities for text analysis,
sentiment analysis, entity recognition, and text classification.

Author: SPIDER Development Team
Version: 1.0.0
"""

import re
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, accuracy_score

# Set up logger
logger = logging.getLogger(__name__)

# Optional imports for advanced NLP
try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize, sent_tokenize
    from nltk.stem import WordNetLemmatizer, PorterStemmer
    from nltk.tag import pos_tag
    from nltk.chunk import ne_chunk
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    logger.warning("NLTK not available. Some advanced features will be limited.")

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning("spaCy not available. Some advanced features will be limited.")

try:
    from transformers import pipeline, AutoTokenizer, AutoModel
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers not available. Some advanced features will be limited.")

logger = logging.getLogger(__name__)


class SentimentType(str, Enum):
    """Sentiment type enumeration."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class EntityType(str, Enum):
    """Entity type enumeration."""
    PERSON = "PERSON"
    ORGANIZATION = "ORG"
    LOCATION = "GPE"
    MONEY = "MONEY"
    PERCENT = "PERCENT"
    DATE = "DATE"
    TIME = "TIME"
    EMAIL = "EMAIL"
    URL = "URL"
    PHONE = "PHONE"


@dataclass
class SentimentResult:
    """Sentiment analysis result."""
    text: str
    sentiment: SentimentType
    confidence: float
    positive_score: float
    negative_score: float
    neutral_score: float


@dataclass
class EntityResult:
    """Entity recognition result."""
    text: str
    entity: str
    entity_type: EntityType
    start_pos: int
    end_pos: int
    confidence: float


@dataclass
class ClassificationResult:
    """Text classification result."""
    text: str
    predicted_class: str
    confidence: float
    class_probabilities: Dict[str, float]


class TextPreprocessor:
    """Advanced text preprocessing utilities."""
    
    def __init__(self, language: str = "english"):
        """
        Initialize text preprocessor.
        
        Args:
            language: Language for processing
        """
        self.language = language
        self.lemmatizer = None
        self.stemmer = None
        self.stop_words = set()
        
        if NLTK_AVAILABLE:
            try:
                self.lemmatizer = WordNetLemmatizer()
                self.stemmer = PorterStemmer()
                self.stop_words = set(stopwords.words(language))
            except LookupError:
                logger.warning(f"NLTK data not found for language: {language}")
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text.
        
        Args:
            text: Input text
            
        Returns:
            Cleaned text
        """
        if not isinstance(text, str):
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove phone numbers
        text = re.sub(r'(\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}', '', text)
        
        # Remove special characters and digits
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into words.
        
        Args:
            text: Input text
            
        Returns:
            List of tokens
        """
        if NLTK_AVAILABLE:
            try:
                return word_tokenize(text)
            except LookupError:
                pass
        
        # Fallback to simple tokenization
        return text.split()
    
    def remove_stopwords(self, tokens: List[str]) -> List[str]:
        """
        Remove stop words from tokens.
        
        Args:
            tokens: List of tokens
            
        Returns:
            Filtered tokens
        """
        if self.stop_words:
            return [token for token in tokens if token not in self.stop_words]
        return tokens
    
    def lemmatize(self, tokens: List[str]) -> List[str]:
        """
        Lemmatize tokens.
        
        Args:
            tokens: List of tokens
            
        Returns:
            Lemmatized tokens
        """
        if self.lemmatizer:
            return [self.lemmatizer.lemmatize(token) for token in tokens]
        return tokens
    
    def stem(self, tokens: List[str]) -> List[str]:
        """
        Stem tokens.
        
        Args:
            tokens: List of tokens
            
        Returns:
            Stemmed tokens
        """
        if self.stemmer:
            return [self.stemmer.stem(token) for token in tokens]
        return tokens
    
    def preprocess(self, text: str, 
                  clean: bool = True,
                  tokenize: bool = True,
                  remove_stopwords: bool = True,
                  lemmatize: bool = True,
                  stem: bool = False) -> Union[str, List[str]]:
        """
        Complete text preprocessing pipeline.
        
        Args:
            text: Input text
            clean: Whether to clean text
            tokenize: Whether to tokenize
            remove_stopwords: Whether to remove stop words
            lemmatize: Whether to lemmatize
            stem: Whether to stem
            
        Returns:
            Processed text or tokens
        """
        if clean:
            text = self.clean_text(text)
        
        if not tokenize:
            return text
        
        tokens = self.tokenize(text)
        
        if remove_stopwords:
            tokens = self.remove_stopwords(tokens)
        
        if lemmatize:
            tokens = self.lemmatize(tokens)
        elif stem:
            tokens = self.stem(tokens)
        
        return tokens


class SentimentAnalyzer:
    """Advanced sentiment analysis using multiple approaches."""
    
    def __init__(self, model_type: str = "hybrid"):
        """
        Initialize sentiment analyzer.
        
        Args:
            model_type: Type of model ("rule_based", "ml", "transformer", "hybrid")
        """
        self.model_type = model_type
        self.preprocessor = TextPreprocessor()
        self.model = None
        self.vectorizer = None
        self.transformer_pipeline = None
        
        # Rule-based sentiment words
        self.positive_words = {
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
            'awesome', 'brilliant', 'outstanding', 'perfect', 'love', 'like',
            'best', 'better', 'superb', 'marvelous', 'delightful', 'pleased'
        }
        
        self.negative_words = {
            'bad', 'terrible', 'awful', 'horrible', 'disgusting', 'hate',
            'worst', 'worse', 'disappointing', 'frustrating', 'annoying',
            'angry', 'sad', 'depressed', 'upset', 'furious', 'disgusted'
        }
        
        # Negation words
        self.negation_words = {
            'not', 'no', 'never', 'none', 'nothing', 'nobody', 'nowhere',
            'neither', 'nor', 'cannot', "can't", "won't", "don't", "doesn't"
        }
    
    def _rule_based_sentiment(self, text: str) -> SentimentResult:
        """Rule-based sentiment analysis."""
        tokens = self.preprocessor.preprocess(text, tokenize=True)
        
        positive_count = 0
        negative_count = 0
        negation_count = 0
        
        for i, token in enumerate(tokens):
            if token in self.positive_words:
                # Check for negation
                if i > 0 and tokens[i-1] in self.negation_words:
                    negative_count += 1
                else:
                    positive_count += 1
            elif token in self.negative_words:
                # Check for negation
                if i > 0 and tokens[i-1] in self.negation_words:
                    positive_count += 1
                else:
                    negative_count += 1
            elif token in self.negation_words:
                negation_count += 1
        
        total_sentiment = positive_count + negative_count
        if total_sentiment == 0:
            sentiment = SentimentType.NEUTRAL
            confidence = 0.5
            positive_score = 0.33
            negative_score = 0.33
            neutral_score = 0.34
        else:
            positive_ratio = positive_count / total_sentiment
            negative_ratio = negative_count / total_sentiment
            
            if positive_ratio > negative_ratio:
                sentiment = SentimentType.POSITIVE
                confidence = positive_ratio
            elif negative_ratio > positive_ratio:
                sentiment = SentimentType.NEGATIVE
                confidence = negative_ratio
            else:
                sentiment = SentimentType.NEUTRAL
                confidence = 0.5
            
            # Normalize scores
            total = positive_count + negative_count + 1  # +1 for neutral
            positive_score = positive_count / total
            negative_score = negative_count / total
            neutral_score = 1 - positive_score - negative_score
        
        return SentimentResult(
            text=text,
            sentiment=sentiment,
            confidence=confidence,
            positive_score=positive_score,
            negative_score=negative_score,
            neutral_score=neutral_score
        )
    
    def _train_ml_model(self, texts: List[str], labels: List[str]):
        """Train ML model for sentiment analysis."""
        # Preprocess texts
        processed_texts = []
        for text in texts:
            tokens = self.preprocessor.preprocess(text, tokenize=True)
            processed_texts.append(' '.join(tokens))
        
        # Create pipeline
        self.vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
        self.model = LogisticRegression(random_state=42)
        
        # Train
        X = self.vectorizer.fit_transform(processed_texts)
        self.model.fit(X, labels)
    
    def _ml_sentiment(self, text: str) -> SentimentResult:
        """ML-based sentiment analysis."""
        if not self.model or not self.vectorizer:
            # Fallback to rule-based
            return self._rule_based_sentiment(text)
        
        # Preprocess text
        tokens = self.preprocessor.preprocess(text, tokenize=True)
        processed_text = ' '.join(tokens)
        
        # Predict
        X = self.vectorizer.transform([processed_text])
        prediction = self.model.predict(X)[0]
        probabilities = self.model.predict_proba(X)[0]
        
        # Map prediction to sentiment
        sentiment_map = {
            'positive': SentimentType.POSITIVE,
            'negative': SentimentType.NEGATIVE,
            'neutral': SentimentType.NEUTRAL
        }
        
        sentiment = sentiment_map.get(prediction, SentimentType.NEUTRAL)
        confidence = max(probabilities)
        
        # Get individual scores
        classes = self.model.classes_
        positive_score = probabilities[classes == 'positive'][0] if 'positive' in classes else 0
        negative_score = probabilities[classes == 'negative'][0] if 'negative' in classes else 0
        neutral_score = probabilities[classes == 'neutral'][0] if 'neutral' in classes else 0
        
        return SentimentResult(
            text=text,
            sentiment=sentiment,
            confidence=confidence,
            positive_score=positive_score,
            negative_score=negative_score,
            neutral_score=neutral_score
        )
    
    def _transformer_sentiment(self, text: str) -> SentimentResult:
        """Transformer-based sentiment analysis."""
        if not TRANSFORMERS_AVAILABLE or not self.transformer_pipeline:
            # Fallback to rule-based
            return self._rule_based_sentiment(text)
        
        try:
            result = self.transformer_pipeline(text)
            
            # Map to our sentiment types
            sentiment_map = {
                'POSITIVE': SentimentType.POSITIVE,
                'NEGATIVE': SentimentType.NEGATIVE,
                'NEUTRAL': SentimentType.NEUTRAL
            }
            
            sentiment = sentiment_map.get(result['label'], SentimentType.NEUTRAL)
            confidence = result['score']
            
            # Estimate individual scores
            if sentiment == SentimentType.POSITIVE:
                positive_score = confidence
                negative_score = (1 - confidence) / 2
                neutral_score = (1 - confidence) / 2
            elif sentiment == SentimentType.NEGATIVE:
                negative_score = confidence
                positive_score = (1 - confidence) / 2
                neutral_score = (1 - confidence) / 2
            else:
                neutral_score = confidence
                positive_score = (1 - confidence) / 2
                negative_score = (1 - confidence) / 2
            
            return SentimentResult(
                text=text,
                sentiment=sentiment,
                confidence=confidence,
                positive_score=positive_score,
                negative_score=negative_score,
                neutral_score=neutral_score
            )
        except Exception as e:
            logger.warning(f"Transformer sentiment analysis failed: {e}")
            return self._rule_based_sentiment(text)
    
    def analyze(self, text: str) -> SentimentResult:
        """
        Analyze sentiment of text.
        
        Args:
            text: Input text
            
        Returns:
            Sentiment analysis result
        """
        if self.model_type == "rule_based":
            return self._rule_based_sentiment(text)
        elif self.model_type == "ml":
            return self._ml_sentiment(text)
        elif self.model_type == "transformer":
            return self._transformer_sentiment(text)
        elif self.model_type == "hybrid":
            # Combine multiple approaches
            rule_result = self._rule_based_sentiment(text)
            ml_result = self._ml_sentiment(text)
            
            # Weighted combination
            combined_positive = (rule_result.positive_score + ml_result.positive_score) / 2
            combined_negative = (rule_result.negative_score + ml_result.negative_score) / 2
            combined_neutral = (rule_result.neutral_score + ml_result.neutral_score) / 2
            
            # Determine final sentiment
            if combined_positive > combined_negative and combined_positive > combined_neutral:
                sentiment = SentimentType.POSITIVE
                confidence = combined_positive
            elif combined_negative > combined_positive and combined_negative > combined_neutral:
                sentiment = SentimentType.NEGATIVE
                confidence = combined_negative
            else:
                sentiment = SentimentType.NEUTRAL
                confidence = combined_neutral
            
            return SentimentResult(
                text=text,
                sentiment=sentiment,
                confidence=confidence,
                positive_score=combined_positive,
                negative_score=combined_negative,
                neutral_score=combined_neutral
            )
        else:
            return self._rule_based_sentiment(text)
    
    def train(self, texts: List[str], labels: List[str]):
        """
        Train the sentiment analyzer.
        
        Args:
            texts: Training texts
            labels: Training labels
        """
        if self.model_type in ["ml", "hybrid"]:
            self._train_ml_model(texts, labels)
        
        if self.model_type == "transformer" and TRANSFORMERS_AVAILABLE:
            try:
                self.transformer_pipeline = pipeline(
                    "sentiment-analysis",
                    model="cardiffnlp/twitter-roberta-base-sentiment-latest"
                )
            except Exception as e:
                logger.warning(f"Failed to load transformer model: {e}")


class EntityRecognizer:
    """Named Entity Recognition using multiple approaches."""
    
    def __init__(self, model_type: str = "spacy"):
        """
        Initialize entity recognizer.
        
        Args:
            model_type: Type of model ("spacy", "nltk", "regex")
        """
        self.model_type = model_type
        self.nlp_model = None
        self.preprocessor = TextPreprocessor()
        
        # Regex patterns for common entities
        self.regex_patterns = {
            EntityType.EMAIL: r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            EntityType.URL: r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            EntityType.PHONE: r'(\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}',
            EntityType.MONEY: r'\$[\d,]+(?:\.\d{2})?',
            EntityType.PERCENT: r'\d+(?:\.\d+)?%',
            EntityType.DATE: r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
        }
        
        if model_type == "spacy" and SPACY_AVAILABLE:
            try:
                self.nlp_model = spacy.load("en_core_web_sm")
            except OSError:
                logger.warning("spaCy English model not found. Install with: python -m spacy download en_core_web_sm")
                self.model_type = "regex"
    
    def _spacy_entities(self, text: str) -> List[EntityResult]:
        """Extract entities using spaCy."""
        if not self.nlp_model:
            return []
        
        doc = self.nlp_model(text)
        entities = []
        
        for ent in doc.ents:
            entity_type = EntityType(ent.label_) if ent.label_ in [e.value for e in EntityType] else EntityType.PERSON
            entities.append(EntityResult(
                text=text,
                entity=ent.text,
                entity_type=entity_type,
                start_pos=ent.start_char,
                end_pos=ent.end_char,
                confidence=1.0  # spaCy doesn't provide confidence scores
            ))
        
        return entities
    
    def _nltk_entities(self, text: str) -> List[EntityResult]:
        """Extract entities using NLTK."""
        if not NLTK_AVAILABLE:
            return []
        
        try:
            tokens = word_tokenize(text)
            pos_tags = pos_tag(tokens)
            chunks = ne_chunk(pos_tags)
            
            entities = []
            current_chunk = []
            
            for chunk in chunks:
                if hasattr(chunk, 'label'):
                    current_chunk.append(chunk)
                else:
                    if current_chunk:
                        entity_text = ' '.join([token for token, pos in current_chunk])
                        entity_type = EntityType(current_chunk[0].label()) if current_chunk[0].label() in [e.value for e in EntityType] else EntityType.PERSON
                        
                        # Find position in original text
                        start_pos = text.find(entity_text)
                        end_pos = start_pos + len(entity_text)
                        
                        entities.append(EntityResult(
                            text=text,
                            entity=entity_text,
                            entity_type=entity_type,
                            start_pos=start_pos,
                            end_pos=end_pos,
                            confidence=1.0
                        ))
                        current_chunk = []
            
            return entities
        except Exception as e:
            logger.warning(f"NLTK entity recognition failed: {e}")
            return []
    
    def _regex_entities(self, text: str) -> List[EntityResult]:
        """Extract entities using regex patterns."""
        entities = []
        
        for entity_type, pattern in self.regex_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append(EntityResult(
                    text=text,
                    entity=match.group(),
                    entity_type=entity_type,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=0.8  # Lower confidence for regex
                ))
        
        return entities
    
    def extract_entities(self, text: str) -> List[EntityResult]:
        """
        Extract named entities from text.
        
        Args:
            text: Input text
            
        Returns:
            List of entity results
        """
        if self.model_type == "spacy":
            return self._spacy_entities(text)
        elif self.model_type == "nltk":
            return self._nltk_entities(text)
        elif self.model_type == "regex":
            return self._regex_entities(text)
        else:
            return self._regex_entities(text)


class TextClassifier:
    """Text classification using multiple algorithms."""
    
    def __init__(self, algorithm: str = "logistic_regression"):
        """
        Initialize text classifier.
        
        Args:
            algorithm: Classification algorithm ("logistic_regression", "naive_bayes", "random_forest")
        """
        self.algorithm = algorithm
        self.preprocessor = TextPreprocessor()
        self.model = None
        self.vectorizer = None
        self.classes_ = None
        
        # Algorithm mapping
        self.algorithms = {
            "logistic_regression": LogisticRegression,
            "naive_bayes": MultinomialNB,
            "random_forest": RandomForestClassifier
        }
    
    def train(self, texts: List[str], labels: List[str]):
        """
        Train the text classifier.
        
        Args:
            texts: Training texts
            labels: Training labels
        """
        # Preprocess texts
        processed_texts = []
        for text in texts:
            tokens = self.preprocessor.preprocess(text, tokenize=True)
            processed_texts.append(' '.join(tokens))
        
        # Create pipeline
        self.vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
        model_class = self.algorithms.get(self.algorithm, LogisticRegression)
        self.model = model_class(random_state=42)
        
        # Train
        X = self.vectorizer.fit_transform(processed_texts)
        self.model.fit(X, labels)
        self.classes_ = self.model.classes_
    
    def predict(self, text: str) -> ClassificationResult:
        """
        Classify text.
        
        Args:
            text: Input text
            
        Returns:
            Classification result
        """
        if not self.model or not self.vectorizer:
            return ClassificationResult(
                text=text,
                predicted_class="unknown",
                confidence=0.0,
                class_probabilities={}
            )
        
        # Preprocess text
        tokens = self.preprocessor.preprocess(text, tokenize=True)
        processed_text = ' '.join(tokens)
        
        # Predict
        X = self.vectorizer.transform([processed_text])
        prediction = self.model.predict(X)[0]
        probabilities = self.model.predict_proba(X)[0]
        
        # Create class probabilities dictionary
        class_probabilities = dict(zip(self.classes_, probabilities))
        confidence = max(probabilities)
        
        return ClassificationResult(
            text=text,
            predicted_class=prediction,
            confidence=confidence,
            class_probabilities=class_probabilities
        )
    
    def evaluate(self, texts: List[str], labels: List[str]) -> Dict[str, float]:
        """
        Evaluate classifier performance.
        
        Args:
            texts: Test texts
            labels: Test labels
            
        Returns:
            Evaluation metrics
        """
        predictions = []
        for text in texts:
            result = self.predict(text)
            predictions.append(result.predicted_class)
        
        return {
            "accuracy": accuracy_score(labels, predictions),
            "classification_report": classification_report(labels, predictions, output_dict=True)
        }


class NLPProcessor:
    """Main NLP processor combining all capabilities."""
    
    def __init__(self):
        """Initialize NLP processor."""
        self.sentiment_analyzer = SentimentAnalyzer()
        self.entity_recognizer = EntityRecognizer()
        self.text_classifier = TextClassifier()
        self.preprocessor = TextPreprocessor()
    
    async def process_text(self, text: str, 
                          sentiment: bool = True,
                          entities: bool = True,
                          classification: bool = False,
                          classification_labels: List[str] = None) -> Dict[str, Any]:
        """
        Process text with multiple NLP techniques.
        
        Args:
            text: Input text
            sentiment: Whether to perform sentiment analysis
            entities: Whether to extract entities
            classification: Whether to perform classification
            classification_labels: Labels for classification (if training needed)
            
        Returns:
            Processing results
        """
        results = {
            "text": text,
            "preprocessed": self.preprocessor.preprocess(text),
            "sentiment": None,
            "entities": [],
            "classification": None
        }
        
        # Sentiment analysis
        if sentiment:
            results["sentiment"] = self.sentiment_analyzer.analyze(text)
        
        # Entity recognition
        if entities:
            results["entities"] = self.entity_recognizer.extract_entities(text)
        
        # Text classification
        if classification and self.text_classifier.model:
            results["classification"] = self.text_classifier.predict(text)
        
        return results
    
    def train_sentiment(self, texts: List[str], labels: List[str]):
        """Train sentiment analyzer."""
        self.sentiment_analyzer.train(texts, labels)
    
    def train_classifier(self, texts: List[str], labels: List[str]):
        """Train text classifier."""
        self.text_classifier.train(texts, labels)
    
    def get_supported_languages(self) -> List[str]:
        """Get supported languages."""
        return ["english"]  # Can be extended
    
    def get_available_models(self) -> Dict[str, List[str]]:
        """Get available models."""
        return {
            "sentiment": ["rule_based", "ml", "transformer", "hybrid"],
            "entities": ["spacy", "nltk", "regex"],
            "classification": ["logistic_regression", "naive_bayes", "random_forest"]
        }
