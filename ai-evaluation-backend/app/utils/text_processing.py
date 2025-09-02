import re
from typing import List, Tuple, Dict, Any
import logging

# Optional imports for ML functionality
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Sentence transformers not available - using fallback similarity calculation")

logger = logging.getLogger(__name__)

# Global sentence transformer model (loaded once)
_sentence_model = None

def get_sentence_model():
    """Get or initialize sentence transformer model."""
    global _sentence_model
    if not SENTENCE_TRANSFORMERS_AVAILABLE:
        return None
    
    if _sentence_model is None:
        try:
            _sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Sentence transformer model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading sentence transformer model: {e}")
            _sentence_model = None
    return _sentence_model

def detect_question_numbers(text: str) -> List[Tuple[int, int, str]]:
    """
    Detect question numbers and their positions in text.
    
    Args:
        text: Input text
        
    Returns:
        List of tuples (question_number, position, matched_pattern)
    """
    patterns = [
        r'(?:^|\n)\s*(\d+)\s*[\.\)]\s*',  # "1.", "1)", "2."
        r'(?:^|\n)\s*[Qq](?:uestion)?\s*(\d+)\s*[\:\.\)]\s*',  # "Q1:", "Question 1."
        r'(?:^|\n)\s*[Aa]ns(?:wer)?\s*(\d+)\s*[\:\.\)]\s*',  # "Ans 1:", "Answer 1:"
        r'(?:^|\n)\s*(\d+)\s*[a-z]\s*[\)\.\:]',  # "1a)", "2b."
        r'(?:^|\n)\s*(\d+)\s*\([ivx]+\)\s*',  # "1(i)", "2(ii)"
    ]
    
    questions = []
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            question_num = int(match.group(1))
            position = match.start()
            matched_text = match.group(0)
            questions.append((question_num, position, matched_text))
    
    # Sort by position and remove duplicates
    questions = sorted(set(questions), key=lambda x: x[1])
    
    return questions

def segment_text_by_questions(text: str) -> Dict[int, str]:
    """
    Segment text by detected question numbers.
    
    Args:
        text: Input text
        
    Returns:
        Dictionary mapping question numbers to their text content
    """
    questions = detect_question_numbers(text)
    
    if not questions:
        # If no questions detected, return as single question
        return {1: text.strip()}
    
    segments = {}
    
    for i, (q_num, start_pos, _) in enumerate(questions):
        # Find end position (start of next question or end of text)
        if i < len(questions) - 1:
            end_pos = questions[i + 1][1]
        else:
            end_pos = len(text)
        
        # Extract question text
        question_text = text[start_pos:end_pos].strip()
        
        # Clean up the text (remove question number prefix)
        cleaned_text = clean_question_text(question_text)
        
        segments[q_num] = cleaned_text
    
    return segments

def clean_question_text(text: str) -> str:
    """
    Clean question text by removing question number prefixes.
    
    Args:
        text: Raw question text
        
    Returns:
        Cleaned question text
    """
    # Remove common question prefixes
    patterns_to_remove = [
        r'^\s*\d+\s*[\.\)]\s*',
        r'^\s*[Qq](?:uestion)?\s*\d+\s*[\:\.\)]\s*',
        r'^\s*[Aa]ns(?:wer)?\s*\d+\s*[\:\.\)]\s*',
        r'^\s*\d+\s*[a-z]\s*[\)\.\:]\s*',
        r'^\s*\d+\s*\([ivx]+\)\s*',
    ]
    
    cleaned = text
    for pattern in patterns_to_remove:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    return cleaned.strip()

def extract_key_concepts(text: str, min_word_length: int = 3) -> List[str]:
    """
    Extract key concepts from text using simple keyword extraction.
    
    Args:
        text: Input text
        min_word_length: Minimum word length to consider
        
    Returns:
        List of key concepts
    """
    # Simple concept extraction - can be enhanced with NLP libraries
    
    # Common stop words to exclude
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
        'before', 'after', 'above', 'below', 'between', 'among', 'through',
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
        'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
        'can', 'cannot', 'this', 'that', 'these', 'those', 'i', 'you', 'he',
        'she', 'it', 'we', 'they', 'them', 'their', 'what', 'which', 'who',
        'when', 'where', 'why', 'how'
    }
    
    # Extract words
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    
    # Filter words
    concepts = [
        word for word in words 
        if len(word) >= min_word_length and word not in stop_words
    ]
    
    # Count frequency and return top concepts
    from collections import Counter
    concept_counts = Counter(concepts)
    
    # Return most frequent concepts
    return [concept for concept, _ in concept_counts.most_common(20)]

def calculate_semantic_similarity(text1: str, text2: str) -> float:
    """
    Calculate semantic similarity between two texts using sentence transformers.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity score between 0 and 1
    """
    model = get_sentence_model()
    
    if model is None:
        # Fallback to keyword-based similarity
        return calculate_keyword_similarity(text1, text2)
    
    try:
        # Generate embeddings
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            embeddings = model.encode([text1, text2])
            # Calculate cosine similarity
            similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        else:
            # Fallback to keyword similarity
            return calculate_keyword_similarity(text1, text2)
        
        # Ensure similarity is between 0 and 1
        return max(0, min(1, similarity))
        
    except Exception as e:
        logger.error(f"Error calculating semantic similarity: {e}")
        return calculate_keyword_similarity(text1, text2)

def calculate_keyword_similarity(text1: str, text2: str) -> float:
    """
    Calculate keyword-based similarity as fallback.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity score between 0 and 1
    """
    concepts1 = set(extract_key_concepts(text1))
    concepts2 = set(extract_key_concepts(text2))
    
    if not concepts1 or not concepts2:
        return 0.0
    
    intersection = concepts1.intersection(concepts2)
    union = concepts1.union(concepts2)
    
    return len(intersection) / len(union) if union else 0.0

def detect_duplicate_content(segments: List[str], threshold: float = 0.8) -> List[Tuple[int, int, float]]:
    """
    Detect duplicate content in text segments.
    
    Args:
        segments: List of text segments
        threshold: Similarity threshold for duplicates
        
    Returns:
        List of tuples (index1, index2, similarity_score) for duplicates
    """
    duplicates = []
    
    for i in range(len(segments)):
        for j in range(i + 1, len(segments)):
            similarity = calculate_semantic_similarity(segments[i], segments[j])
            if similarity >= threshold:
                duplicates.append((i, j, similarity))
    
    return duplicates

def merge_fragmented_answers(fragments: List[str]) -> str:
    """
    Merge fragmented answer parts into coherent text.
    
    Args:
        fragments: List of answer fragments
        
    Returns:
        Merged answer text
    """
    if not fragments:
        return ""
    
    if len(fragments) == 1:
        return fragments[0].strip()
    
    # Simple merging strategy - join with appropriate spacing
    merged = ""
    
    for i, fragment in enumerate(fragments):
        fragment = fragment.strip()
        if not fragment:
            continue
            
        if i == 0:
            merged = fragment
        else:
            # Check if we need spacing
            if merged and not merged.endswith(('.', '!', '?', ':', ';')):
                if not fragment.startswith((',', '.', '!', '?', ':', ';')):
                    merged += " "
            merged += fragment
    
    return merged.strip()

def normalize_text(text: str) -> str:
    """
    Normalize text for consistent processing.
    
    Args:
        text: Input text
        
    Returns:
        Normalized text
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters except punctuation
    text = re.sub(r'[^\w\s.,!?;:()\-]', '', text)
    
    # Normalize case
    text = text.strip()
    
    return text

def extract_mathematical_expressions(text: str) -> List[str]:
    """
    Extract mathematical expressions from text.
    
    Args:
        text: Input text
        
    Returns:
        List of mathematical expressions
    """
    patterns = [
        r'\b\d+\s*[\+\-\*/=]\s*\d+\b',  # Simple arithmetic
        r'\b[a-zA-Z]\s*[=]\s*[a-zA-Z0-9\+\-\*/\(\)\s]+',  # Equations
        r'\b[a-zA-Z]\^?\d+\b',  # Variables with powers
        r'\b\d+\.\d+\b',  # Decimal numbers
        r'\b\d+/\d+\b',  # Fractions
    ]
    
    expressions = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        expressions.extend(matches)
    
    return list(set(expressions))