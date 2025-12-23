"""
LangGraph Workflow for AI Assessment Evaluation.

This module defines the workflow state machine that orchestrates:
1. Document ingestion
2. AI evaluation
3. Human validation (when needed)
4. Report generation

For beginners: This shows how to build a state machine that can pause
for human input and resume automatically.
"""

from typing import TypedDict, List, Optional, Literal
from typing_extensions import Annotated
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import uuid

from src.models import Question, Evaluation, Assessment, Report
from src.document_parser import DocumentParser
from src.ai_evaluator import AIEvaluator


# Define the workflow state
class WorkflowState(TypedDict):
    """
    State that flows through the workflow.
    
    This is like a shared memory that each step can read and update.
    """
    # Input
    document_path: Optional[str]
    document_text: Optional[str]
    
    # Parsed data
    questions: List[Question]
    
    # Evaluation results
    evaluations: List[Evaluation]
    
    # Assessment
    assessment: Optional[Assessment]
    
    # Human review
    questions_needing_review: List[str]  # Question IDs
    human_feedback: dict  # {question_id: {score, notes}}
    
    # Final output
    report: Optional[Report]
    
    # Workflow control
    current_step: str
    error: Optional[str]
    completed: bool


class AssessmentWorkflow:
    """
    Orchestrates the entire assessment evaluation workflow.
    
    This class uses LangGraph to create a state machine that:
    - Processes documents
    - Evaluates answers with AI
    - Pauses for human review when needed
    - Generates final reports
    """
    
    def __init__(self):
        """Initialize the workflow."""
        self.parser = DocumentParser()
        self.evaluator = AIEvaluator()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph state machine.
        
        States:
        - ingest: Parse document and extract questions
        - evaluate: AI evaluates all answers
        - check_confidence: Determine if human review needed
        - human_review: Wait for human input (conditional)
        - finalize: Calculate final scores
        - generate_report: Create assessment report
        
        Returns:
            Compiled StateGraph
        """
        # Create the graph
        workflow = StateGraph(WorkflowState)
        
        # Add nodes (states)
        workflow.add_node("ingest", self._ingest_document)
        workflow.add_node("evaluate", self._evaluate_answers)
        workflow.add_node("check_confidence", self._check_confidence)
        workflow.add_node("human_review", self._human_review)
        workflow.add_node("finalize", self._finalize_scores)
        workflow.add_node("generate_report", self._generate_report)
        
        # Define edges (transitions)
        workflow.set_entry_point("ingest")
        
        workflow.add_edge("ingest", "evaluate")
        workflow.add_edge("evaluate", "check_confidence")
        
        # Conditional edge: human review or skip to finalize
        workflow.add_conditional_edges(
            "check_confidence",
            self._should_review,
            {
                "review": "human_review",
                "skip": "finalize"
            }
        )
        
        workflow.add_edge("human_review", "finalize")
        workflow.add_edge("finalize", "generate_report")
        workflow.add_edge("generate_report", END)
        
        # Compile with memory (allows pausing and resuming)
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)
    
    def _ingest_document(self, state: WorkflowState) -> WorkflowState:
        """
        Step 1: Parse document and extract questions.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with questions
        """
        try:
            # Parse from file or text
            if state.get("document_path"):
                questions = self.parser.parse_file(state["document_path"])
            elif state.get("document_text"):
                questions = self.parser.parse_text_directly(state["document_text"])
            else:
                raise ValueError("No document provided")
            
            # Create assessment ID
            assessment_id = str(uuid.uuid4())
            
            return {
                **state,
                "questions": questions,
                "assessment": Assessment(
                    id=assessment_id,
                    title=f"Assessment {assessment_id[:8]}",
                    questions=questions,
                    evaluations=[]
                ),
                "current_step": "ingest",
                "error": None
            }
        
        except Exception as e:
            return {
                **state,
                "error": f"Ingestion failed: {str(e)}",
                "current_step": "ingest"
            }
    
    def _evaluate_answers(self, state: WorkflowState) -> WorkflowState:
        """
        Step 2: AI evaluates all answers.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with evaluations
        """
        try:
            questions = state["questions"]
            evaluations = self.evaluator.batch_evaluate(questions)
            
            return {
                **state,
                "evaluations": evaluations,
                "current_step": "evaluate",
                "error": None
            }
        
        except Exception as e:
            return {
                **state,
                "error": f"Evaluation failed: {str(e)}",
                "current_step": "evaluate"
            }
    
    def _check_confidence(self, state: WorkflowState) -> WorkflowState:
        """
        Step 3: Check which questions need human review.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with review list
        """
        evaluations = state["evaluations"]
        
        # Find questions needing review
        needs_review = [
            eval.question_id 
            for eval in evaluations 
            if eval.needs_human_review
        ]
        
        return {
            **state,
            "questions_needing_review": needs_review,
            "current_step": "check_confidence"
        }
    
    def _should_review(self, state: WorkflowState) -> Literal["review", "skip"]:
        """
        Conditional routing: Do we need human review?
        
        Args:
            state: Current workflow state
            
        Returns:
            "review" if human input needed, "skip" otherwise
        """
        if state["questions_needing_review"]:
            return "review"
        return "skip"
    
    def _human_review(self, state: WorkflowState) -> WorkflowState:
        """
        Step 4: Wait for human review (this is where workflow pauses).
        
        In a real application, this would:
        1. Display questions to human reviewer
        2. Wait for their input
        3. Resume when feedback is provided
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state (waits for human_feedback to be added)
        """
        # In the actual Streamlit UI, this step will pause
        # and wait for user input through the interface
        
        # For now, just mark that we're in review mode
        return {
            **state,
            "current_step": "human_review"
        }
    
    def _finalize_scores(self, state: WorkflowState) -> WorkflowState:
        """
        Step 5: Calculate final scores with human overrides.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with final assessment
        """
        assessment = state["assessment"]
        evaluations = state["evaluations"]
        human_feedback = state.get("human_feedback", {})
        
        # Apply human overrides
        for eval in evaluations:
            if eval.question_id in human_feedback:
                feedback = human_feedback[eval.question_id]
                eval.human_override_score = feedback.get("score")
                eval.human_notes = feedback.get("notes")
                eval.reviewed_by_human = True
                eval.status = "human_reviewed"
        
        # Update assessment
        assessment.evaluations = evaluations
        assessment.calculate_scores()
        
        return {
            **state,
            "assessment": assessment,
            "current_step": "finalize"
        }
    
    def _generate_report(self, state: WorkflowState) -> WorkflowState:
        """
        Step 6: Generate final assessment report.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with report
        """
        assessment = state["assessment"]
        
        # Analyze strengths and weaknesses
        strengths, weaknesses = self._analyze_performance(assessment)
        
        # Generate summary
        summary = self._generate_summary(assessment)
        
        # Create recommendations
        recommendations = self._generate_recommendations(assessment, weaknesses)
        
        # Build report
        report = Report(
            assessment_id=assessment.id,
            summary=summary,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            detailed_results=self._build_detailed_results(assessment),
            statistics=self._calculate_statistics(assessment)
        )
        
        return {
            **state,
            "report": report,
            "current_step": "generate_report",
            "completed": True
        }
    
    def _analyze_performance(self, assessment: Assessment) -> tuple:
        """Analyze strengths and weaknesses."""
        from src.models import StrengthWeakness
        
        strengths = []
        weaknesses = []
        
        # Group by topic
        topic_scores = {}
        for q, e in zip(assessment.questions, assessment.evaluations):
            topic = q.topic or "General"
            if topic not in topic_scores:
                topic_scores[topic] = []
            
            score_pct = (e.score / q.max_score) * 100 if q.max_score > 0 else 0
            topic_scores[topic].append(score_pct)
        
        # Identify strengths (>80%) and weaknesses (<60%)
        for topic, scores in topic_scores.items():
            avg_score = sum(scores) / len(scores)
            
            if avg_score >= 80:
                strengths.append(StrengthWeakness(
                    category=topic,
                    description=f"Strong performance in {topic} with {avg_score:.1f}% average",
                    evidence=[f"{len(scores)} questions answered well"],
                    score_impact=avg_score
                ))
            elif avg_score < 60:
                weaknesses.append(StrengthWeakness(
                    category=topic,
                    description=f"Needs improvement in {topic} with {avg_score:.1f}% average",
                    evidence=[f"{len(scores)} questions need review"],
                    score_impact=avg_score
                ))
        
        return strengths, weaknesses
    
    def _generate_summary(self, assessment: Assessment) -> str:
        """Generate executive summary."""
        total_questions = len(assessment.questions)
        correct = sum(1 for e in assessment.evaluations if e.is_correct)
        
        return f"""
Assessment completed with {assessment.percentage:.1f}% overall score.

- Total Questions: {total_questions}
- Correct Answers: {correct}
- Score: {assessment.total_score:.1f}/{assessment.max_possible_score:.1f}

The assessment demonstrates {'strong' if assessment.percentage >= 80 else 'moderate' if assessment.percentage >= 60 else 'developing'} understanding of the material.
        """.strip()
    
    def _generate_recommendations(self, assessment: Assessment, weaknesses: list) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        if assessment.percentage < 60:
            recommendations.append("Review fundamental concepts before proceeding to advanced topics")
        
        for weakness in weaknesses:
            recommendations.append(f"Focus additional study on {weakness.category}")
        
        if not recommendations:
            recommendations.append("Continue building on this strong foundation")
        
        return recommendations
    
    def _build_detailed_results(self, assessment: Assessment) -> dict:
        """Build detailed question-by-question results."""
        results = {}
        
        for q, e in zip(assessment.questions, assessment.evaluations):
            results[q.id] = {
                "question": q.text,
                "user_answer": q.user_answer,
                "reference_answer": q.reference_answer,
                "score": e.score,
                "max_score": q.max_score,
                "is_correct": e.is_correct,
                "explanation": e.explanation,
                "confidence": e.confidence,
                "human_reviewed": e.reviewed_by_human
            }
        
        return results
    
    def _calculate_statistics(self, assessment: Assessment) -> dict:
        """Calculate statistical summary."""
        scores = [e.score for e in assessment.evaluations]
        confidences = [e.confidence for e in assessment.evaluations]
        
        return {
            "total_questions": len(assessment.questions),
            "correct_count": sum(1 for e in assessment.evaluations if e.is_correct),
            "average_confidence": sum(confidences) / len(confidences) if confidences else 0,
            "human_reviewed_count": sum(1 for e in assessment.evaluations if e.reviewed_by_human),
            "total_score": assessment.total_score,
            "max_possible_score": assessment.max_possible_score,
            "percentage": assessment.percentage
        }
    
    def run(self, document_path: Optional[str] = None, document_text: Optional[str] = None) -> dict:
        """
        Run the complete workflow.
        
        Args:
            document_path: Path to document file
            document_text: Raw document text
            
        Returns:
            Final workflow state
        """
        # Initial state
        initial_state = WorkflowState(
            document_path=document_path,
            document_text=document_text,
            questions=[],
            evaluations=[],
            assessment=None,
            questions_needing_review=[],
            human_feedback={},
            report=None,
            current_step="start",
            error=None,
            completed=False
        )
        
        # Run the workflow
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        final_state = self.graph.invoke(initial_state, config)
        
        return final_state


# Example usage
if __name__ == "__main__":
    print("🔄 Testing Assessment Workflow...\n")
    
    # Sample document text
    sample_text = """
    Q: What is Python?
    Expected: A high-level programming language
    A: A programming language
    
    Q: What is 2 + 2?
    A: 4
    """
    
    try:
        workflow = AssessmentWorkflow()
        result = workflow.run(document_text=sample_text)
        
        if result.get("error"):
            print(f"❌ Error: {result['error']}")
        else:
            print("✅ Workflow completed successfully!\n")
            
            assessment = result.get("assessment")
            if assessment:
                print(f"Questions: {len(assessment.questions)}")
                print(f"Score: {assessment.total_score}/{assessment.max_possible_score}")
                print(f"Percentage: {assessment.percentage:.1f}%")
            
            if result.get("questions_needing_review"):
                print(f"\n⚠️ {len(result['questions_needing_review'])} questions need human review")
            
            report = result.get("report")
            if report:
                print(f"\n📊 Report generated")
                print(f"Summary: {report.summary[:100]}...")
    
    except Exception as e:
        print(f"❌ Workflow failed: {str(e)}")
        print("\nMake sure you have set OPENAI_API_KEY in .env")
