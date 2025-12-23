# Tutorial 02: Document Formats and Data Models

Welcome to Tutorial 02! In this guide, you'll learn how we structure data and parse documents.

---

## What You'll Learn

- How to use **Pydantic** for data validation
- Creating **data models** for questions and evaluations
- Parsing documents (TXT, PDF, DOCX)
- Extracting Q&A pairs automatically

---

## Understanding Data Models

### What is a Data Model?

Think of a data model as a **blueprint** for your data. It defines:
- What fields exist (e.g., question text, answer, score)
- What type each field is (string, number, date)
- What rules the data must follow (e.g., score must be positive)

### Why Use Pydantic?

**Pydantic** is a Python library that makes data validation easy:

```python
from pydantic import BaseModel

class Person(BaseModel):
    name: str
    age: int

# This works ✅
person = Person(name="Alice", age=25)

# This fails ❌ (age must be a number)
person = Person(name="Bob", age="twenty")  # ValidationError!
```

Pydantic automatically:
- Checks data types
- Validates values
- Provides helpful error messages
- Converts data when possible

---

## Our Data Models

We have four main models in `src/models.py`:

### 1. Question Model

Represents a single question with its answer:

```python
class Question(BaseModel):
    id: str                    # Unique identifier (e.g., "q1")
    text: str                  # Question text
    question_type: QuestionType  # Type of question
    reference_answer: Optional[str]  # Expected answer (optional)
    user_answer: str           # User's answer
    max_score: float           # Maximum points
    topic: Optional[str]       # Subject area
```

**Example:**
```python
question = Question(
    id="q1",
    text="What is Python?",
    question_type=QuestionType.SHORT_ANSWER,
    reference_answer="A high-level programming language",
    user_answer="A programming language",
    max_score=10.0,
    topic="Programming Basics"
)
```

### 2. Evaluation Model

Stores the AI's evaluation of an answer:

```python
class Evaluation(BaseModel):
    question_id: str           # Which question this evaluates
    score: float               # Points awarded
    confidence: float          # AI confidence (0.0 to 1.0)
    explanation: str           # Why this score?
    is_correct: bool           # Correct or not?
    needs_human_review: bool   # Should a human check this?
```

**Key Concept: Confidence Score**

The confidence score tells us how sure the AI is:
- **0.9 - 1.0**: Very confident → Proceed automatically
- **0.7 - 0.9**: Moderately confident → Probably OK
- **Below 0.7**: Low confidence → Ask human for help!

### 3. Assessment Model

A collection of questions and their evaluations:

```python
class Assessment(BaseModel):
    id: str
    title: str
    questions: List[Question]
    evaluations: List[Evaluation]
    total_score: float
    max_possible_score: float
    percentage: float
```

This model has helper methods:
- `calculate_scores()`: Computes total score and percentage
- `get_questions_needing_review()`: Finds questions needing human input

### 4. Report Model

The final assessment report:

```python
class Report(BaseModel):
    assessment_id: str
    summary: str
    strengths: List[StrengthWeakness]
    weaknesses: List[StrengthWeakness]
    recommendations: List[str]
    statistics: dict
```

---

## Document Parsing

### Supported Formats

Our parser supports three formats:

| Format | Extension | Use Case                     |
| ------ | --------- | ---------------------------- |
| Text   | `.txt`    | Simple, easy to create       |
| PDF    | `.pdf`    | Scanned documents, printouts |
| Word   | `.docx`   | Formatted documents          |

### Expected Document Structure

Documents should follow this format:

```
Q: Question text here?
Expected: Reference answer (optional)
A: User's answer here

Q: Another question?
A: Another answer
```

**Example:**

```
Q: What is Python?
Expected: Python is a high-level programming language
A: Python is a programming language

Q: What is 2 + 2?
A: 4

Q: True or False: Python is compiled
A: False
```

### How the Parser Works

The `DocumentParser` class does three things:

#### Step 1: Read the File

Different file types need different readers:

```python
# TXT files - simple
with open(path, 'r') as f:
    text = f.read()

# PDF files - extract text from pages
pdf_reader = PyPDF2.PdfReader(file)
for page in pdf_reader.pages:
    text += page.extract_text()

# DOCX files - extract paragraphs
doc = Document(path)
text = "\n".join([p.text for p in doc.paragraphs])
```

#### Step 2: Extract Q&A Pairs

We use **regular expressions** (regex) to find patterns:

```python
# Pattern: Q: ... [Expected: ...] A: ...
pattern = r'Q:\s*(.+?)(?:Expected:\s*(.+?))?\s*A:\s*(.+?)(?=Q:|$)'
matches = re.findall(pattern, text, re.DOTALL)
```

**What this means:**
- `Q:\s*(.+?)` - Find "Q:" followed by question text
- `(?:Expected:\s*(.+?))?` - Optionally find "Expected:" with answer
- `A:\s*(.+?)` - Find "A:" followed by answer text
- `(?=Q:|$)` - Stop at next "Q:" or end of file

#### Step 3: Detect Question Type

The parser automatically detects question types:

```python
def _detect_question_type(question_text, answer_text):
    # True/False questions
    if 'true or false' in question_text.lower():
        return QuestionType.TRUE_FALSE
    
    # Coding questions
    if 'def ' in answer_text or 'function' in answer_text:
        return QuestionType.CODING
    
    # Essay (long answers)
    if len(answer_text.split()) > 100:
        return QuestionType.ESSAY
    
    # Default: short answer
    return QuestionType.SHORT_ANSWER
```

---

## Testing the Models

Let's test our models:

```bash
# Test the models
python src/models.py

# Test the parser
python src/document_parser.py
```

You should see:
```
✅ Models validated successfully!
✅ Parsed 4 questions
```

---

## Creating Your Own Test Document

Create a file `my_test.txt`:

```
Q: What is your name?
A: My name is Alice

Q: What is 10 + 5?
Expected: 15
A: 15

Q: True or False: The Earth is flat
A: False
```

Then parse it:

```python
from src.document_parser import DocumentParser

parser = DocumentParser()
questions = parser.parse_file('my_test.txt')

for q in questions:
    print(f"Q: {q.text}")
    print(f"A: {q.user_answer}")
    print(f"Type: {q.question_type.value}")
    print()
```

---

## Key Concepts Explained

### 1. Type Hints

Python type hints tell you what type a variable should be:

```python
name: str = "Alice"        # String
age: int = 25              # Integer
score: float = 98.5        # Decimal number
is_correct: bool = True    # True/False
items: List[str] = ["a", "b"]  # List of strings
```

### 2. Optional Values

`Optional[str]` means "can be a string OR None":

```python
from typing import Optional

# This is OK
reference: Optional[str] = "Expected answer"

# This is also OK
reference: Optional[str] = None
```

### 3. Enums

Enums define a fixed set of choices:

```python
class QuestionType(str, Enum):
    SHORT_ANSWER = "short_answer"
    LONG_ANSWER = "long_answer"
    CODING = "coding"

# Can only use defined values
type = QuestionType.SHORT_ANSWER  # ✅
type = "random_type"  # ❌ Not allowed
```

### 4. Regular Expressions (Regex)

Regex finds patterns in text:

```python
import re

text = "Q: What is Python? A: A language"

# Find all questions
questions = re.findall(r'Q: (.+?) A:', text)
# Result: ['What is Python?']
```

**Common regex symbols:**
- `.` = any character
- `+` = one or more
- `*` = zero or more
- `?` = optional
- `\s` = whitespace

---

## Common Issues

### Issue: "ValidationError: Field required"

**Problem:** Missing required field

**Solution:** Make sure all required fields are provided:
```python
# Missing 'text' field ❌
question = Question(id="q1", user_answer="answer")

# All required fields ✅
question = Question(
    id="q1",
    text="Question?",
    user_answer="answer"
)
```

### Issue: "No Q&A pairs found"

**Problem:** Document format doesn't match expected pattern

**Solution:** Check your document format:
- Use `Q:` for questions
- Use `A:` for answers
- Make sure there's a space after the colon

### Issue: "Error reading PDF"

**Problem:** PDF might be encrypted or corrupted

**Solution:** 
- Try converting to TXT first
- Check if PDF opens normally
- Use a different PDF

---

## Testing Your Understanding

Try these exercises:

1. **Create a Question**: Make a Question object with all fields
2. **Parse a Document**: Create a TXT file and parse it
3. **Modify Detection**: Change the question type detection logic
4. **Add Validation**: Add a validator to ensure scores are not negative

---

## Next Steps

Great! You now understand:
- ✅ Data models with Pydantic
- ✅ Document parsing
- ✅ Q&A extraction

Next, we'll build the **AI Evaluation Engine** that uses OpenAI to evaluate answers!

Continue to: **[Tutorial 03: AI Evaluation](03_ai_evaluation.md)**

---

## Quick Reference

### Creating a Question
```python
from src.models import Question, QuestionType

q = Question(
    id="q1",
    text="What is AI?",
    question_type=QuestionType.SHORT_ANSWER,
    user_answer="Artificial Intelligence",
    max_score=10.0
)
```

### Parsing a Document
```python
from src.document_parser import DocumentParser

parser = DocumentParser()
questions = parser.parse_file('path/to/file.txt')
```

### Parsing Text Directly
```python
text = """
Q: Question?
A: Answer
"""
questions = parser.parse_text_directly(text)
```
