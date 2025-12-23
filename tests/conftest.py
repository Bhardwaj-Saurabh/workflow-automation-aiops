"""
Shared test fixtures and configuration.
"""

import pytest
import os


@pytest.fixture(scope="session")
def mock_openai_key():
    """Provide a mock OpenAI API key for testing."""
    original_key = os.getenv("OPENAI_API_KEY")
    os.environ["OPENAI_API_KEY"] = "sk-test-key-for-testing"
    yield "sk-test-key-for-testing"
    if original_key:
        os.environ["OPENAI_API_KEY"] = original_key
    else:
        os.environ.pop("OPENAI_API_KEY", None)


@pytest.fixture
def sample_questions():
    """Provide sample questions for testing."""
    from src.models import Question, QuestionType
    
    return [
        Question(
            id="q1",
            text="What is Python?",
            question_type=QuestionType.SHORT_ANSWER,
            user_answer="A programming language",
            reference_answer="A high-level programming language",
            max_score=10.0
        ),
        Question(
            id="q2",
            text="What is 2+2?",
            question_type=QuestionType.SHORT_ANSWER,
            user_answer="4",
            reference_answer="4",
            max_score=5.0
        )
    ]


@pytest.fixture
def sample_evaluations():
    """Provide sample evaluations for testing."""
    from src.models import Evaluation
    
    return [
        Evaluation(
            question_id="q1",
            score=8.0,
            confidence=0.85,
            explanation="Good answer with correct concept",
            is_correct=True
        ),
        Evaluation(
            question_id="q2",
            score=5.0,
            confidence=0.95,
            explanation="Correct answer",
            is_correct=True
        )
    ]
