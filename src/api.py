"""
FastAPI Backend Service for AI Assessment System.

This service provides REST API endpoints for:
- Document upload and parsing
- AI evaluation
- Workflow orchestration
- Report generation
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import tempfile
import os
import uuid
from pathlib import Path

from src.workflow import AssessmentWorkflow
from src.models import Question, Evaluation, Assessment, Report
from src.document_parser import DocumentParser
from src.ai_evaluator import AIEvaluator

# Initialize FastAPI app
app = FastAPI(
    title="AI Assessment API",
    description="Backend API for AI-assisted assessment evaluation system",
    version="1.0.0"
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for workflow states (use Redis/database in production)
workflow_states: Dict[str, Dict[str, Any]] = {}


# Request/Response Models
class DocumentUploadResponse(BaseModel):
    workflow_id: str
    questions: List[Dict[str, Any]]
    message: str


class EvaluationRequest(BaseModel):
    workflow_id: str


class HumanFeedbackRequest(BaseModel):
    workflow_id: str
    feedback: Dict[str, Dict[str, Any]]  # {question_id: {score, notes}}


class WorkflowStatusResponse(BaseModel):
    workflow_id: str
    status: str
    current_step: str
    questions_needing_review: List[str]
    assessment: Optional[Dict[str, Any]]
    report: Optional[Dict[str, Any]]


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes probes."""
    return {"status": "healthy", "service": "ai-assessment-backend"}


# Document upload and parsing
@app.post("/api/v1/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and parse a document.
    
    Supports: TXT, PDF, DOCX
    """
    try:
        # Validate file type
        allowed_extensions = {'.txt', '.pdf', '.docx'}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {allowed_extensions}"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        # Parse document
        parser = DocumentParser()
        questions = parser.parse_file(tmp_path)
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        # Create workflow
        workflow_id = str(uuid.uuid4())
        workflow_states[workflow_id] = {
            "questions": [q.model_dump() for q in questions],
            "evaluations": [],
            "status": "parsed",
            "current_step": "upload_complete"
        }
        
        return DocumentUploadResponse(
            workflow_id=workflow_id,
            questions=[q.model_dump() for q in questions],
            message=f"Successfully parsed {len(questions)} questions"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Text-based document submission
@app.post("/api/v1/submit-text", response_model=DocumentUploadResponse)
async def submit_text(text: str):
    """Submit document as plain text."""
    try:
        parser = DocumentParser()
        questions = parser.parse_text_directly(text)
        
        workflow_id = str(uuid.uuid4())
        workflow_states[workflow_id] = {
            "questions": [q.model_dump() for q in questions],
            "evaluations": [],
            "status": "parsed",
            "current_step": "text_submitted"
        }
        
        return DocumentUploadResponse(
            workflow_id=workflow_id,
            questions=[q.model_dump() for q in questions],
            message=f"Successfully parsed {len(questions)} questions"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# AI Evaluation
@app.post("/api/v1/evaluate")
async def evaluate_answers(request: EvaluationRequest, background_tasks: BackgroundTasks):
    """
    Evaluate answers using AI.
    
    This is an async operation that runs in the background.
    """
    workflow_id = request.workflow_id
    
    if workflow_id not in workflow_states:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Run evaluation in background
    background_tasks.add_task(run_evaluation, workflow_id)
    
    return {
        "workflow_id": workflow_id,
        "message": "Evaluation started",
        "status": "evaluating"
    }


async def run_evaluation(workflow_id: str):
    """Background task to run AI evaluation."""
    try:
        state = workflow_states[workflow_id]
        
        # Reconstruct Question objects
        questions = [Question(**q) for q in state["questions"]]
        
        # Evaluate
        evaluator = AIEvaluator()
        evaluations = evaluator.batch_evaluate(questions)
        
        # Update state
        state["evaluations"] = [e.model_dump() for e in evaluations]
        state["status"] = "evaluated"
        state["current_step"] = "evaluation_complete"
        
        # Identify questions needing review
        state["questions_needing_review"] = [
            e.question_id for e in evaluations if e.needs_human_review
        ]
    
    except Exception as e:
        workflow_states[workflow_id]["status"] = "error"
        workflow_states[workflow_id]["error"] = str(e)


# Get workflow status
@app.get("/api/v1/workflow/{workflow_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(workflow_id: str):
    """Get current workflow status."""
    if workflow_id not in workflow_states:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    state = workflow_states[workflow_id]
    
    # Build assessment if evaluations exist
    assessment = None
    if state.get("evaluations"):
        questions = [Question(**q) for q in state["questions"]]
        evaluations = [Evaluation(**e) for e in state["evaluations"]]
        
        assessment_obj = Assessment(
            id=workflow_id,
            title=f"Assessment {workflow_id[:8]}",
            questions=questions,
            evaluations=evaluations
        )
        assessment_obj.calculate_scores()
        assessment = assessment_obj.model_dump()
    
    return WorkflowStatusResponse(
        workflow_id=workflow_id,
        status=state["status"],
        current_step=state["current_step"],
        questions_needing_review=state.get("questions_needing_review", []),
        assessment=assessment,
        report=state.get("report")
    )


# Submit human feedback
@app.post("/api/v1/feedback")
async def submit_feedback(request: HumanFeedbackRequest):
    """Submit human feedback for low-confidence evaluations."""
    workflow_id = request.workflow_id
    
    if workflow_id not in workflow_states:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    state = workflow_states[workflow_id]
    
    # Apply human feedback
    evaluations = [Evaluation(**e) for e in state["evaluations"]]
    
    for eval in evaluations:
        if eval.question_id in request.feedback:
            feedback = request.feedback[eval.question_id]
            eval.human_override_score = feedback.get("score")
            eval.human_notes = feedback.get("notes")
            eval.reviewed_by_human = True
            eval.status = "human_reviewed"
    
    # Update state
    state["evaluations"] = [e.model_dump() for e in evaluations]
    state["status"] = "reviewed"
    state["current_step"] = "human_review_complete"
    
    return {
        "workflow_id": workflow_id,
        "message": "Feedback applied successfully"
    }


# Generate report
@app.post("/api/v1/generate-report/{workflow_id}")
async def generate_report(workflow_id: str):
    """Generate final assessment report."""
    if workflow_id not in workflow_states:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    try:
        state = workflow_states[workflow_id]
        
        # Reconstruct objects
        questions = [Question(**q) for q in state["questions"]]
        evaluations = [Evaluation(**e) for e in state["evaluations"]]
        
        # Create assessment
        assessment = Assessment(
            id=workflow_id,
            title=f"Assessment {workflow_id[:8]}",
            questions=questions,
            evaluations=evaluations
        )
        assessment.calculate_scores()
        
        # Use workflow to generate report
        workflow = AssessmentWorkflow()
        
        # Create temporary state for report generation
        temp_state = {
            "assessment": assessment,
            "questions": questions,
            "evaluations": evaluations
        }
        
        # Generate report
        final_state = workflow._generate_report(temp_state)
        report = final_state["report"]
        
        # Store report
        state["report"] = report.model_dump()
        state["status"] = "completed"
        state["current_step"] = "report_generated"
        
        return {
            "workflow_id": workflow_id,
            "report": report.model_dump(),
            "message": "Report generated successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Get report as markdown
@app.get("/api/v1/report/{workflow_id}/markdown")
async def get_report_markdown(workflow_id: str):
    """Get report in markdown format."""
    if workflow_id not in workflow_states:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    state = workflow_states[workflow_id]
    
    if "report" not in state:
        raise HTTPException(status_code=404, detail="Report not generated yet")
    
    report = Report(**state["report"])
    markdown = report.to_markdown()
    
    return {"markdown": markdown}


# List all workflows
@app.get("/api/v1/workflows")
async def list_workflows():
    """List all workflows."""
    return {
        "workflows": [
            {
                "workflow_id": wid,
                "status": state["status"],
                "current_step": state["current_step"],
                "question_count": len(state["questions"])
            }
            for wid, state in workflow_states.items()
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
