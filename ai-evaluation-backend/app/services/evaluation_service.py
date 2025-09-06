from typing import List, Dict, Optional, Tuple
from ..models.scheme import EvaluationScheme, Concept, Question
from ..models.script import ExtractedQuestion
from ..models.evaluation import (
    ConceptEvaluation, QuestionEvaluation, EvaluationResult,
    EvaluationResultCreate, ReviewReason
)
from ..utils.text_processing import (
    calculate_semantic_similarity, extract_key_concepts,
    merge_fragmented_answers, normalize_text
)
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

class EvaluationService:
    def __init__(self):
        self.confidence_threshold = 0.7
        self.min_similarity_for_marks = 0.3
    
    async def evaluate_answer_script(
        self,
        extracted_questions: List[ExtractedQuestion],
        evaluation_scheme: EvaluationScheme
    ) -> EvaluationResult:
        """
        Evaluate an entire answer script against the evaluation scheme.
        
        Args:
            extracted_questions: Questions extracted from the script
            evaluation_scheme: The evaluation scheme to use
            
        Returns:
            Complete evaluation result
        """
        try:
            question_scores = []
            total_score = 0.0
            
            # Process each question in the scheme
            for scheme_question in evaluation_scheme.questions:
                # Find corresponding extracted question
                extracted_q = self._find_matching_question(
                    scheme_question.question_number, extracted_questions
                )
                
                if extracted_q:
                    # Evaluate the question
                    evaluation = await self._evaluate_single_question(
                        extracted_q, scheme_question
                    )
                    question_scores.append(evaluation)
                    total_score += evaluation.score
                else:
                    # No answer found - zero marks
                    evaluation = QuestionEvaluation(
                        question_number=scheme_question.question_number,
                        score=0.0,
                        max_score=scheme_question.max_marks,
                        concept_breakdown=[],
                        overall_confidence=1.0,  # Confident it's missing
                        needs_review=False,
                        review_reasons=["No answer provided"]
                    )
                    question_scores.append(evaluation)
            
            # Calculate percentage
            percentage = (total_score / evaluation_scheme.total_marks * 100) if evaluation_scheme.total_marks > 0 else 0
            
            # Determine if manual review is needed
            requires_review, review_reasons = self._check_review_requirements(
                question_scores, percentage, evaluation_scheme.passing_marks
            )
            
            # Create evaluation result (as dict, will be converted to EvaluationResult later)
            result_data = {
                "total_score": total_score,
                "max_possible_score": evaluation_scheme.total_marks,
                "percentage": percentage,
                "question_scores": question_scores,
                "requires_manual_review": requires_review,
                "review_reasons": review_reasons,
                "evaluated_at": datetime.utcnow()
            }
            
            logger.info(f"Evaluation completed: {total_score}/{evaluation_scheme.total_marks} ({percentage:.1f}%)")
            
            return result_data
            
        except Exception as e:
            logger.error(f"Error evaluating answer script: {e}")
            raise
    
    def _find_matching_question(
        self, question_number: int, extracted_questions: List[ExtractedQuestion]
    ) -> Optional[ExtractedQuestion]:
        """Find extracted question matching the scheme question number."""
        for eq in extracted_questions:
            if eq.question_number == question_number:
                return eq
        return None
    
    async def _evaluate_single_question(
        self,
        extracted_question: ExtractedQuestion,
        scheme_question: Question
    ) -> QuestionEvaluation:
        """
        Evaluate a single question against its scheme.
        
        Args:
            extracted_question: The student's answer
            scheme_question: The marking scheme for this question
            
        Returns:
            Question evaluation with concept breakdown
        """
        try:
            # Merge fragments if multiple
            student_answer = merge_fragmented_answers([
                fragment.fragment_text for fragment in extracted_question.fragments
            ])
            
            # Normalize text
            normalized_answer = normalize_text(student_answer)
            
            if not normalized_answer.strip():
                # Empty answer
                return QuestionEvaluation(
                    question_number=extracted_question.question_number,
                    score=0.0,
                    max_score=scheme_question.max_marks,
                    concept_breakdown=[],
                    overall_confidence=1.0,
                    needs_review=False,
                    review_reasons=["Empty answer"]
                )
            
            # Evaluate each concept
            concept_evaluations = []
            total_concept_score = 0.0
            confidence_scores = []
            
            for concept in scheme_question.concepts:
                concept_eval = await self._evaluate_concept(
                    normalized_answer, concept
                )
                concept_evaluations.append(concept_eval)
                total_concept_score += concept_eval.marks_awarded
                confidence_scores.append(concept_eval.confidence)
            
            # Calculate overall confidence
            overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
            
            # Determine if this question needs review
            needs_review = (
                overall_confidence < self.confidence_threshold or
                extracted_question.has_duplicates or
                not extracted_question.is_complete or
                extracted_question.confidence < 0.6
            )
            
            review_reasons = []
            if overall_confidence < self.confidence_threshold:
                review_reasons.append("Low evaluation confidence")
            if extracted_question.has_duplicates:
                review_reasons.append("Duplicate content detected")
            if not extracted_question.is_complete:
                review_reasons.append("Incomplete answer detected")
            if extracted_question.confidence < 0.6:
                review_reasons.append("Poor OCR quality")
            
            return QuestionEvaluation(
                question_number=extracted_question.question_number,
                score=min(total_concept_score, scheme_question.max_marks),  # Cap at max marks
                max_score=scheme_question.max_marks,
                concept_breakdown=concept_evaluations,
                overall_confidence=overall_confidence,
                needs_review=needs_review,
                review_reasons=review_reasons
            )
            
        except Exception as e:
            logger.error(f"Error evaluating question {extracted_question.question_number}: {e}")
            # Return zero score evaluation on error
            return QuestionEvaluation(
                question_number=extracted_question.question_number,
                score=0.0,
                max_score=scheme_question.max_marks,
                concept_breakdown=[],
                overall_confidence=0.0,
                needs_review=True,
                review_reasons=["Evaluation error occurred"]
            )
    
    async def _evaluate_concept(
        self,
        student_answer: str,
        concept: Concept
    ) -> ConceptEvaluation:
        """
        Evaluate how well the student answer addresses a specific concept.
        
        Args:
            student_answer: The student's normalized answer text
            concept: The concept from the marking scheme
            
        Returns:
            Concept evaluation with similarity score and marks
        """
        try:
            # Create concept description from keywords
            concept_text = f"{concept.concept}. Key terms: {', '.join(concept.keywords)}"
            
            # Calculate semantic similarity
            similarity = calculate_semantic_similarity(student_answer, concept_text)
            
            # Check for keyword presence (gives bonus to similarity)
            keyword_bonus = self._calculate_keyword_bonus(student_answer, concept.keywords)
            
            # Combine similarity with keyword bonus
            final_similarity = min(1.0, similarity + keyword_bonus)
            
            # Calculate marks based on similarity
            if final_similarity < self.min_similarity_for_marks:
                marks_awarded = 0.0
                confidence = 0.8  # Confident it's not there
            else:
                # Scale marks based on similarity
                marks_ratio = self._similarity_to_marks_ratio(final_similarity)
                marks_awarded = concept.marks_allocation * marks_ratio
                confidence = min(0.95, 0.5 + final_similarity * 0.5)  # Higher similarity = higher confidence
            
            # Generate reasoning
            reasoning = self._generate_concept_reasoning(
                concept.concept, final_similarity, marks_awarded, concept.marks_allocation
            )
            
            return ConceptEvaluation(
                concept=concept.concept,
                similarity_score=final_similarity,
                marks_awarded=marks_awarded,
                max_marks=concept.marks_allocation,
                confidence=confidence,
                reasoning=reasoning
            )
            
        except Exception as e:
            logger.error(f"Error evaluating concept '{concept.concept}': {e}")
            return ConceptEvaluation(
                concept=concept.concept,
                similarity_score=0.0,
                marks_awarded=0.0,
                max_marks=concept.marks_allocation,
                confidence=0.0,
                reasoning=f"Error evaluating concept: {str(e)}"
            )
    
    def _calculate_keyword_bonus(self, text: str, keywords: List[str]) -> float:
        """Calculate bonus similarity for keyword matches."""
        text_lower = text.lower()
        matched_keywords = sum(1 for keyword in keywords if keyword.lower() in text_lower)
        
        if not keywords:
            return 0.0
        
        # Bonus up to 0.2 for keyword matches
        return min(0.2, (matched_keywords / len(keywords)) * 0.2)
    
    def _similarity_to_marks_ratio(self, similarity: float) -> float:
        """Convert similarity score to marks ratio using a curved scale."""
        # Non-linear scaling to reward higher similarities
        if similarity < 0.3:
            return 0.0
        elif similarity < 0.5:
            return 0.2  # 20% marks for basic understanding
        elif similarity < 0.7:
            return 0.5  # 50% marks for moderate understanding
        elif similarity < 0.85:
            return 0.75  # 75% marks for good understanding
        else:
            return 1.0  # Full marks for excellent understanding
    
    def _generate_concept_reasoning(
        self, concept: str, similarity: float, awarded: float, max_marks: float
    ) -> str:
        """Generate human-readable reasoning for concept evaluation."""
        percentage = (awarded / max_marks * 100) if max_marks > 0 else 0
        
        if similarity < 0.3:
            return f"No clear evidence of understanding '{concept}' concept."
        elif similarity < 0.5:
            return f"Basic mention of '{concept}' concept detected. Limited understanding shown. ({percentage:.0f}% of marks)"
        elif similarity < 0.7:
            return f"Moderate understanding of '{concept}' concept demonstrated. ({percentage:.0f}% of marks)"
        elif similarity < 0.85:
            return f"Good understanding of '{concept}' concept with relevant details. ({percentage:.0f}% of marks)"
        else:
            return f"Excellent understanding of '{concept}' concept with comprehensive explanation. ({percentage:.0f}% of marks)"
    
    def _check_review_requirements(
        self,
        question_scores: List[QuestionEvaluation],
        percentage: float,
        passing_marks: float
    ) -> Tuple[bool, List[ReviewReason]]:
        """Check if the evaluation requires manual review."""
        reasons = []
        
        # Check if any question needs review
        if any(q.needs_review for q in question_scores):
            reasons.append(ReviewReason.LOW_CONFIDENCE)
        
        # Check if below passing marks
        if percentage < passing_marks:
            reasons.append(ReviewReason.BELOW_PASSING)
        
        # Check for OCR quality issues
        avg_confidence = sum(q.overall_confidence for q in question_scores) / len(question_scores) if question_scores else 0
        if avg_confidence < 0.6:
            reasons.append(ReviewReason.OCR_ERRORS)
        
        return len(reasons) > 0, reasons
    
    async def recalculate_scores_after_manual_review(
        self,
        original_result: EvaluationResult,
        manual_adjustments: Dict[int, Dict]
    ) -> EvaluationResult:
        """
        Recalculate scores after manual review adjustments.
        
        Args:
            original_result: The original AI evaluation
            manual_adjustments: Manual adjustments per question
            
        Returns:
            Updated evaluation result
        """
        try:
            updated_questions = []
            total_score = 0.0
            
            for q_eval in original_result.question_scores:
                if q_eval.question_number in manual_adjustments:
                    adjustment = manual_adjustments[q_eval.question_number]
                    
                    # Apply manual override
                    updated_q = QuestionEvaluation(
                        question_number=q_eval.question_number,
                        score=adjustment.get('score', q_eval.score),
                        max_score=q_eval.max_score,
                        concept_breakdown=q_eval.concept_breakdown,  # Keep original breakdown
                        overall_confidence=1.0,  # Manual review = high confidence
                        needs_review=False,
                        review_reasons=[]
                    )
                    updated_questions.append(updated_q)
                    total_score += updated_q.score
                else:
                    updated_questions.append(q_eval)
                    total_score += q_eval.score
            
            # Recalculate percentage
            percentage = (total_score / original_result.max_possible_score * 100) if original_result.max_possible_score > 0 else 0
            
            # Create updated result
            updated_result = EvaluationResult(
                id=original_result.id,
                script_id=original_result.script_id,
                session_id=original_result.session_id,
                total_score=total_score,
                max_possible_score=original_result.max_possible_score,
                percentage=percentage,
                question_scores=updated_questions,
                requires_manual_review=False,  # Review completed
                review_reasons=[],
                evaluated_at=original_result.evaluated_at,
                manual_override=manual_adjustments
            )
            
            return updated_result
            
        except Exception as e:
            logger.error(f"Error recalculating scores after manual review: {e}")
            raise