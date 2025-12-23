"""
Unit tests for document parser.
"""

import pytest
from pathlib import Path
from src.document_parser import DocumentParser
from src.models import QuestionType


class TestDocumentParser:
    """Tests for DocumentParser."""
    
    @pytest.fixture
    def parser(self):
        """Create a parser instance."""
        return DocumentParser()
    
    def test_parse_simple_text(self, parser):
        """Test parsing simple Q&A text."""
        text = """
Q: What is Python?
A: A programming language

Q: What is 2+2?
A: 4
"""
        questions = parser.parse_text_directly(text)
        
        assert len(questions) == 2
        assert questions[0].text == "What is Python?"
        assert questions[0].user_answer == "A programming language"
        assert questions[1].text == "What is 2+2?"
        assert questions[1].user_answer == "4"
    
    def test_parse_with_reference_answer(self, parser):
        """Test parsing with reference answers."""
        text = """
Q: What is Python?
Expected: A high-level programming language
A: A programming language
"""
        questions = parser.parse_text_directly(text)
        
        assert len(questions) == 1
        assert questions[0].reference_answer == "A high-level programming language"
    
    def test_detect_true_false(self, parser):
        """Test detection of True/False questions."""
        text = """
Q: Python is a compiled language. True or False?
A: False
"""
        questions = parser.parse_text_directly(text)
        
        assert len(questions) == 1
        assert questions[0].question_type == QuestionType.TRUE_FALSE
    
    def test_detect_multiple_choice(self, parser):
        """Test detection of multiple choice questions."""
        text = """
Q: What is Python? (a) Language (b) Snake (c) Framework
A: a
"""
        questions = parser.parse_text_directly(text)
        
        assert len(questions) == 1
        assert questions[0].question_type == QuestionType.MULTIPLE_CHOICE
    
    def test_detect_coding_question(self, parser):
        """Test detection of coding questions."""
        text = """
Q: Write a function to add two numbers
A: def add(a, b): return a + b
"""
        questions = parser.parse_text_directly(text)
        
        assert len(questions) == 1
        assert questions[0].question_type == QuestionType.CODING
    
    def test_empty_text(self, parser):
        """Test parsing empty text."""
        questions = parser.parse_text_directly("")
        assert len(questions) == 0
    
    def test_no_questions(self, parser):
        """Test text with no questions."""
        text = "This is just some random text without questions."
        questions = parser.parse_text_directly(text)
        assert len(questions) == 0
    
    def test_parse_file(self, parser, tmp_path):
        """Test parsing from file."""
        # Create temporary file
        test_file = tmp_path / "test.txt"
        test_file.write_text("""
Q: Test question?
A: Test answer
""")
        
        questions = parser.parse_file(str(test_file))
        
        assert len(questions) == 1
        assert questions[0].text == "Test question?"
    
    def test_unsupported_file_type(self, parser):
        """Test unsupported file type."""
        with pytest.raises(ValueError, match="Unsupported file type"):
            parser.parse_file("test.xyz")
    
    def test_max_score_assignment(self, parser):
        """Test max score assignment based on question type."""
        text = """
Q: True or False question?
A: True

Q: Write an essay about Python
A: Python is a great language...
"""
        questions = parser.parse_text_directly(text)
        
        # True/False should have lower max score
        assert questions[0].max_score <= questions[1].max_score
