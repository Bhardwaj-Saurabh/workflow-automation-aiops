"""
Document parser for extracting questions and answers from various file formats.

Supports:
- TXT: Simple text format with Q: and A: markers
- PDF: Extracts text and parses Q&A pairs
- DOCX: Extracts from Word documents

For beginners: This module shows how to work with different file formats
and extract structured data from unstructured text.
"""

import re
import uuid
from typing import List, Tuple, Optional
from pathlib import Path
import PyPDF2
from docx import Document

from src.models import Question, QuestionType


class DocumentParser:
    """
    Parses documents to extract question-answer pairs.
    
    This class handles multiple file formats and converts them into
    structured Question objects that our AI can evaluate.
    """
    
    def __init__(self):
        """Initialize the document parser."""
        self.supported_formats = ['.txt', '.pdf', '.docx']
    
    def parse_file(self, file_path: str) -> List[Question]:
        """
        Parse a file and extract questions.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            List of Question objects
            
        Raises:
            ValueError: If file format is not supported
            FileNotFoundError: If file doesn't exist
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        extension = path.suffix.lower()
        
        if extension not in self.supported_formats:
            raise ValueError(
                f"Unsupported file format: {extension}. "
                f"Supported formats: {', '.join(self.supported_formats)}"
            )
        
        # Extract text based on file type
        if extension == '.txt':
            text = self._read_txt(path)
        elif extension == '.pdf':
            text = self._read_pdf(path)
        elif extension == '.docx':
            text = self._read_docx(path)
        else:
            raise ValueError(f"Unsupported format: {extension}")
        
        # Parse Q&A pairs from text
        questions = self._extract_qa_pairs(text)
        
        return questions
    
    def _read_txt(self, path: Path) -> str:
        """
        Read text from a TXT file.
        
        Args:
            path: Path to TXT file
            
        Returns:
            File contents as string
        """
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _read_pdf(self, path: Path) -> str:
        """
        Extract text from a PDF file.
        
        Args:
            path: Path to PDF file
            
        Returns:
            Extracted text
        """
        text = ""
        try:
            with open(path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            raise ValueError(f"Error reading PDF: {str(e)}")
        
        return text
    
    def _read_docx(self, path: Path) -> str:
        """
        Extract text from a DOCX file.
        
        Args:
            path: Path to DOCX file
            
        Returns:
            Extracted text
        """
        try:
            doc = Document(path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        except Exception as e:
            raise ValueError(f"Error reading DOCX: {str(e)}")
        
        return text
    
    def _extract_qa_pairs(self, text: str) -> List[Question]:
        """
        Extract question-answer pairs from text.
        
        Expected format:
            Q: Question text here?
            A: Answer text here.
            
            Q: Another question?
            A: Another answer.
        
        Or with reference answers:
            Q: Question text?
            Expected: Reference answer
            A: User's answer
        
        Args:
            text: Document text
            
        Returns:
            List of Question objects
        """
        questions = []
        
        # Pattern to match Q&A pairs with optional reference answer
        # This regex finds: Q: ... [Expected: ...] A: ...
        pattern = r'Q:\s*(.+?)(?:Expected:\s*(.+?))?\s*A:\s*(.+?)(?=Q:|$)'
        
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        
        for i, match in enumerate(matches, 1):
            question_text = match[0].strip()
            reference_answer = match[1].strip() if match[1] else None
            user_answer = match[2].strip()
            
            if not question_text or not user_answer:
                continue  # Skip invalid pairs
            
            # Detect question type based on content
            question_type = self._detect_question_type(question_text, user_answer)
            
            question = Question(
                id=f"q{i}",
                text=question_text,
                question_type=question_type,
                reference_answer=reference_answer,
                user_answer=user_answer,
                max_score=10.0,  # Default score, can be customized
                topic=None  # Can be extracted or set later
            )
            
            questions.append(question)
        
        return questions
    
    def _detect_question_type(self, question_text: str, answer_text: str) -> QuestionType:
        """
        Detect the type of question based on content.
        
        Args:
            question_text: The question
            answer_text: The answer
            
        Returns:
            QuestionType enum value
        """
        question_lower = question_text.lower()
        answer_lower = answer_text.lower()
        
        # True/False detection
        if any(word in question_lower for word in ['true or false', 't/f', 'true/false']):
            return QuestionType.TRUE_FALSE
        
        if answer_lower in ['true', 'false', 't', 'f']:
            return QuestionType.TRUE_FALSE
        
        # Multiple choice detection
        if any(char in question_text for char in ['A)', 'B)', 'C)', 'D)']):
            return QuestionType.MULTIPLE_CHOICE
        
        # Coding detection
        if any(keyword in answer_lower for keyword in ['def ', 'function', 'class ', 'import ', 'return']):
            return QuestionType.CODING
        
        # Essay detection (long answers)
        if len(answer_text.split()) > 100:
            return QuestionType.ESSAY
        
        # Long answer detection
        if len(answer_text.split()) > 30:
            return QuestionType.LONG_ANSWER
        
        # Default to short answer
        return QuestionType.SHORT_ANSWER
    
    def parse_text_directly(self, text: str, title: str = "Direct Input") -> List[Question]:
        """
        Parse Q&A pairs directly from text string.
        
        Useful for testing or when text is already extracted.
        
        Args:
            text: Text containing Q&A pairs
            title: Title for this set of questions
            
        Returns:
            List of Question objects
        """
        return self._extract_qa_pairs(text)


# Example usage and testing
if __name__ == "__main__":
    # Create a sample text for testing
    sample_text = """
    Q: What is Python?
    Expected: Python is a high-level, interpreted programming language
    A: Python is a programming language
    
    Q: What is 2 + 2?
    A: 4
    
    Q: True or False: Python is compiled
    A: False
    
    Q: Write a function to add two numbers
    A: def add(a, b):
        return a + b
    """
    
    parser = DocumentParser()
    questions = parser.parse_text_directly(sample_text)
    
    print(f"✅ Parsed {len(questions)} questions:\n")
    for q in questions:
        print(f"ID: {q.id}")
        print(f"Type: {q.question_type.value}")
        print(f"Question: {q.text[:50]}...")
        print(f"Answer: {q.user_answer[:50]}...")
        if q.reference_answer:
            print(f"Expected: {q.reference_answer[:50]}...")
        print("-" * 50)
