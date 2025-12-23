# Tutorial 03: AI Evaluation with OpenAI

Welcome to Tutorial 03! Now we'll integrate AI to automatically evaluate answers.

---

## What You'll Learn

- How to use the **OpenAI API**
- **Prompt engineering** basics
- Confidence scoring and when to ask for human help
- Handling AI responses

---

## Understanding AI Evaluation

### What is OpenAI?

**OpenAI** provides powerful language models (like GPT-4) that can:
- Understand natural language
- Analyze text
- Make intelligent decisions
- Generate explanations

We use these models to evaluate student answers.

### How Does It Work?

```
1. We send a PROMPT (instructions + question + answer)
   ↓
2. OpenAI's AI model processes it
   ↓
3. AI returns an EVALUATION (score + explanation)
   ↓
4. We parse the response into structured data
```

---

## The AIEvaluator Class

Our `AIEvaluator` class in `src/ai_evaluator.py` handles everything:

```python
from src.ai_evaluator import AIEvaluator

# Create evaluator
evaluator = AIEvaluator()

# Evaluate a question
evaluation = evaluator.evaluate_answer(question)

print(f"Score: {evaluation.score}")
print(f"Confidence: {evaluation.confidence}")
print(f"Explanation: {evaluation.explanation}")
```

---

## Prompt Engineering

### What is a Prompt?

A **prompt** is the instruction you give to the AI. Quality of the prompt = quality of the result!

### Our Evaluation Prompt Structure

```
You are an expert evaluator...

Question Type: short_answer
Maximum Score: 10

Question: What is Python?
Expected Answer: A high-level programming language
Student's Answer: A programming language

[Type-specific instructions]

Please provide:
SCORE: [number]
CONFIDENCE: [0.0-1.0]
IS_CORRECT: [true/false]
EXPLANATION: [detailed feedback]
```

### Why This Structure Works

1. **Clear role**: "You are an expert evaluator"
2. **Context**: Question type, max score
3. **Data**: Question, expected answer, student answer
4. **Instructions**: How to evaluate this type
5. **Format**: Structured output we can parse

---

## Question Type-Specific Evaluation

Different question types need different evaluation strategies:

### True/False Questions

```python
# High confidence, no partial credit
SCORE: 10 or 0
CONFIDENCE: 0.95
IS_CORRECT: true
EXPLANATION: Answer is exactly correct.
```

### Short Answer Questions

```python
# Partial credit allowed
SCORE: 7
CONFIDENCE: 0.80
IS_CORRECT: true
EXPLANATION: Answer captures main concept but lacks detail.
```

### Essay Questions

```python
# Subjective, needs human review
SCORE: 15
CONFIDENCE: 0.60
IS_CORRECT: true
EXPLANATION: Good argument but subjective. Recommend human review.
```

---

## Confidence Scoring

### What is Confidence?

**Confidence** = How sure the AI is about its evaluation (0.0 to 1.0)

| Confidence | Meaning         | Action                |
| ---------- | --------------- | --------------------- |
| 0.9 - 1.0  | Very sure       | Auto-approve ✅        |
| 0.7 - 0.9  | Moderately sure | Probably OK ⚠️         |
| 0.0 - 0.7  | Uncertain       | Human review needed 👤 |

### When is Confidence Low?

- Ambiguous answers
- Subjective questions (essays)
- Unexpected responses
- Missing reference answer
- Complex coding questions

### The Confidence Threshold

```python
evaluator = AIEvaluator(confidence_threshold=0.7)

# If confidence < 0.7:
#   → needs_human_review = True
#   → Workflow pauses for human input
```

---

## Making API Calls

### Setting Up Your API Key

1. Get your key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. Add to `.env` file:
   ```
   OPENAI_API_KEY=sk-your-key-here
   ```
3. The code loads it automatically:
   ```python
   load_dotenv()  # Loads .env file
   api_key = os.getenv("OPENAI_API_KEY")
   ```

### The API Call

```python
response = client.chat.completions.create(
    model="gpt-4o-mini",  # Cost-effective model
    messages=[
        {
            "role": "system",
            "content": "You are an expert evaluator..."
        },
        {
            "role": "user",
            "content": prompt
        }
    ],
    temperature=0.3,  # Low = consistent, High = creative
    max_tokens=500    # Maximum response length
)
```

### Understanding Parameters

**model**: Which AI model to use
- `gpt-4o-mini`: Fast, cheap, good quality
- `gpt-4o`: More powerful, more expensive

**temperature**: Creativity level (0.0 - 2.0)
- `0.0 - 0.3`: Consistent, factual (good for grading)
- `0.7 - 1.0`: Creative, varied
- `1.0+`: Very creative, unpredictable

**max_tokens**: Response length limit
- 1 token ≈ 0.75 words
- 500 tokens ≈ 375 words

---

## Parsing AI Responses

The AI returns text like:

```
SCORE: 8
CONFIDENCE: 0.85
IS_CORRECT: true
EXPLANATION: The answer is mostly correct but could include more detail about Python being high-level and interpreted.
```

We parse this into structured data:

```python
def _parse_response(response, question):
    result = {}
    
    # Extract score
    if "SCORE:" in response:
        score_line = [line for line in response.split('\n') 
                     if 'SCORE:' in line][0]
        score_str = score_line.split('SCORE:')[1].strip()
        result['score'] = float(score_str)
    
    # Extract confidence
    if "CONFIDENCE:" in response:
        # Similar extraction...
        result['confidence'] = float(conf_str)
    
    # Extract explanation
    if "EXPLANATION:" in response:
        explanation_start = response.find('EXPLANATION:')
        result['explanation'] = response[explanation_start:].strip()
    
    return result
```

---

## Error Handling

### What Can Go Wrong?

1. **No API key**: Can't connect to OpenAI
2. **Invalid API key**: Authentication fails
3. **No credits**: API quota exceeded
4. **Network error**: Connection issues
5. **Parsing error**: Unexpected response format

### How We Handle Errors

```python
try:
    evaluation = evaluator.evaluate_answer(question)
except Exception as e:
    # Create a failed evaluation
    evaluation = Evaluation(
        question_id=question.id,
        score=0.0,
        confidence=0.0,
        explanation=f"Evaluation failed: {str(e)}",
        needs_human_review=True  # Always review failures
    )
```

---

## Testing the Evaluator

### Test 1: Simple Question

```python
from src.models import Question, QuestionType
from src.ai_evaluator import AIEvaluator

question = Question(
    id="q1",
    text="What is 2 + 2?",
    question_type=QuestionType.SHORT_ANSWER,
    reference_answer="4",
    user_answer="4",
    max_score=10.0
)

evaluator = AIEvaluator()
evaluation = evaluator.evaluate_answer(question)

print(f"Score: {evaluation.score}/10")
print(f"Confidence: {evaluation.confidence}")
# Expected: High score, high confidence
```

### Test 2: Partial Credit

```python
question = Question(
    id="q2",
    text="What is Python?",
    reference_answer="A high-level, interpreted programming language",
    user_answer="A programming language",
    max_score=10.0
)

evaluation = evaluator.evaluate_answer(question)
# Expected: Partial score (6-8), moderate confidence
```

### Test 3: Wrong Answer

```python
question = Question(
    id="q3",
    text="What is the capital of France?",
    reference_answer="Paris",
    user_answer="London",
    max_score=10.0
)

evaluation = evaluator.evaluate_answer(question)
# Expected: Low score (0-2), high confidence it's wrong
```

---

## Batch Evaluation

Evaluate multiple questions at once:

```python
from src.document_parser import DocumentParser

# Parse document
parser = DocumentParser()
questions = parser.parse_file('tests/sample_documents/python_quiz.txt')

# Evaluate all questions
evaluator = AIEvaluator()
evaluations = evaluator.batch_evaluate(questions)

# Review results
for q, e in zip(questions, evaluations):
    print(f"\nQ: {q.text[:50]}...")
    print(f"Score: {e.score}/{q.max_score}")
    print(f"Confidence: {e.confidence:.2f}")
    if e.needs_human_review:
        print("⚠️ Needs human review")
```

---

## Cost Considerations

### OpenAI Pricing (as of 2024)

**GPT-4o-mini**:
- Input: $0.15 per 1M tokens
- Output: $0.60 per 1M tokens

**Example**: Evaluating 100 questions
- ~50,000 tokens total
- Cost: ~$0.03 (3 cents!)

**Tips to save money**:
1. Use `gpt-4o-mini` instead of `gpt-4o`
2. Keep prompts concise
3. Set reasonable `max_tokens`
4. Cache results when possible

---

## Best Practices

### 1. Clear Prompts

❌ Bad:
```
Evaluate this answer: [answer]
```

✅ Good:
```
You are an expert evaluator.
Question: [question]
Expected: [reference]
Student: [answer]
Provide score, confidence, and explanation.
```

### 2. Appropriate Confidence Thresholds

- **Strict grading**: threshold = 0.8
- **Balanced**: threshold = 0.7
- **Lenient**: threshold = 0.6

### 3. Type-Specific Instructions

Different question types need different evaluation criteria. Our code handles this automatically!

### 4. Error Recovery

Always have fallback behavior when API calls fail.

---

## Common Issues

### Issue: "OpenAI API key not found"

**Solution**: Check your `.env` file:
```bash
cat .env
# Should show: OPENAI_API_KEY=sk-...
```

### Issue: "Rate limit exceeded"

**Solution**: 
- Wait a few seconds between requests
- Upgrade your OpenAI plan
- Use batch processing with delays

### Issue: "Parsing failed"

**Solution**:
- Check the raw response
- AI might not follow format exactly
- Add more robust parsing logic

---

## Testing Your Understanding

Try these exercises:

1. **Modify Temperature**: Change temperature to 0.0 and 1.0, see how results differ
2. **Custom Prompt**: Add your own evaluation criteria
3. **New Question Type**: Add evaluation logic for a new question type
4. **Error Simulation**: Test what happens when API key is invalid

---

## Next Steps

Excellent! You now understand:
- ✅ OpenAI API integration
- ✅ Prompt engineering
- ✅ Confidence scoring
- ✅ Response parsing

Next, we'll build the **LangGraph Workflow** that orchestrates the entire evaluation process with human-in-the-loop!

Continue to: **[Tutorial 04: Workflow Orchestration](04_workflow_orchestration.md)**

---

## Quick Reference

### Create Evaluator
```python
from src.ai_evaluator import AIEvaluator

evaluator = AIEvaluator(
    model="gpt-4o-mini",
    temperature=0.3,
    confidence_threshold=0.7
)
```

### Evaluate Single Question
```python
evaluation = evaluator.evaluate_answer(question)
```

### Batch Evaluate
```python
evaluations = evaluator.batch_evaluate(questions)
```

### Check if Needs Review
```python
if evaluation.needs_human_review:
    print("Human review required!")
```
