import openai
from typing import Dict, List, Optional, Tuple
import base64
from ..config import settings
from ..models.script import ExtractedQuestion, QuestionFragment
from ..utils.text_processing import detect_question_numbers, segment_text_by_questions, normalize_text
from ..utils.image_processing import preprocess_image, validate_image
import logging
import json
import asyncio

logger = logging.getLogger(__name__)

class OCRService:
    def __init__(self):
        if settings.openai_api_key:
            openai.api_key = settings.openai_api_key
        else:
            logger.warning("OpenAI API key not set")
    
    async def extract_text_from_image(self, image_path: str) -> Tuple[str, float]:
        """
        Extract text from image using OpenAI Vision API.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        try:
            # Validate image first
            is_valid, error_msg = validate_image(image_path)
            if not is_valid:
                raise ValueError(f"Invalid image: {error_msg}")
            
            # Preprocess image for better OCR
            processed_image_path = preprocess_image(image_path)
            
            # Encode image to base64
            with open(processed_image_path, 'rb') as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Prepare the prompt
            prompt = """
            You are an expert OCR system designed to extract handwritten text from answer sheets.
            Please extract ALL text from this image, maintaining the original structure and format.
            
            Important instructions:
            1. Preserve question numbers and their format (1., Q1:, Answer 1:, etc.)
            2. Maintain line breaks and paragraph structure
            3. Include ALL readable text, even if partially visible
            4. If text is unclear, include your best interpretation in [brackets]
            5. Indicate confidence level for unclear sections
            
            Please provide the extracted text exactly as written.
            """
            
            # Make API call to OpenAI Vision
            response = await self._call_openai_vision(base64_image, prompt)
            
            if not response:
                return "", 0.0
            
            # Extract text and estimate confidence
            extracted_text = response.get('text', '')
            confidence = self._estimate_confidence(response)
            
            logger.info(f"OCR extracted {len(extracted_text)} characters with confidence {confidence}")
            
            return extracted_text, confidence
            
        except Exception as e:
            logger.error(f"Error extracting text from image {image_path}: {e}")
            return "", 0.0
    
    async def _call_openai_vision(self, base64_image: str, prompt: str) -> Optional[Dict]:
        """Make API call to OpenAI Vision API."""
        try:
            if not settings.openai_api_key:
                logger.error("OpenAI API key not configured")
                return None
            
            # Simulate OpenAI Vision API call (replace with actual API call)
            # In production, this would be the actual OpenAI API call:
            """
            response = await openai.ChatCompletion.acreate(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=4000
            )
            
            return {
                'text': response.choices[0].message.content,
                'confidence': 0.9  # Estimate based on API response
            }
            """
            
            # Mock response for development
            mock_text = """
            1. Define a binary tree and explain its properties.
            
            Answer: A binary tree is a hierarchical data structure where each node has at most two children, referred to as left and right child. The properties include:
            - Each node contains data
            - Maximum two children per node
            - Can be empty (null tree)
            - Root node has no parent
            
            2. What is the time complexity of binary tree traversal?
            
            Answer: The time complexity of binary tree traversal is O(n) where n is the number of nodes, because we visit each node exactly once during the traversal process.
            
            3. Implement inorder traversal recursively.
            
            Answer: 
            def inorder(root):
                if root:
                    inorder(root.left)
                    print(root.data)
                    inorder(root.right)
            """
            
            return {
                'text': mock_text.strip(),
                'confidence': 0.85
            }
            
        except Exception as e:
            logger.error(f"Error calling OpenAI Vision API: {e}")
            return None
    
    def _estimate_confidence(self, response: Dict) -> float:
        """Estimate confidence score based on OCR response."""
        # In production, this would analyze the API response for confidence indicators
        base_confidence = response.get('confidence', 0.5)
        
        text = response.get('text', '')
        
        # Adjust confidence based on text characteristics
        if len(text) < 50:
            base_confidence *= 0.8  # Short text might be incomplete
        
        # Check for uncertainty indicators
        uncertainty_markers = ['[', ']', '?', 'unclear', 'illegible']
        uncertainty_count = sum(1 for marker in uncertainty_markers if marker in text.lower())
        
        if uncertainty_count > 0:
            base_confidence *= max(0.3, 1 - (uncertainty_count * 0.1))
        
        return min(1.0, max(0.0, base_confidence))
    
    async def extract_and_segment_questions(self, image_path: str) -> Tuple[List[ExtractedQuestion], float]:
        """
        Extract text from image and segment it by questions.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Tuple of (extracted_questions, overall_confidence)
        """
        try:
            # Extract raw text
            raw_text, ocr_confidence = await self.extract_text_from_image(image_path)
            
            if not raw_text:
                return [], 0.0
            
            # Normalize text
            normalized_text = normalize_text(raw_text)
            
            # Segment text by questions
            question_segments = segment_text_by_questions(normalized_text)
            
            # Create ExtractedQuestion objects
            extracted_questions = []
            
            for q_num, q_text in question_segments.items():
                # Create question fragment
                fragment = QuestionFragment(
                    fragment_text=q_text,
                    confidence=ocr_confidence,
                    page_number=1  # Assuming single page for now
                )
                
                # Create extracted question
                question = ExtractedQuestion(
                    question_number=q_num,
                    raw_text=q_text,
                    fragments=[fragment],
                    is_complete=len(q_text.strip()) > 10,  # Basic completeness check
                    has_duplicates=False,  # Will be checked later
                    confidence=ocr_confidence
                )
                
                extracted_questions.append(question)
            
            # Check for duplicates
            await self._check_for_duplicates(extracted_questions)
            
            logger.info(f"Extracted {len(extracted_questions)} questions from image")
            
            return extracted_questions, ocr_confidence
            
        except Exception as e:
            logger.error(f"Error extracting and segmenting questions: {e}")
            return [], 0.0
    
    async def _check_for_duplicates(self, questions: List[ExtractedQuestion]) -> None:
        """Check for duplicate content in extracted questions."""
        try:
            from ..utils.text_processing import detect_duplicate_content
            
            # Extract text from all questions
            question_texts = [q.raw_text for q in questions]
            
            # Detect duplicates
            duplicates = detect_duplicate_content(question_texts, threshold=0.7)
            
            # Mark questions with duplicates
            duplicate_indices = set()
            for idx1, idx2, _ in duplicates:
                duplicate_indices.add(idx1)
                duplicate_indices.add(idx2)
            
            for idx in duplicate_indices:
                if idx < len(questions):
                    questions[idx].has_duplicates = True
            
            if duplicates:
                logger.warning(f"Detected {len(duplicates)} duplicate question pairs")
                
        except Exception as e:
            logger.error(f"Error checking for duplicates: {e}")
    
    async def enhance_text_quality(self, raw_text: str) -> Tuple[str, float]:
        """
        Use AI to enhance and clean up OCR text.
        
        Args:
            raw_text: Raw OCR extracted text
            
        Returns:
            Tuple of (enhanced_text, confidence_improvement)
        """
        try:
            if not raw_text or len(raw_text.strip()) < 10:
                return raw_text, 0.0
            
            prompt = f"""
            You are an expert text enhancer. The following text was extracted from a handwritten answer sheet using OCR.
            Please enhance and clean it up while maintaining the original meaning and structure.
            
            Tasks:
            1. Fix obvious OCR errors and spelling mistakes
            2. Maintain original question numbers and structure
            3. Improve readability while preserving student's words
            4. DO NOT add content that wasn't in the original
            5. Mark any uncertain corrections with [?]
            
            Original OCR text:
            {raw_text}
            
            Enhanced text:
            """
            
            # This would make an actual API call in production
            # For now, return the original text with minimal processing
            enhanced = raw_text.strip()
            
            # Basic cleanup
            enhanced = enhanced.replace('\n\n\n', '\n\n')
            enhanced = enhanced.replace('  ', ' ')
            
            confidence_improvement = 0.1  # Small improvement from cleanup
            
            return enhanced, confidence_improvement
            
        except Exception as e:
            logger.error(f"Error enhancing text quality: {e}")
            return raw_text, 0.0
    
    async def validate_question_extraction(self, questions: List[ExtractedQuestion]) -> Dict[str, bool]:
        """
        Validate the quality of question extraction.
        
        Args:
            questions: List of extracted questions
            
        Returns:
            Dictionary with validation results
        """
        validation = {
            'has_questions': len(questions) > 0,
            'reasonable_count': 1 <= len(questions) <= 20,
            'all_have_content': all(len(q.raw_text.strip()) > 5 for q in questions),
            'no_major_duplicates': not any(q.has_duplicates for q in questions),
            'good_confidence': all(q.confidence >= 0.5 for q in questions),
            'sequential_numbers': self._check_sequential_numbers(questions)
        }
        
        validation['overall_valid'] = all(validation.values())
        
        return validation
    
    def _check_sequential_numbers(self, questions: List[ExtractedQuestion]) -> bool:
        """Check if question numbers are reasonably sequential."""
        if not questions:
            return False
        
        numbers = sorted([q.question_number for q in questions])
        
        # Check if numbers start from 1 and are mostly sequential
        if numbers[0] != 1:
            return False
        
        # Allow some gaps but not too many
        max_expected = numbers[-1]
        if len(numbers) < max_expected * 0.5:  # Too many missing numbers
            return False
        
        return True