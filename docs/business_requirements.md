# Business Requirements Document (BRD)
## AI-Assisted Assessment Evaluation & Reporting System

---

## 1. Purpose

The purpose of this project is to build an **AI-assisted workflow automation system** that evaluates **question-and-answer documents**, interacts with a **human user for clarification or validation**, and generates a **final structured assessment report**.

The system is designed to assist educators, interviewers, trainers, and evaluators in **automatically assessing responses**, while still **keeping humans in the loop** for subjective or ambiguous cases.

---

## 2. Business Objective

### Primary Objectives
- Automate the evaluation of question–answer documents
- Reduce manual effort in assessment and scoring
- Provide structured, explainable feedback
- Combine AI judgment with human validation

### Secondary Objectives
- Identify strengths and weaknesses of respondents
- Generate standardized evaluation reports
- Demonstrate human-in-the-loop AI workflows
- Serve as a learning project for modern AI orchestration tools

---

## 3. Problem Statement

Manual evaluation of assessments is:
- Time-consuming
- Inconsistent
- Hard to scale
- Lacks structured insights

Purely automated evaluation lacks:
- Context awareness
- Human judgment
- Trust and transparency

This project aims to **combine AI automation with human validation** to produce **accurate, explainable, and reliable assessment reports**.

---

## 4. Scope

### In Scope
- Uploading documents containing multiple questions and answers
- AI-based answer evaluation
- Human clarification and validation
- Score calculation
- Strength and weakness analysis
- Final report generation
- Interactive UI

### Out of Scope
- Exam proctoring
- Cheating detection
- Long-term user tracking
- Integration with LMS platforms (initial phase)

---

## 5. Target Users

| User Type    | Description                     |
| ------------ | ------------------------------- |
| Educators    | Evaluating tests or assignments |
| Interviewers | Assessing candidate responses   |
| Trainers     | Measuring learning outcomes     |
| HR Teams     | Skill assessment                |
| Individuals  | Self-evaluation and learning    |

---

## 6. Functional Requirements

### 6.1 Document Upload

- The system shall allow users to upload documents (PDF / DOCX / TXT)
- Documents shall contain:
  - Questions
  - Expected answers (optional)
  - User-provided answers
- The system shall validate document format

---

### 6.2 Question Parsing & Structuring

- The system shall extract:
  - Question text
  - User answer
  - Reference answer (if available)
- The system shall structure extracted data into a standardized format

---

### 6.3 AI-Based Evaluation

- The system shall use OpenAI models to:
  - Evaluate correctness of answers
  - Assign partial or full scores
  - Detect ambiguous or subjective answers
- The system shall explain:
  - Why an answer is correct or incorrect

---

### 6.4 Human-in-the-Loop Interaction

- The system shall:
  - Ask the human user for clarification when confidence is low
  - Allow users to override AI decisions
  - Accept additional input or corrections
- Human input shall be recorded and factored into final scoring

---

### 6.5 Scoring Logic

- The system shall:
  - Assign scores per question
  - Calculate total score
  - Support configurable scoring weights
- The system shall differentiate:
  - Correct answers
  - Incorrect answers
  - Partially correct answers

---

### 6.6 Strength & Weakness Analysis

- The system shall analyze responses to identify:
  - Strong knowledge areas
  - Weak or improvement areas
- The analysis shall be grouped by:
  - Topic
  - Skill
  - Question type

---

### 6.7 Final Report Generation

- The system shall generate a final report including:
  - Total score
  - Question-wise evaluation
  - Correct vs incorrect answers
  - Strengths and weaknesses
  - AI explanations
  - Human adjustments
- Reports shall be exportable (PDF / Markdown)

---

## 7. Workflow Orchestration Requirements

- The system shall use **LangGraph** to define workflow states:
  - Document ingestion
  - AI evaluation
  - Human validation
  - Re-evaluation
  - Report generation
- The workflow shall support conditional branching:
  - Proceed automatically if confidence is high
  - Pause for human input if confidence is low

---

## 8. User Interface Requirements

- The system shall provide a **Streamlit-based UI**
- The UI shall allow:
  - Document upload
  - Viewing extracted questions and answers
  - Entering human feedback
  - Reviewing AI decisions
  - Downloading final reports

---

## 9. Non-Functional Requirements

### Performance
- Document processing under 30 seconds for typical inputs
- Interactive human feedback without page reloads

### Usability
- Clear explanation of AI decisions
- Simple, guided workflow

### Reliability
- Graceful handling of malformed documents
- Safe retries for AI calls

### Security
- Uploaded documents processed in-session only
- No long-term storage unless explicitly enabled

---

## 10. Technology Stack

- **Frontend**: Streamlit
- **LLM**: OpenAI
- **Orchestration**: LangChain + LangGraph
- **Document Parsing**: Python libraries (PDF/DOCX parsers)
- **Reporting**: Markdown / PDF generation

---

## 11. Success Criteria

- Accurate extraction of questions and answers
- Clear and explainable AI evaluations
- Effective human-in-the-loop interaction
- Structured final reports
- Positive user feedback on clarity and usefulness

---

## 12. Risks & Mitigations

| Risk                | Mitigation                |
| ------------------- | ------------------------- |
| AI misjudgment      | Human validation step     |
| Ambiguous questions | User clarification        |
| Over-automation     | Manual override option    |
| Model hallucination | Strict prompt constraints |

---

## 13. Future Enhancements

- Topic-wise skill scoring
- Comparison across multiple candidates
- Analytics dashboards
- Multi-language support
- Persistent user profiles

---

## 14. Summary

This project delivers a **simple yet powerful workflow automation system** that combines **AI evaluation with human judgment**. It demonstrates real-world use of **OpenAI, Streamlit, LangChain, and LangGraph**, while producing meaningful, explainable assessment reports suitable for education, hiring, and training use cases.

---