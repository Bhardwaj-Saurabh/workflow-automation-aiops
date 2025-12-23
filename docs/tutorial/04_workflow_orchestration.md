# Tutorial 04: Workflow Orchestration with LangGraph

Welcome to Tutorial 04! Now we'll build the state machine that orchestrates the entire evaluation process.

---

## What You'll Learn

- What is a **state machine**?
- How **LangGraph** works
- Building workflows with **conditional routing**
- Implementing **human-in-the-loop** patterns
- State persistence and resumption

---

## Understanding State Machines

### What is a State Machine?

A **state machine** is like a flowchart that actually runs. It has:

1. **States** (steps in the process)
2. **Transitions** (moving from one step to another)
3. **Conditions** (deciding which path to take)

### Real-World Example: Coffee Machine

```
START → Insert Money → Select Drink → [Check Stock]
                                           ↓
                                    ┌──────┴──────┐
                                    │             │
                                 In Stock    Out of Stock
                                    │             │
                                    ▼             ▼
                              Make Coffee    Refund Money
                                    │             │
                                    └──────┬──────┘
                                           ▼
                                          END
```

Our assessment workflow is similar!

---

## Our Assessment Workflow

### States (Steps)

1. **INGEST**: Parse document, extract questions
2. **EVALUATE**: AI evaluates all answers
3. **CHECK_CONFIDENCE**: Determine if human review needed
4. **HUMAN_REVIEW**: Wait for human input (conditional)
5. **FINALIZE**: Calculate final scores
6. **GENERATE_REPORT**: Create assessment report

### Flow Diagram

```
START
  │
  ▼
INGEST (Parse Document)
  │
  ▼
EVALUATE (AI Evaluation)
  │
  ▼
CHECK_CONFIDENCE
  │
  ├─────────────┬─────────────┐
  │             │             │
High Conf.   Low Conf.     Error
  │             │             │
  │             ▼             │
  │      HUMAN_REVIEW         │
  │             │             │
  └──────┬──────┘             │
         │                    │
         ▼                    ▼
    FINALIZE              Handle Error
         │
         ▼
  GENERATE_REPORT
         │
         ▼
        END
```

---

## LangGraph Basics

### What is LangGraph?

**LangGraph** is a library for building stateful workflows with LLMs. It helps you:
- Define states and transitions
- Handle conditional routing
- Persist state (pause and resume)
- Visualize workflows

### Core Concepts

#### 1. State

The **state** is shared data that flows through the workflow:

```python
class WorkflowState(TypedDict):
    questions: List[Question]
    evaluations: List[Evaluation]
    current_step: str
    error: Optional[str]
```

Think of it as a backpack that each step can read from and add to.

#### 2. Nodes

**Nodes** are functions that process the state:

```python
def _ingest_document(state: WorkflowState) -> WorkflowState:
    # Read state
    document_path = state["document_path"]
    
    # Do work
    questions = parser.parse_file(document_path)
    
    # Update state
    return {**state, "questions": questions}
```

#### 3. Edges

**Edges** connect nodes (define transitions):

```python
# Simple edge: always go from A to B
workflow.add_edge("ingest", "evaluate")

# Conditional edge: decide where to go
workflow.add_conditional_edges(
    "check_confidence",
    should_review_function,
    {
        "review": "human_review",
        "skip": "finalize"
    }
)
```

---

## Building Our Workflow

### Step 1: Define the State

```python
from typing import TypedDict, List, Optional

class WorkflowState(TypedDict):
    # Input
    document_path: Optional[str]
    
    # Processing
    questions: List[Question]
    evaluations: List[Evaluation]
    
    # Human interaction
    questions_needing_review: List[str]
    human_feedback: dict
    
    # Output
    report: Optional[Report]
    
    # Control
    current_step: str
    error: Optional[str]
    completed: bool
```

### Step 2: Create the Graph

```python
from langgraph.graph import StateGraph, END

workflow = StateGraph(WorkflowState)
```

### Step 3: Add Nodes

```python
# Add processing nodes
workflow.add_node("ingest", ingest_function)
workflow.add_node("evaluate", evaluate_function)
workflow.add_node("human_review", review_function)
workflow.add_node("finalize", finalize_function)
workflow.add_node("generate_report", report_function)
```

### Step 4: Define Transitions

```python
# Set starting point
workflow.set_entry_point("ingest")

# Simple transitions
workflow.add_edge("ingest", "evaluate")
workflow.add_edge("evaluate", "check_confidence")

# Conditional transition
workflow.add_conditional_edges(
    "check_confidence",
    should_review,  # Function that returns "review" or "skip"
    {
        "review": "human_review",
        "skip": "finalize"
    }
)

workflow.add_edge("human_review", "finalize")
workflow.add_edge("finalize", "generate_report")
workflow.add_edge("generate_report", END)
```

### Step 5: Compile

```python
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()  # Enables pause/resume
compiled_graph = workflow.compile(checkpointer=memory)
```

---

## Implementing Each Node

### Node 1: Ingest Document

```python
def _ingest_document(state: WorkflowState) -> WorkflowState:
    """Parse document and extract questions."""
    try:
        parser = DocumentParser()
        questions = parser.parse_file(state["document_path"])
        
        return {
            **state,
            "questions": questions,
            "current_step": "ingest",
            "error": None
        }
    except Exception as e:
        return {
            **state,
            "error": f"Parsing failed: {str(e)}",
            "current_step": "ingest"
        }
```

**Key Points**:
- Always return updated state
- Handle errors gracefully
- Update `current_step` for tracking

### Node 2: Evaluate Answers

```python
def _evaluate_answers(state: WorkflowState) -> WorkflowState:
    """AI evaluates all questions."""
    evaluator = AIEvaluator()
    questions = state["questions"]
    
    evaluations = evaluator.batch_evaluate(questions)
    
    return {
        **state,
        "evaluations": evaluations,
        "current_step": "evaluate"
    }
```

### Node 3: Check Confidence

```python
def _check_confidence(state: WorkflowState) -> WorkflowState:
    """Identify questions needing human review."""
    evaluations = state["evaluations"]
    
    needs_review = [
        e.question_id 
        for e in evaluations 
        if e.needs_human_review
    ]
    
    return {
        **state,
        "questions_needing_review": needs_review,
        "current_step": "check_confidence"
    }
```

### Conditional Routing Function

```python
def _should_review(state: WorkflowState) -> str:
    """Decide: human review or skip?"""
    if state["questions_needing_review"]:
        return "review"  # Go to human_review node
    return "skip"  # Go to finalize node
```

**This is the magic!** The workflow automatically routes based on confidence.

### Node 4: Human Review

```python
def _human_review(state: WorkflowState) -> WorkflowState:
    """Wait for human input."""
    # In Streamlit UI, this will pause the workflow
    # and display questions for review
    
    # The workflow resumes when human_feedback is added
    return {
        **state,
        "current_step": "human_review"
    }
```

### Node 5: Finalize Scores

```python
def _finalize_scores(state: WorkflowState) -> WorkflowState:
    """Apply human overrides and calculate final scores."""
    evaluations = state["evaluations"]
    human_feedback = state.get("human_feedback", {})
    
    # Apply human overrides
    for eval in evaluations:
        if eval.question_id in human_feedback:
            feedback = human_feedback[eval.question_id]
            eval.human_override_score = feedback["score"]
            eval.human_notes = feedback["notes"]
            eval.reviewed_by_human = True
    
    # Calculate totals
    assessment = state["assessment"]
    assessment.evaluations = evaluations
    assessment.calculate_scores()
    
    return {
        **state,
        "assessment": assessment,
        "current_step": "finalize"
    }
```

### Node 6: Generate Report

```python
def _generate_report(state: WorkflowState) -> WorkflowState:
    """Create final assessment report."""
    assessment = state["assessment"]
    
    # Analyze performance
    strengths, weaknesses = analyze_performance(assessment)
    
    # Create report
    report = Report(
        assessment_id=assessment.id,
        summary=generate_summary(assessment),
        strengths=strengths,
        weaknesses=weaknesses,
        recommendations=generate_recommendations(weaknesses)
    )
    
    return {
        **state,
        "report": report,
        "completed": True,
        "current_step": "generate_report"
    }
```

---

## Running the Workflow

### Basic Usage

```python
from src.workflow import AssessmentWorkflow

# Create workflow
workflow = AssessmentWorkflow()

# Run with document
result = workflow.run(document_path="tests/sample_documents/python_quiz.txt")

# Check result
if result["completed"]:
    print("✅ Assessment complete!")
    print(f"Score: {result['assessment'].percentage:.1f}%")
    
    if result["questions_needing_review"]:
        print(f"⚠️ {len(result['questions_needing_review'])} questions need review")
```

### With Human Review

```python
# Run workflow
result = workflow.run(document_path="quiz.txt")

# Check if human review needed
if result["questions_needing_review"]:
    print("Pausing for human review...")
    
    # In Streamlit, display questions and collect feedback
    human_feedback = {
        "q1": {"score": 8.5, "notes": "Good answer, minor detail missing"},
        "q3": {"score": 5.0, "notes": "Partially correct"}
    }
    
    # Resume workflow with feedback
    result["human_feedback"] = human_feedback
    final_result = workflow.graph.invoke(result, config)
```

---

## State Persistence

### Why Persistence Matters

Persistence allows workflows to:
- **Pause** for human input
- **Resume** from where they left off
- **Survive** crashes or restarts
- **Track** progress

### How It Works

```python
from langgraph.checkpoint.memory import MemorySaver

# Create memory
memory = MemorySaver()

# Compile with checkpointer
graph = workflow.compile(checkpointer=memory)

# Run with thread ID
config = {"configurable": {"thread_id": "assessment-123"}}
result = graph.invoke(initial_state, config)

# Later, resume with same thread ID
resumed_result = graph.invoke(updated_state, config)
```

The `thread_id` identifies a specific workflow instance.

---

## Human-in-the-Loop Pattern

### The Pattern

1. **AI does initial work** (fast, automated)
2. **AI checks confidence** (self-aware)
3. **If uncertain** → Pause for human
4. **Human provides input** (quality control)
5. **Workflow resumes** with human feedback
6. **Final result** combines AI + human judgment

### Benefits

- **Efficiency**: AI handles routine cases
- **Quality**: Humans review edge cases
- **Trust**: Humans stay in control
- **Learning**: System improves over time

### Implementation

```python
# Conditional routing
workflow.add_conditional_edges(
    "check_confidence",
    lambda state: "review" if state["questions_needing_review"] else "skip",
    {
        "review": "human_review",  # Pause here
        "skip": "finalize"         # Continue automatically
    }
)
```

---

## Error Handling

### Graceful Degradation

```python
def _ingest_document(state: WorkflowState) -> WorkflowState:
    try:
        # Normal processing
        questions = parser.parse_file(state["document_path"])
        return {**state, "questions": questions, "error": None}
    
    except Exception as e:
        # Capture error, don't crash
        return {
            **state,
            "error": f"Ingestion failed: {str(e)}",
            "questions": [],
            "current_step": "ingest"
        }
```

### Error Recovery

```python
# Check for errors after each step
if result.get("error"):
    print(f"❌ Error in {result['current_step']}: {result['error']}")
    # Handle appropriately
```

---

## Testing the Workflow

### Test 1: Simple Document (No Review Needed)

```python
sample_text = """
Q: What is 2 + 2?
A: 4
"""

workflow = AssessmentWorkflow()
result = workflow.run(document_text=sample_text)

# Expected: High confidence, no human review
assert not result["questions_needing_review"]
assert result["completed"]
```

### Test 2: Ambiguous Answer (Review Needed)

```python
sample_text = """
Q: Explain quantum computing
A: It's complicated
"""

result = workflow.run(document_text=sample_text)

# Expected: Low confidence, needs review
assert len(result["questions_needing_review"]) > 0
```

---

## Visualizing the Workflow

LangGraph can generate visual diagrams:

```python
from IPython.display import Image

# Get graph visualization
Image(workflow.graph.get_graph().draw_mermaid_png())
```

This creates a flowchart showing all states and transitions!

---

## Best Practices

### 1. Keep Nodes Focused

Each node should do ONE thing well:
- ✅ `_ingest_document` - only parses
- ✅ `_evaluate_answers` - only evaluates
- ❌ Don't mix parsing and evaluation in one node

### 2. Always Update State

```python
# ✅ Good: Return updated state
return {**state, "questions": questions}

# ❌ Bad: Modify state in place
state["questions"] = questions
return state
```

### 3. Handle Errors Gracefully

Never let exceptions crash the workflow. Capture them in state.

### 4. Use Meaningful Step Names

```python
# ✅ Good
"current_step": "evaluate"

# ❌ Bad
"current_step": "step2"
```

---

## Common Issues

### Issue: "State not updating"

**Problem**: Forgetting to return updated state

**Solution**:
```python
# Always return new state
return {**state, "new_field": value}
```

### Issue: "Workflow stuck in loop"

**Problem**: Conditional routing always returns same value

**Solution**: Check your routing function logic

### Issue: "Can't resume workflow"

**Problem**: No checkpointer or different thread_id

**Solution**: Use MemorySaver and consistent thread_id

---

## Next Steps

Excellent! You now understand:
- ✅ State machines and workflows
- ✅ LangGraph basics
- ✅ Conditional routing
- ✅ Human-in-the-loop patterns
- ✅ State persistence

Next, we'll build the **Streamlit UI** that brings this workflow to life with an interactive interface!

Continue to: **[Tutorial 05: Building the UI](05_building_ui.md)**

---

## Quick Reference

### Create Workflow
```python
from src.workflow import AssessmentWorkflow

workflow = AssessmentWorkflow()
```

### Run Workflow
```python
result = workflow.run(document_path="quiz.txt")
```

### Check Status
```python
if result["completed"]:
    print("Done!")
if result["error"]:
    print(f"Error: {result['error']}")
if result["questions_needing_review"]:
    print("Needs human review")
```

### Access Results
```python
assessment = result["assessment"]
report = result["report"]
```
