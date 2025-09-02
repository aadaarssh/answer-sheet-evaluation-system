import google.generativeai as genai
from typing import Dict, List, Optional, Any
from ..config import settings
from ..models.evaluation import EvaluationResult, GeminiVerification, QuestionEvaluation
from ..models.scheme import EvaluationScheme
import logging
import json
import asyncio

logger = logging.getLogger(__name__)

class VerificationService:
    def __init__(self):
        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            logger.warning("Gemini API key not set - verification will use fallback logic")
            self.model = None
    
    async def verify_evaluation(
        self,
        evaluation_result: EvaluationResult,
        evaluation_scheme: EvaluationScheme,
        student_answers: Dict[int, str]
    ) -> GeminiVerification:
        """
        Verify the AI evaluation using Gemini AI.
        
        Args:
            evaluation_result: The AI evaluation to verify
            evaluation_scheme: The evaluation scheme used
            student_answers: Dictionary of question number to student answer text
            
        Returns:
            Gemini verification result
        """
        try:
            if not self.model:
                # Fallback verification without Gemini
                return self._fallback_verification(evaluation_result)
            
            # Prepare verification prompt
            prompt = self._create_verification_prompt(
                evaluation_result, evaluation_scheme, student_answers
            )
            
            # Get verification from Gemini
            verification_response = await self._call_gemini_api(prompt)
            
            if not verification_response:
                return self._fallback_verification(evaluation_result)
            
            # Parse verification response
            verification = self._parse_verification_response(
                verification_response, evaluation_result
            )
            
            logger.info(f"Gemini verification completed with confidence {verification.confidence_score}")
            
            return verification
            
        except Exception as e:
            logger.error(f"Error in Gemini verification: {e}")
            return self._fallback_verification(evaluation_result)
    
    def _create_verification_prompt(
        self,
        evaluation_result: EvaluationResult,
        evaluation_scheme: EvaluationScheme,
        student_answers: Dict[int, str]
    ) -> str:
        """Create a comprehensive prompt for Gemini verification."""
        
        # Build evaluation summary
        evaluation_summary = []
        for q_eval in evaluation_result.question_scores:
            student_text = student_answers.get(q_eval.question_number, "No answer provided")
            evaluation_summary.append(f"""
Question {q_eval.question_number}:
Student Answer: {student_text[:500]}{'...' if len(student_text) > 500 else ''}
AI Score: {q_eval.score}/{q_eval.max_score} ({(q_eval.score/q_eval.max_score*100):.1f}%)
AI Confidence: {q_eval.overall_confidence:.2f}
""")
        
        # Build scheme summary
        scheme_summary = []
        for question in evaluation_scheme.questions:
            concepts = [f"- {concept.concept} ({concept.marks_allocation} marks)" 
                       for concept in question.concepts]
            scheme_summary.append(f"""
Question {question.question_number} (Max: {question.max_marks} marks):
{chr(10).join(concepts)}
""")
        
        prompt = f"""
You are an expert academic evaluator tasked with verifying an AI-generated evaluation of student answer sheets.

EVALUATION SCHEME:
Subject: {evaluation_scheme.subject}
Total Marks: {evaluation_scheme.total_marks}
Passing Marks: {evaluation_scheme.passing_marks}

Questions and Marking Criteria:
{"".join(scheme_summary)}

STUDENT EVALUATION:
Total Score: {evaluation_result.total_score}/{evaluation_result.max_possible_score} ({evaluation_result.percentage:.1f}%)

Question-wise Breakdown:
{"".join(evaluation_summary)}

VERIFICATION TASK:
Please verify this evaluation and provide feedback in the following JSON format:

{{
    "verified": true/false,
    "confidence_score": 0.0-1.0,
    "overall_assessment": "brief overall assessment",
    "question_feedback": [
        {{
            "question_number": 1,
            "ai_score_appropriate": true/false,
            "suggested_score": null or alternative_score,
            "reasoning": "explanation for any adjustments"
        }}
    ],
    "suggested_adjustments": [
        {{
            "question_number": 1,
            "current_score": current_score,
            "suggested_score": suggested_score,
            "reason": "reason for adjustment"
        }}
    ],
    "flagged_for_review": true/false,
    "verification_notes": "detailed notes about the evaluation quality"
}}

Consider these factors:
1. Are the AI scores consistent with the marking scheme?
2. Has the AI correctly identified key concepts in student answers?
3. Are the marks allocated fairly compared to the quality of answers?
4. Are there any obvious over-scoring or under-scoring issues?
5. Should this evaluation be flagged for manual review?

Please be thorough but fair in your verification.
"""
        
        return prompt
    
    async def _call_gemini_api(self, prompt: str) -> Optional[str]:
        """Make API call to Gemini."""
        try:
            if not self.model:
                return None
            
            # Simulate Gemini API call (replace with actual API call in production)
            """
            response = await self.model.generate_content_async(prompt)
            return response.text
            """
            
            # Mock response for development
            mock_response = """
            {
                "verified": true,
                "confidence_score": 0.85,
                "overall_assessment": "The AI evaluation appears generally accurate and well-reasoned. Most scores align with the marking scheme and student answer quality.",
                "question_feedback": [
                    {
                        "question_number": 1,
                        "ai_score_appropriate": true,
                        "suggested_score": null,
                        "reasoning": "Score appropriately reflects the student's understanding of binary tree concepts"
                    },
                    {
                        "question_number": 2,
                        "ai_score_appropriate": true,
                        "suggested_score": null,
                        "reasoning": "Correct identification of time complexity understanding"
                    }
                ],
                "suggested_adjustments": [],
                "flagged_for_review": false,
                "verification_notes": "AI evaluation demonstrates good alignment with academic standards. No significant discrepancies detected."
            }
            """
            
            return mock_response
            
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            return None
    
    def _parse_verification_response(
        self, response: str, original_evaluation: EvaluationResult
    ) -> GeminiVerification:
        """Parse Gemini's verification response."""
        try:
            # Try to parse JSON response
            verification_data = json.loads(response.strip())
            
            # Extract suggested adjustments
            suggested_adjustments = []
            for adjustment in verification_data.get('suggested_adjustments', []):
                suggested_adjustments.append({
                    'question_number': adjustment.get('question_number'),
                    'current_score': adjustment.get('current_score'),
                    'suggested_score': adjustment.get('suggested_score'),
                    'reason': adjustment.get('reason', '')
                })
            
            return GeminiVerification(
                verified=verification_data.get('verified', True),
                confidence_score=verification_data.get('confidence_score', 0.8),
                suggested_adjustments=suggested_adjustments,
                flagged_for_review=verification_data.get('flagged_for_review', False),
                verification_notes=verification_data.get('verification_notes', ''),
                original_score=original_evaluation.total_score,
                suggested_score=self._calculate_suggested_total_score(
                    original_evaluation, suggested_adjustments
                )
            )
            
        except json.JSONDecodeError:
            logger.error("Failed to parse Gemini verification response as JSON")
            return self._fallback_verification(original_evaluation)
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {e}")
            return self._fallback_verification(original_evaluation)
    
    def _calculate_suggested_total_score(
        self, original_evaluation: EvaluationResult, adjustments: List[Dict[str, Any]]
    ) -> Optional[float]:
        """Calculate total score if Gemini adjustments were applied."""
        if not adjustments:
            return None
        
        total = original_evaluation.total_score
        
        for adjustment in adjustments:
            q_num = adjustment.get('question_number')
            suggested = adjustment.get('suggested_score')
            current = adjustment.get('current_score')
            
            if all(x is not None for x in [q_num, suggested, current]):
                total = total - current + suggested
        
        return total
    
    def _fallback_verification(self, evaluation_result: EvaluationResult) -> GeminiVerification:
        """Provide fallback verification when Gemini is not available."""
        
        # Simple heuristic-based verification
        confidence = self._calculate_fallback_confidence(evaluation_result)
        
        # Flag for review if confidence is low or other issues
        flag_for_review = (
            confidence < 0.7 or
            evaluation_result.requires_manual_review or
            evaluation_result.percentage < 30  # Very low scores
        )
        
        notes = f"Fallback verification (Gemini unavailable). "
        if flag_for_review:
            notes += "Flagged for manual review due to low confidence or concerning patterns."
        else:
            notes += "Evaluation appears reasonable based on heuristic analysis."
        
        return GeminiVerification(
            verified=not flag_for_review,
            confidence_score=confidence,
            suggested_adjustments=[],
            flagged_for_review=flag_for_review,
            verification_notes=notes,
            original_score=evaluation_result.total_score
        )
    
    def _calculate_fallback_confidence(self, evaluation_result: EvaluationResult) -> float:
        """Calculate verification confidence using heuristics."""
        
        # Base confidence from AI evaluation confidences
        ai_confidences = [q.overall_confidence for q in evaluation_result.question_scores]
        avg_ai_confidence = sum(ai_confidences) / len(ai_confidences) if ai_confidences else 0.5
        
        # Adjust based on various factors
        confidence = avg_ai_confidence
        
        # Penalize if many questions need review
        questions_needing_review = sum(1 for q in evaluation_result.question_scores if q.needs_review)
        total_questions = len(evaluation_result.question_scores)
        
        if total_questions > 0:
            review_ratio = questions_needing_review / total_questions
            confidence *= (1.0 - review_ratio * 0.3)  # Up to 30% reduction
        
        # Penalize extremely low or high scores (might indicate issues)
        if evaluation_result.percentage < 10 or evaluation_result.percentage > 95:
            confidence *= 0.8
        
        # Bonus for consistent scoring
        if all(q.overall_confidence > 0.7 for q in evaluation_result.question_scores):
            confidence = min(1.0, confidence * 1.1)
        
        return max(0.0, min(1.0, confidence))
    
    async def batch_verify_evaluations(
        self,
        evaluations: List[Dict],  # List of evaluation data with all required info
        max_concurrent: int = 3
    ) -> List[GeminiVerification]:
        """
        Verify multiple evaluations concurrently.
        
        Args:
            evaluations: List of evaluation data dictionaries
            max_concurrent: Maximum concurrent verifications
            
        Returns:
            List of verification results
        """
        try:
            # Create semaphore to limit concurrent API calls
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def verify_single(eval_data):
                async with semaphore:
                    return await self.verify_evaluation(
                        eval_data['result'],
                        eval_data['scheme'], 
                        eval_data['answers']
                    )
            
            # Run verifications concurrently
            tasks = [verify_single(eval_data) for eval_data in evaluations]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle any exceptions
            verified_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Verification failed for evaluation {i}: {result}")
                    # Use fallback for failed verifications
                    verified_results.append(
                        self._fallback_verification(evaluations[i]['result'])
                    )
                else:
                    verified_results.append(result)
            
            return verified_results
            
        except Exception as e:
            logger.error(f"Error in batch verification: {e}")
            # Return fallback verifications for all
            return [
                self._fallback_verification(eval_data['result']) 
                for eval_data in evaluations
            ]