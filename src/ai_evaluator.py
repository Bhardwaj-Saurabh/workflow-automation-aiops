"""
AI Evaluator using OpenAI for answer assessment.

This module integrates with OpenAI's API to evaluate student answers,
assign scores, and provide explanations.

For beginners: This shows how to use AI APIs to analyze text and make
intelligent decisions with confidence scoring.
"""

import os
from typing import Optional, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

from src.models import Question, Evaluation, EvaluationStatus, QuestionType


# Load environment variables
load_dotenv()


class AIEvaluator:
    """
    Evaluates answers using OpenAI's language models.
    
    This class handles:
    - Connecting to OpenAI API
    - Creating evaluation prompts
    - Parsing AI responses
    - Calculating confidence scores
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.3,
        confidence_threshold: float = 0.7
    ):
        """
        Initialize the AI evaluator.
        
        Args:
            api_key: OpenAI API key (if None, reads from environment)
            model: OpenAI model to use (gpt-4o-mini is cost-effective)
            temperature: Creativity level (0.0-1.0, lower = more consistent)
            confidence_threshold: Minimum confidence for auto-approval
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        self.temperature = temperature
        self.confidence_threshold = confidence_threshold
    
    def evaluate_answer(self, question: Question) -> Evaluation:
        """
        Evaluate a single answer using AI.
        
        Args:
            question: Question object with user answer
            
        Returns:
            Evaluation object with score, confidence, and explanation
        """
        # Create the evaluation prompt
        prompt = self._create_evaluation_prompt(question)
        
        # Call OpenAI API
        response = self._call_openai(prompt)
        
        # Parse the response
        evaluation_data = self._parse_response(response, question)
        
        # Create Evaluation object
        evaluation = Evaluation(
            question_id=question.id,
            score=evaluation_data['score'],
            confidence=evaluation_data['confidence'],
            explanation=evaluation_data['explanation'],
            is_correct=evaluation_data['is_correct'],
            needs_human_review=evaluation_data['confidence'] < self.confidence_threshold,
            status=EvaluationStatus.AI_EVALUATED
        )
        
        return evaluation
    
    def _create_evaluation_prompt(self, question: Question) -> str:
        """
        Create a detailed prompt for the AI to evaluate an answer.
        
        This is crucial! The quality of the prompt determines the quality
        of the evaluation.
        
        Args:
            question: Question to evaluate
            
        Returns:
            Formatted prompt string
        """
        # Base prompt with instructions
        prompt = f"""You are an expert evaluator assessing student answers.

**Question Type**: {question.question_type.value}
**Maximum Score**: {question.max_score}

**Question**: {question.text}

"""
        
        # Add reference answer if available
        if question.reference_answer:
            prompt += f"**Expected Answer**: {question.reference_answer}\n\n"
        
        # Add the user's answer
        prompt += f"**Student's Answer**: {question.user_answer}\n\n"
        
        # Add evaluation instructions based on question type
        prompt += self._get_type_specific_instructions(question.question_type)
        
        # Request structured output
        prompt += """
Please provide your evaluation in the following format:

SCORE: [number between 0 and maximum score]
CONFIDENCE: [number between 0.0 and 1.0]
IS_CORRECT: [true or false]
EXPLANATION: [detailed explanation of why you gave this score]

Be objective, fair, and provide constructive feedback.
"""
        
        return prompt
    
    def _get_type_specific_instructions(self, question_type: QuestionType) -> str:
        """
        Get evaluation instructions specific to question type.
        
        Args:
            question_type: Type of question
            
        Returns:
            Instruction text
        """
        instructions = {
            QuestionType.TRUE_FALSE: """
**Evaluation Criteria**:
- Answer must be exactly correct (True/False)
- No partial credit
- Confidence should be very high (0.9+) for clear answers
""",
            QuestionType.MULTIPLE_CHOICE: """
**Evaluation Criteria**:
- Answer must match the correct option
- No partial credit unless answer shows understanding
- High confidence for exact matches
""",
            QuestionType.SHORT_ANSWER: """
**Evaluation Criteria**:
- Check for key concepts and accuracy
- Award partial credit for partially correct answers
- Consider different phrasings of correct answers
- Confidence depends on clarity and completeness
""",
            QuestionType.LONG_ANSWER: """
**Evaluation Criteria**:
- Assess depth of understanding
- Check for key points and examples
- Award partial credit generously
- Consider organization and clarity
- Lower confidence if answer is ambiguous
""",
            QuestionType.CODING: """
**Evaluation Criteria**:
- Check if code logic is correct
- Syntax errors should reduce score but not eliminate it
- Consider alternative solutions
- Award partial credit for correct approach
- High confidence only if code is clearly correct or incorrect
""",
            QuestionType.ESSAY: """
**Evaluation Criteria**:
- Assess argument quality and evidence
- Check for coherence and organization
- Consider depth of analysis
- This is subjective - use lower confidence (0.5-0.7)
- Recommend human review for final grading
"""
        }
        
        return instructions.get(question_type, instructions[QuestionType.SHORT_ANSWER])
    
    def _call_openai(self, prompt: str) -> str:
        """
        Make API call to OpenAI.
        
        Args:
            prompt: Evaluation prompt
            
        Returns:
            AI response text
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert educational evaluator. "
                                 "Provide fair, objective, and constructive assessments."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                max_tokens=500
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {str(e)}")
    
    def _parse_response(self, response: str, question: Question) -> Dict[str, Any]:
        """
        Parse the AI's response into structured data.
        
        Args:
            response: Raw AI response
            question: Original question (for context)
            
        Returns:
            Dictionary with score, confidence, explanation, is_correct
        """
        # Initialize defaults
        result = {
            'score': 0.0,
            'confidence': 0.5,
            'explanation': response,
            'is_correct': False
        }
        
        try:
            # Extract SCORE
            if "SCORE:" in response:
                score_line = [line for line in response.split('\n') if 'SCORE:' in line][0]
                score_str = score_line.split('SCORE:')[1].strip().split()[0]
                result['score'] = float(score_str)
                result['score'] = min(result['score'], question.max_score)  # Cap at max
            
            # Extract CONFIDENCE
            if "CONFIDENCE:" in response:
                conf_line = [line for line in response.split('\n') if 'CONFIDENCE:' in line][0]
                conf_str = conf_line.split('CONFIDENCE:')[1].strip().split()[0]
                result['confidence'] = float(conf_str)
                result['confidence'] = max(0.0, min(1.0, result['confidence']))  # Clamp 0-1
            
            # Extract IS_CORRECT
            if "IS_CORRECT:" in response:
                correct_line = [line for line in response.split('\n') if 'IS_CORRECT:' in line][0]
                correct_str = correct_line.split('IS_CORRECT:')[1].strip().lower()
                result['is_correct'] = correct_str.startswith('true')
            
            # Extract EXPLANATION
            if "EXPLANATION:" in response:
                explanation_start = response.find('EXPLANATION:') + len('EXPLANATION:')
                result['explanation'] = response[explanation_start:].strip()
        
        except Exception as e:
            # If parsing fails, use defaults and include error in explanation
            result['explanation'] = f"Parsing error: {str(e)}\n\nRaw response:\n{response}"
            result['confidence'] = 0.3  # Low confidence due to parsing error
        
        return result
    
    def batch_evaluate(self, questions: list[Question]) -> list[Evaluation]:
        """
        Evaluate multiple questions.
        
        Args:
            questions: List of questions to evaluate
            
        Returns:
            List of evaluations
        """
        evaluations = []
        
        for question in questions:
            try:
                evaluation = self.evaluate_answer(question)
                evaluations.append(evaluation)
            except Exception as e:
                # Create a failed evaluation
                evaluation = Evaluation(
                    question_id=question.id,
                    score=0.0,
                    confidence=0.0,
                    explanation=f"Evaluation failed: {str(e)}",
                    is_correct=False,
                    needs_human_review=True,
                    status=EvaluationStatus.PENDING
                )
                evaluations.append(evaluation)
        
        return evaluations


# Example usage and testing
if __name__ == "__main__":
    # Test with a sample question
    test_question = Question(
        id="test1",
        text="What is Python?",
        question_type=QuestionType.SHORT_ANSWER,
        reference_answer="Python is a high-level, interpreted programming language known for its simplicity",
        user_answer="Python is a programming language used for web development and data science",
        max_score=10.0,
        topic="Programming"
    )
    
    print("🤖 Testing AI Evaluator...\n")
    print(f"Question: {test_question.text}")
    print(f"Expected: {test_question.reference_answer}")
    print(f"Student Answer: {test_question.user_answer}\n")
    
    try:
        evaluator = AIEvaluator()
        evaluation = evaluator.evaluate_answer(test_question)
        
        print("✅ Evaluation Complete!\n")
        print(f"Score: {evaluation.score}/{test_question.max_score}")
        print(f"Confidence: {evaluation.confidence:.2f}")
        print(f"Correct: {evaluation.is_correct}")
        print(f"Needs Review: {evaluation.needs_human_review}")
        print(f"\nExplanation:\n{evaluation.explanation}")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\nMake sure you have:")
        print("1. Set OPENAI_API_KEY in your .env file")
        print("2. Valid API key with credits")
