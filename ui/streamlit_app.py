"""
Streamlit UI for AI Assessment Evaluation System - API Client Version.

This frontend communicates with the backend API via HTTP requests.
"""

import streamlit as st
import requests
import os
from datetime import datetime
from typing import Optional, Dict, Any
import time

# Backend API configuration
BACKEND_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "300"))

# Page configuration
st.set_page_config(
    page_title="AI Assessment Evaluator",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS (same as before)
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .step-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2ca02c;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .question-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #1f77b4;
    }
    .evaluation-card {
        background-color: #e8f4f8;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-top: 0.5rem;
    }
    .score-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 0.25rem;
        font-weight: bold;
        font-size: 1.1rem;
    }
    .score-high {
        background-color: #d4edda;
        color: #155724;
    }
    .score-medium {
        background-color: #fff3cd;
        color: #856404;
    }
    .score-low {
        background-color: #f8d7da;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if 'workflow_id' not in st.session_state:
        st.session_state.workflow_id = None
    if 'workflow_data' not in st.session_state:
        st.session_state.workflow_data = None
    if 'human_feedback' not in st.session_state:
        st.session_state.human_feedback = {}
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "upload"


def api_request(method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
    """Make API request to backend."""
    url = f"{BACKEND_URL}{endpoint}"
    
    try:
        response = requests.request(method, url, timeout=API_TIMEOUT, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return None


def get_workflow_status(workflow_id: str) -> Optional[Dict[str, Any]]:
    """Get workflow status from backend."""
    return api_request("GET", f"/api/v1/workflow/{workflow_id}")


def render_header():
    """Render the main header."""
    st.markdown('<div class="main-header">📝 AI Assessment Evaluator</div>', unsafe_allow_html=True)
    st.markdown("""
    <p style="text-align: center; color: #666; font-size: 1.1rem;">
    Automated assessment evaluation with AI-powered analysis and human-in-the-loop validation
    </p>
    """, unsafe_allow_html=True)
    st.markdown("---")


def render_sidebar():
    """Render the sidebar with navigation and info."""
    with st.sidebar:
        st.header("📋 Navigation")
        
        # Progress indicator
        steps = {
            "upload": "1️⃣ Upload Document",
            "review": "2️⃣ Review Questions",
            "evaluate": "3️⃣ AI Evaluation",
            "human_review": "4️⃣ Human Review",
            "report": "5️⃣ Final Report"
        }
        
        current = st.session_state.current_page
        for key, label in steps.items():
            if key == current:
                st.markdown(f"**→ {label}**")
            else:
                st.markdown(f"   {label}")
        
        st.markdown("---")
        
        # Info section
        st.header("ℹ️ About")
        st.markdown("""
        This system uses AI to evaluate answers and identifies cases that need human review.
        
        **Features:**
        - Multi-format support (TXT, PDF, DOCX)
        - AI-powered evaluation
        - Confidence scoring
        - Human validation
        - Detailed reports
        """)
        
        st.markdown("---")
        
        # Backend status
        st.header("� Backend Status")
        health = api_request("GET", "/health")
        if health:
            st.success("✅ Connected")
        else:
            st.error("❌ Disconnected")


def page_upload():
    """Page 1: Document Upload"""
    st.markdown('<div class="step-header">Step 1: Upload Assessment Document</div>', unsafe_allow_html=True)
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose a document file",
        type=['txt', 'pdf', 'docx'],
        help="Upload a document containing questions and answers in Q:/A: format"
    )
    
    # Text input option
    st.markdown("### Or paste text directly:")
    text_input = st.text_area(
        "Document text",
        height=200,
        placeholder="""Q: What is Python?
Expected: A high-level programming language
A: Python is a programming language

Q: What is 2 + 2?
A: 4""",
        help="Format: Q: question, Expected: reference (optional), A: answer"
    )
    
    # Process button
    if st.button("🚀 Process Document", type="primary", use_container_width=True):
        if not uploaded_file and not text_input:
            st.error("Please upload a file or paste text")
            return
        
        with st.spinner("Processing document..."):
            try:
                if uploaded_file:
                    # Upload file to backend
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    result = api_request("POST", "/api/v1/upload", files=files)
                else:
                    # Submit text to backend
                    result = api_request("POST", "/api/v1/submit-text", params={"text": text_input})
                
                if result:
                    st.session_state.workflow_id = result["workflow_id"]
                    st.session_state.workflow_data = result
                    st.session_state.current_page = "review"
                    st.success(f"✅ {result['message']}")
                    st.rerun()
            
            except Exception as e:
                st.error(f"Failed to process document: {str(e)}")
    
    # Example format
    with st.expander("📖 Document Format Guide"):
        st.markdown("""
        ### Expected Format
        
        ```
        Q: Question text here?
        Expected: Reference answer (optional)
        A: User's answer here
        
        Q: Another question?
        A: Another answer
        ```
        
        ### Supported Question Types
        - True/False
        - Multiple Choice
        - Short Answer
        - Long Answer
        - Coding
        - Essay
        
        The system automatically detects question types!
        """)


def page_review_questions():
    """Page 2: Review Extracted Questions"""
    if not st.session_state.workflow_id:
        st.warning("No document processed yet")
        return
    
    st.markdown('<div class="step-header">Step 2: Review Extracted Questions</div>', unsafe_allow_html=True)
    
    questions = st.session_state.workflow_data.get("questions", [])
    
    if not questions:
        st.error("No questions found in document")
        return
    
    st.success(f"✅ Extracted {len(questions)} questions")
    
    # Display questions
    for i, q in enumerate(questions, 1):
        with st.container():
            st.markdown(f"""
            <div class="question-card">
                <h4>Question {i} ({q['question_type']})</h4>
                <p><strong>Q:</strong> {q['text']}</p>
                <p><strong>Student Answer:</strong> {q['user_answer']}</p>
                {f"<p><strong>Expected:</strong> {q['reference_answer']}</p>" if q.get('reference_answer') else ''}
                <p><strong>Max Score:</strong> {q['max_score']} points</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Navigation
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Upload", use_container_width=True):
            st.session_state.current_page = "upload"
            st.rerun()
    with col2:
        if st.button("Start AI Evaluation →", type="primary", use_container_width=True):
            # Trigger evaluation
            with st.spinner("Starting AI evaluation..."):
                result = api_request("POST", "/api/v1/evaluate", 
                                   json={"workflow_id": st.session_state.workflow_id})
                if result:
                    st.session_state.current_page = "evaluate"
                    st.rerun()


def page_evaluation():
    """Page 3: AI Evaluation Results"""
    if not st.session_state.workflow_id:
        st.warning("No evaluation results yet")
        return
    
    st.markdown('<div class="step-header">Step 3: AI Evaluation Results</div>', unsafe_allow_html=True)
    
    # Poll for evaluation completion
    with st.spinner("AI is evaluating answers..."):
        max_attempts = 60
        for attempt in range(max_attempts):
            status = get_workflow_status(st.session_state.workflow_id)
            
            if status and status["status"] in ["evaluated", "reviewed", "completed"]:
                st.session_state.workflow_data = status
                break
            
            time.sleep(2)
        else:
            st.error("Evaluation timeout. Please try again.")
            return
    
    assessment = st.session_state.workflow_data.get("assessment")
    
    if not assessment:
        st.error("No evaluation data available")
        return
    
    # Overall stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Score", f"{assessment['total_score']:.1f}")
    with col2:
        st.metric("Max Possible", f"{assessment['max_possible_score']:.1f}")
    with col3:
        st.metric("Percentage", f"{assessment['percentage']:.1f}%")
    with col4:
        correct_count = sum(1 for e in assessment["evaluations"] if e["is_correct"])
        st.metric("Correct", f"{correct_count}/{len(assessment['evaluations'])}")
    
    st.markdown("---")
    
    # Display each evaluation
    questions = {q["id"]: q for q in assessment["questions"]}
    
    for e in assessment["evaluations"]:
        q = questions[e["question_id"]]
        score_pct = (e["score"] / q["max_score"] * 100) if q["max_score"] > 0 else 0
        score_class = "score-high" if score_pct >= 80 else "score-medium" if score_pct >= 60 else "score-low"
        
        with st.container():
            st.markdown(f"""
            <div class="question-card">
                <h4>{q['text']}</h4>
                <p><strong>Answer:</strong> {q['user_answer']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="evaluation-card">
                <span class="score-badge {score_class}">Score: {e['score']:.1f}/{q['max_score']}</span>
                <span style="margin-left: 1rem;">Confidence: {e['confidence']:.0%}</span>
                <span style="margin-left: 1rem;">{'✅ Correct' if e['is_correct'] else '❌ Incorrect'}</span>
                {f'<span style="margin-left: 1rem; color: #ff6b6b;">⚠️ Needs Review</span>' if e['needs_human_review'] else ''}
                <p style="margin-top: 0.5rem;"><strong>Explanation:</strong> {e['explanation']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
    
    # Navigation
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Questions", use_container_width=True):
            st.session_state.current_page = "review"
            st.rerun()
    with col2:
        questions_needing_review = st.session_state.workflow_data.get("questions_needing_review", [])
        if questions_needing_review:
            if st.button("Review Flagged Questions →", type="primary", use_container_width=True):
                st.session_state.current_page = "human_review"
                st.rerun()
        else:
            if st.button("Generate Report →", type="primary", use_container_width=True):
                # Generate report
                with st.spinner("Generating report..."):
                    result = api_request("POST", f"/api/v1/generate-report/{st.session_state.workflow_id}")
                    if result:
                        st.session_state.current_page = "report"
                        st.rerun()


def page_human_review():
    """Page 4: Human Review for Low-Confidence Evaluations"""
    if not st.session_state.workflow_id:
        st.warning("No evaluation results yet")
        return
    
    st.markdown('<div class="step-header">Step 4: Human Review Required</div>', unsafe_allow_html=True)
    
    questions_needing_review = st.session_state.workflow_data.get("questions_needing_review", [])
    
    if not questions_needing_review:
        st.success("✅ No questions need human review!")
        if st.button("Generate Report →", type="primary"):
            with st.spinner("Generating report..."):
                result = api_request("POST", f"/api/v1/generate-report/{st.session_state.workflow_id}")
                if result:
                    st.session_state.current_page = "report"
                    st.rerun()
        return
    
    st.info(f"⚠️ {len(questions_needing_review)} questions need your review")
    
    assessment = st.session_state.workflow_data["assessment"]
    questions = {q["id"]: q for q in assessment["questions"]}
    evaluations = {e["question_id"]: e for e in assessment["evaluations"]}
    
    # Review each flagged question
    for q_id in questions_needing_review:
        q = questions[q_id]
        e = evaluations[q_id]
        
        with st.container():
            st.markdown(f"""
            <div class="question-card">
                <h4>{q['text']}</h4>
                <p><strong>Student Answer:</strong> {q['user_answer']}</p>
                {f"<p><strong>Expected:</strong> {q['reference_answer']}</p>" if q.get('reference_answer') else ''}
                <p><strong>AI Score:</strong> {e['score']:.1f}/{q['max_score']} (Confidence: {e['confidence']:.0%})</p>
                <p><strong>AI Explanation:</strong> {e['explanation']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Human override
            col1, col2 = st.columns([2, 3])
            with col1:
                override_score = st.number_input(
                    "Your Score",
                    min_value=0.0,
                    max_value=float(q["max_score"]),
                    value=float(e["score"]),
                    step=0.5,
                    key=f"score_{q_id}"
                )
            with col2:
                notes = st.text_area(
                    "Notes (optional)",
                    placeholder="Add your comments...",
                    key=f"notes_{q_id}",
                    height=100
                )
            
            # Store feedback
            st.session_state.human_feedback[q_id] = {
                "score": override_score,
                "notes": notes
            }
            
            st.markdown("---")
    
    # Submit button
    if st.button("✅ Submit Reviews", type="primary", use_container_width=True):
        with st.spinner("Submitting feedback..."):
            result = api_request("POST", "/api/v1/feedback", 
                               json={
                                   "workflow_id": st.session_state.workflow_id,
                                   "feedback": st.session_state.human_feedback
                               })
            
            if result:
                # Generate report
                report_result = api_request("POST", f"/api/v1/generate-report/{st.session_state.workflow_id}")
                if report_result:
                    st.session_state.current_page = "report"
                    st.success("✅ Reviews submitted!")
                    st.rerun()


def page_report():
    """Page 5: Final Assessment Report"""
    if not st.session_state.workflow_id:
        st.warning("No report available yet")
        return
    
    st.markdown('<div class="step-header">Step 5: Final Assessment Report</div>', unsafe_allow_html=True)
    
    # Get latest workflow status
    status = get_workflow_status(st.session_state.workflow_id)
    if not status or not status.get("report"):
        st.error("Report not generated yet")
        return
    
    report = status["report"]
    assessment = status["assessment"]
    
    # Overall score
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 2rem; border-radius: 1rem; color: white; text-align: center; margin-bottom: 2rem;">
        <h2 style="margin: 0; font-size: 3rem;">{assessment['percentage']:.1f}%</h2>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.2rem;">Overall Score: {assessment['total_score']:.1f}/{assessment['max_possible_score']:.1f}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Summary
    st.markdown("### 📋 Summary")
    st.info(report["summary"])
    
    # Strengths
    if report.get("strengths"):
        st.markdown("### 💪 Strengths")
        for strength in report["strengths"]:
            st.success(f"**{strength['category']}**: {strength['description']}")
    
    # Weaknesses
    if report.get("weaknesses"):
        st.markdown("### 📈 Areas for Improvement")
        for weakness in report["weaknesses"]:
            st.warning(f"**{weakness['category']}**: {weakness['description']}")
    
    # Recommendations
    if report.get("recommendations"):
        st.markdown("### 💡 Recommendations")
        for i, rec in enumerate(report["recommendations"], 1):
            st.markdown(f"{i}. {rec}")
    
    # Statistics
    st.markdown("### 📊 Statistics")
    stats = report["statistics"]
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Questions", stats["total_questions"])
        st.metric("Correct Answers", stats["correct_count"])
    with col2:
        st.metric("Average Confidence", f"{stats['average_confidence']:.0%}")
        st.metric("Human Reviewed", stats["human_reviewed_count"])
    with col3:
        st.metric("Total Score", f"{stats['total_score']:.1f}")
        st.metric("Percentage", f"{stats['percentage']:.1f}%")
    
    # Download report
    st.markdown("---")
    st.markdown("### 📥 Download Report")
    
    # Get markdown report
    markdown_result = api_request("GET", f"/api/v1/report/{st.session_state.workflow_id}/markdown")
    if markdown_result:
        markdown_report = markdown_result["markdown"]
        
        st.download_button(
            label="📄 Download as Markdown",
            data=markdown_report,
            file_name=f"assessment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True
        )
    
    # Start over button
    st.markdown("---")
    if st.button("🔄 Start New Assessment", use_container_width=True):
        st.session_state.workflow_id = None
        st.session_state.workflow_data = None
        st.session_state.human_feedback = {}
        st.session_state.current_page = "upload"
        st.rerun()


def main():
    """Main application entry point."""
    initialize_session_state()
    render_header()
    render_sidebar()
    
    # Route to appropriate page
    page = st.session_state.current_page
    
    if page == "upload":
        page_upload()
    elif page == "review":
        page_review_questions()
    elif page == "evaluate":
        page_evaluation()
    elif page == "human_review":
        page_human_review()
    elif page == "report":
        page_report()


if __name__ == "__main__":
    main()
