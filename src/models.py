"""
Data models for the AI Assessment Evaluation System.

This module defines the core data structures using Pydantic for validation:
- Question: Represents a single question with reference and user answers
- Evaluation: AI's evaluation of an answer with confidence and explanation
- Assessment: Collection of questions and their evaluations
- Report: Final assessment report with analysis
"""

from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class QuestionType(str, Enum):
    """Types of questions that can be evaluated."""
    MULTIPLE_CHOICE = "multiple_choice"
    SHORT_ANSWER = "short_answer"
    LONG_ANSWER = "long_answer"
    TRUE_FALSE = "true_false"
    CODING = "coding"
    ESSAY = "essay"


class EvaluationStatus(str, Enum):
    """Status of an evaluation."""
    PENDING = "pending"
    AI_EVALUATED = "ai_evaluated"
    HUMAN_REVIEWED = "human_reviewed"
    COMPLETED = "completed"


class Question(BaseModel):
    """
    Represents a single question with its answers.
    
    Attributes:
        id: Unique identifier for the question
        text: The question text
        question_type: Type of question (multiple choice, short answer, etc.)
        reference_answer: Expected/correct answer (optional)
        user_answer: Answer provided by the user
        max_score: Maximum points for this question
        topic: Subject area or topic (optional)
    """
    id: str = Field(..., description="Unique question identifier")
    text: str = Field(..., min_length=1, description="Question text")
    question_type: QuestionType = Field(default=QuestionType.SHORT_ANSWER)
    reference_answer: Optional[str] = Field(None, description="Expected answer")
    user_answer: str = Field(..., min_length=1, description="User's answer")
    max_score: float = Field(default=1.0, gt=0, description="Maximum points")
    topic: Optional[str] = Field(None, description="Question topic/category")
    
    @field_validator('user_answer', 'text')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Ensure text fields are not just whitespace."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or whitespace")
        return v.strip()


class Evaluation(BaseModel):
    """
    AI's evaluation of a question answer.
    
    Attributes:
        question_id: Reference to the question being evaluated
        score: Points awarded (0 to max_score)
        confidence: AI's confidence in this evaluation (0.0 to 1.0)
        explanation: Detailed explanation of the evaluation
        is_correct: Whether the answer is considered correct
        needs_human_review: Flag indicating if human review is needed
        status: Current status of the evaluation
        evaluated_at: Timestamp of evaluation
        reviewed_by_human: Whether a human has reviewed this
        human_override_score: Score set by human reviewer (if any)
        human_notes: Additional notes from human reviewer
    """
    question_id: str = Field(..., description="Question identifier")
    score: float = Field(..., ge=0, description="Points awarded")
    confidence: float = Field(..., ge=0.0, le=1.0, description="AI confidence score")
    explanation: str = Field(..., min_length=1, description="Evaluation explanation")
    is_correct: bool = Field(..., description="Whether answer is correct")
    needs_human_review: bool = Field(default=False, description="Needs human validation")
    status: EvaluationStatus = Field(default=EvaluationStatus.AI_EVALUATED)
    evaluated_at: datetime = Field(default_factory=datetime.now)
    reviewed_by_human: bool = Field(default=False)
    human_override_score: Optional[float] = Field(None, ge=0)
    human_notes: Optional[str] = Field(None)
    
    @field_validator('needs_human_review', mode='before')
    @classmethod
    def check_confidence_threshold(cls, v, info):
        """Automatically flag for review if confidence is low."""
        confidence = info.data.get('confidence', 1.0)
        if confidence < 0.7:  # Threshold can be configured
            return True
        return v


class StrengthWeakness(BaseModel):
    """
    Analysis of strengths or weaknesses.
    
    Attributes:
        category: Topic or skill category
        description: Detailed description
        evidence: Supporting evidence from answers
        score_impact: Impact on overall score
    """
    category: str = Field(..., description="Category name")
    description: str = Field(..., description="Detailed description")
    evidence: List[str] = Field(default_factory=list, description="Supporting evidence")
    score_impact: Optional[float] = Field(None, description="Impact on score")


class Assessment(BaseModel):
    """
    Complete assessment with questions and evaluations.
    
    Attributes:
        id: Unique assessment identifier
        title: Assessment title
        questions: List of questions
        evaluations: List of evaluations (one per question)
        created_at: When assessment was created
        completed_at: When assessment was completed
        total_score: Total points earned
        max_possible_score: Maximum possible points
        percentage: Score as percentage
    """
    id: str = Field(..., description="Assessment identifier")
    title: str = Field(default="Untitled Assessment", description="Assessment title")
    questions: List[Question] = Field(default_factory=list)
    evaluations: List[Evaluation] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = Field(None)
    total_score: float = Field(default=0.0, ge=0)
    max_possible_score: float = Field(default=0.0, ge=0)
    percentage: float = Field(default=0.0, ge=0, le=100)
    
    def calculate_scores(self) -> None:
        """Calculate total score and percentage."""
        self.max_possible_score = sum(q.max_score for q in self.questions)
        
        # Use human override scores if available, otherwise use AI scores
        self.total_score = sum(
            eval.human_override_score if eval.human_override_score is not None 
            else eval.score 
            for eval in self.evaluations
        )
        
        if self.max_possible_score > 0:
            self.percentage = (self.total_score / self.max_possible_score) * 100
        else:
            self.percentage = 0.0
    
    def get_questions_needing_review(self) -> List[Question]:
        """Get questions that need human review."""
        review_ids = {
            eval.question_id 
            for eval in self.evaluations 
            if eval.needs_human_review and not eval.reviewed_by_human
        }
        return [q for q in self.questions if q.id in review_ids]


class Report(BaseModel):
    """
    Final assessment report with analysis.
    
    Attributes:
        assessment_id: Reference to the assessment
        generated_at: When report was generated
        summary: Executive summary
        strengths: Identified strengths
        weaknesses: Areas for improvement
        recommendations: Actionable recommendations
        detailed_results: Question-by-question breakdown
        statistics: Statistical summary
    """
    assessment_id: str = Field(..., description="Assessment identifier")
    generated_at: datetime = Field(default_factory=datetime.now)
    summary: str = Field(..., description="Executive summary")
    strengths: List[StrengthWeakness] = Field(default_factory=list)
    weaknesses: List[StrengthWeakness] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    detailed_results: dict = Field(default_factory=dict)
    statistics: dict = Field(default_factory=dict)
    
    def to_markdown(self) -> str:
        """Convert report to markdown format."""
        md = f"# Assessment Report\n\n"
        md += f"**Generated**: {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        md += f"## Summary\n\n{self.summary}\n\n"
        
        if self.strengths:
            md += "## Strengths\n\n"
            for strength in self.strengths:
                md += f"### {strength.category}\n"
                md += f"{strength.description}\n\n"
        
        if self.weaknesses:
            md += "## Areas for Improvement\n\n"
            for weakness in self.weaknesses:
                md += f"### {weakness.category}\n"
                md += f"{weakness.description}\n\n"
        
        if self.recommendations:
            md += "## Recommendations\n\n"
            for i, rec in enumerate(self.recommendations, 1):
                md += f"{i}. {rec}\n"
        
        return md


# Example usage and validation
if __name__ == "__main__":
    # Create a sample question
    question = Question(
        id="q1",
        text="What is Python?",
        question_type=QuestionType.SHORT_ANSWER,
        reference_answer="Python is a high-level programming language",
        user_answer="Python is a programming language",
        max_score=10.0,
        topic="Programming Basics"
    )
    
    # Create an evaluation
    evaluation = Evaluation(
        question_id="q1",
        score=8.0,
        confidence=0.85,
        explanation="Answer is mostly correct but lacks detail about 'high-level'",
        is_correct=True,
        needs_human_review=False
    )
    
    print("✅ Models validated successfully!")
    print(f"Question: {question.text}")
    print(f"Score: {evaluation.score}/{question.max_score}")
    print(f"Confidence: {evaluation.confidence}")
