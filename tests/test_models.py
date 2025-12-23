"""
Unit tests for data models.
"""

import pytest
from src.models import (
    Question, QuestionType, Evaluation, EvaluationStatus,
    Assessment, Report, PerformanceArea
)


class TestQuestion:
    """Tests for Question model."""
    
    def test_create_question(self):
        """Test creating a basic question."""
        q = Question(
            id="q1",
            text="What is Python?",
            question_type=QuestionType.SHORT_ANSWER,
            user_answer="A programming language",
            max_score=10.0
        )
        
        assert q.id == "q1"
        assert q.text == "What is Python?"
        assert q.question_type == QuestionType.SHORT_ANSWER
        assert q.max_score == 10.0
    
    def test_question_with_reference(self):
        """Test question with reference answer."""
        q = Question(
            id="q2",
            text="What is 2+2?",
            question_type=QuestionType.SHORT_ANSWER,
            user_answer="4",
            reference_answer="4",
            max_score=5.0
        )
        
        assert q.reference_answer == "4"
    
    def test_question_validation(self):
        """Test question validation."""
        with pytest.raises(ValueError):
            Question(
                id="q3",
                text="Test",
                question_type=QuestionType.SHORT_ANSWER,
                user_answer="Answer",
                max_score=-1.0  # Invalid: negative score
            )


class TestEvaluation:
    """Tests for Evaluation model."""
    
    def test_create_evaluation(self):
        """Test creating an evaluation."""
        e = Evaluation(
            question_id="q1",
            score=8.0,
            confidence=0.85,
            explanation="Good answer",
            is_correct=True
        )
        
        assert e.question_id == "q1"
        assert e.score == 8.0
        assert e.confidence == 0.85
        assert e.is_correct is True
        assert e.status == EvaluationStatus.AI_EVALUATED
    
    def test_needs_human_review(self):
        """Test automatic human review flagging."""
        e = Evaluation(
            question_id="q2",
            score=5.0,
            confidence=0.6,  # Low confidence
            explanation="Uncertain",
            is_correct=False,
            needs_human_review=True
        )
        
        assert e.needs_human_review is True
    
    def test_human_override(self):
        """Test human override functionality."""
        e = Evaluation(
            question_id="q3",
            score=5.0,
            confidence=0.7,
            explanation="AI evaluation",
            is_correct=False
        )
        
        # Apply human override
        e.human_override_score = 8.0
        e.human_notes = "Actually correct"
        e.reviewed_by_human = True
        e.status = EvaluationStatus.HUMAN_REVIEWED
        
        assert e.get_final_score() == 8.0
        assert e.reviewed_by_human is True


class TestAssessment:
    """Tests for Assessment model."""
    
    def test_create_assessment(self):
        """Test creating an assessment."""
        questions = [
            Question(
                id="q1",
                text="Question 1",
                question_type=QuestionType.SHORT_ANSWER,
                user_answer="Answer 1",
                max_score=10.0
            ),
            Question(
                id="q2",
                text="Question 2",
                question_type=QuestionType.SHORT_ANSWER,
                user_answer="Answer 2",
                max_score=10.0
            )
        ]
        
        evaluations = [
            Evaluation(
                question_id="q1",
                score=8.0,
                confidence=0.9,
                explanation="Good",
                is_correct=True
            ),
            Evaluation(
                question_id="q2",
                score=6.0,
                confidence=0.8,
                explanation="Okay",
                is_correct=True
            )
        ]
        
        assessment = Assessment(
            id="a1",
            title="Test Assessment",
            questions=questions,
            evaluations=evaluations
        )
        
        assessment.calculate_scores()
        
        assert assessment.total_score == 14.0
        assert assessment.max_possible_score == 20.0
        assert assessment.percentage == 70.0
    
    def test_empty_assessment(self):
        """Test assessment with no questions."""
        assessment = Assessment(
            id="a2",
            title="Empty",
            questions=[],
            evaluations=[]
        )
        
        assessment.calculate_scores()
        
        assert assessment.total_score == 0.0
        assert assessment.percentage == 0.0


class TestReport:
    """Tests for Report model."""
    
    def test_create_report(self):
        """Test creating a report."""
        report = Report(
            assessment_id="a1",
            summary="Good performance overall",
            strengths=[
                PerformanceArea(
                    category="Python Basics",
                    description="Strong understanding"
                )
            ],
            weaknesses=[
                PerformanceArea(
                    category="Advanced Topics",
                    description="Needs improvement"
                )
            ],
            recommendations=[
                "Study advanced Python features",
                "Practice more coding exercises"
            ],
            statistics={
                "total_questions": 10,
                "correct_count": 7,
                "total_score": 70.0,
                "percentage": 70.0
            }
        )
        
        assert report.assessment_id == "a1"
        assert len(report.strengths) == 1
        assert len(report.weaknesses) == 1
        assert len(report.recommendations) == 2
    
    def test_report_to_markdown(self):
        """Test markdown generation."""
        report = Report(
            assessment_id="a1",
            summary="Test summary",
            strengths=[],
            weaknesses=[],
            recommendations=["Recommendation 1"],
            statistics={"total_questions": 5}
        )
        
        markdown = report.to_markdown()
        
        assert "# Assessment Report" in markdown
        assert "Test summary" in markdown
        assert "Recommendation 1" in markdown
