# Tutorial 05: Building the Streamlit UI

Welcome to Tutorial 05! Now we'll create the interactive web interface that brings our AI assessment system to life.

---

## What You'll Learn

- **Streamlit basics** - Building web apps with Python
- **Session state** - Managing data across page interactions
- **File uploads** - Handling document uploads
- **Multi-page apps** - Creating a workflow with multiple steps
- **Custom styling** - Making it look professional

---

## What is Streamlit?

**Streamlit** is a Python library that turns scripts into web apps with minimal code. No HTML, CSS, or JavaScript required!

### Why Streamlit?

- ✅ **Pure Python** - No web development experience needed
- ✅ **Fast** - Build apps in minutes, not days
- ✅ **Interactive** - Automatic UI updates
- ✅ **Beautiful** - Professional-looking by default

### Hello World Example

```python
import streamlit as st

st.title("Hello World!")
st.write("This is a Streamlit app")

name = st.text_input("What's your name?")
if name:
    st.write(f"Hello, {name}!")
```

That's it! Run with: `streamlit run app.py`

---

## Our UI Structure

We have a **5-page workflow**:

1. **Upload** - Upload document or paste text
2. **Review** - View extracted questions
3. **Evaluate** - See AI evaluation results
4. **Human Review** - Provide feedback on flagged questions
5. **Report** - View final assessment report

---

## Session State

### The Problem

Streamlit reruns your entire script on every interaction. How do we preserve data?

### The Solution: Session State

```python
import streamlit as st

# Initialize
if 'count' not in st.session_state:
    st.session_state.count = 0

# Use
st.write(f"Count: {st.session_state.count}")

# Update
if st.button("Increment"):
    st.session_state.count += 1
    st.rerun()  # Refresh the page
```

### Our Session State

```python
def initialize_session_state():
    if 'workflow_result' not in st.session_state:
        st.session_state.workflow_result = None
    if 'human_feedback' not in st.session_state:
        st.session_state.human_feedback = {}
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "upload"
```

---

## Page 1: Document Upload

### File Upload Widget

```python
uploaded_file = st.file_uploader(
    "Choose a document file",
    type=['txt', 'pdf', 'docx'],
    help="Upload a document with Q&A pairs"
)
```

### Text Area for Direct Input

```python
text_input = st.text_area(
    "Or paste text directly",
    height=200,
    placeholder="Q: Question?\nA: Answer"
)
```

### Processing the Document

```python
if st.button("Process Document", type="primary"):
    with st.spinner("Processing..."):
        workflow = AssessmentWorkflow()
        
        if uploaded_file:
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(uploaded_file.getvalue())
                result = workflow.run(document_path=tmp.name)
        else:
            result = workflow.run(document_text=text_input)
        
        # Store in session state
        st.session_state.workflow_result = result
        st.session_state.current_page = "review"
        st.rerun()
```

---

## Page 2: Review Questions

### Displaying Questions

```python
questions = result["questions"]

for i, q in enumerate(questions, 1):
    st.markdown(f"### Question {i}")
    st.write(f"**Q:** {q.text}")
    st.write(f"**Answer:** {q.user_answer}")
    if q.reference_answer:
        st.write(f"**Expected:** {q.reference_answer}")
    st.write(f"**Type:** {q.question_type.value}")
    st.write(f"**Max Score:** {q.max_score}")
    st.markdown("---")
```

### Navigation Buttons

```python
col1, col2 = st.columns(2)
with col1:
    if st.button("← Back"):
        st.session_state.current_page = "upload"
        st.rerun()
with col2:
    if st.button("Continue →", type="primary"):
        st.session_state.current_page = "evaluate"
        st.rerun()
```

---

## Page 3: AI Evaluation Results

### Metrics Display

```python
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Score", f"{assessment.total_score:.1f}")
with col2:
    st.metric("Max Possible", f"{assessment.max_possible_score:.1f}")
with col3:
    st.metric("Percentage", f"{assessment.percentage:.1f}%")
with col4:
    st.metric("Correct", f"{correct_count}/{total}")
```

### Displaying Evaluations

```python
for q, e in zip(questions, evaluations):
    # Question
    st.markdown(f"### {q.text}")
    st.write(f"**Answer:** {q.user_answer}")
    
    # Evaluation
    score_pct = (e.score / q.max_score) * 100
    
    # Color-coded score
    if score_pct >= 80:
        st.success(f"Score: {e.score}/{q.max_score} ✅")
    elif score_pct >= 60:
        st.warning(f"Score: {e.score}/{q.max_score} ⚠️")
    else:
        st.error(f"Score: {e.score}/{q.max_score} ❌")
    
    st.write(f"**Confidence:** {e.confidence:.0%}")
    st.write(f"**Explanation:** {e.explanation}")
    
    if e.needs_human_review:
        st.warning("⚠️ This question needs human review")
    
    st.markdown("---")
```

---

## Page 4: Human Review

### Collecting Feedback

```python
for q_id in questions_needing_review:
    q = questions[q_id]
    e = evaluations[q_id]
    
    st.markdown(f"### {q.text}")
    st.write(f"**Student Answer:** {q.user_answer}")
    st.write(f"**AI Score:** {e.score} (Confidence: {e.confidence:.0%})")
    st.write(f"**AI Explanation:** {e.explanation}")
    
    # Human input
    col1, col2 = st.columns([1, 2])
    with col1:
        override_score = st.number_input(
            "Your Score",
            min_value=0.0,
            max_value=float(q.max_score),
            value=float(e.score),
            key=f"score_{q_id}"
        )
    with col2:
        notes = st.text_area(
            "Notes",
            key=f"notes_{q_id}"
        )
    
    # Store feedback
    st.session_state.human_feedback[q_id] = {
        "score": override_score,
        "notes": notes
    }
```

### Submitting Reviews

```python
if st.button("Submit Reviews", type="primary"):
    # Update workflow with human feedback
    result["human_feedback"] = st.session_state.human_feedback
    
    # Regenerate report
    workflow = AssessmentWorkflow()
    final_state = workflow._finalize_scores(result)
    final_state = workflow._generate_report(final_state)
    
    st.session_state.workflow_result = final_state
    st.session_state.current_page = "report"
    st.rerun()
```

---

## Page 5: Final Report

### Overall Score Display

```python
st.markdown(f"""
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            padding: 2rem; border-radius: 1rem; color: white; text-align: center;">
    <h2 style="font-size: 3rem;">{assessment.percentage:.1f}%</h2>
    <p>Score: {assessment.total_score:.1f}/{assessment.max_possible_score:.1f}</p>
</div>
""", unsafe_allow_html=True)
```

### Strengths and Weaknesses

```python
if report.strengths:
    st.markdown("### 💪 Strengths")
    for strength in report.strengths:
        st.success(f"**{strength.category}**: {strength.description}")

if report.weaknesses:
    st.markdown("### 📈 Areas for Improvement")
    for weakness in report.weaknesses:
        st.warning(f"**{weakness.category}**: {weakness.description}")
```

### Download Report

```python
markdown_report = report.to_markdown()

st.download_button(
    label="📄 Download Report",
    data=markdown_report,
    file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
    mime="text/markdown"
)
```

---

## Custom Styling

### Adding CSS

```python
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .question-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)
```

### Using Custom Styles

```python
st.markdown('<div class="main-header">My Title</div>', unsafe_allow_html=True)
```

---

## Sidebar Navigation

```python
with st.sidebar:
    st.header("Navigation")
    
    steps = {
        "upload": "1️⃣ Upload",
        "review": "2️⃣ Review",
        "evaluate": "3️⃣ Evaluate",
        "human_review": "4️⃣ Review",
        "report": "5️⃣ Report"
    }
    
    current = st.session_state.current_page
    for key, label in steps.items():
        if key == current:
            st.markdown(f"**→ {label}**")
        else:
            st.markdown(f"   {label}")
```

---

## Running the App

### Start the Server

```bash
streamlit run ui/streamlit_app.py
```

### Access the App

Open your browser to: `http://localhost:8501`

### Stop the Server

Press `Ctrl+C` in the terminal

---

## Common Streamlit Widgets

### Input Widgets

```python
# Text input
name = st.text_input("Name")

# Number input
age = st.number_input("Age", min_value=0, max_value=120)

# Text area
bio = st.text_area("Bio", height=200)

# Select box
choice = st.selectbox("Choose", ["A", "B", "C"])

# Slider
value = st.slider("Value", 0, 100, 50)

# Checkbox
agree = st.checkbox("I agree")

# Button
if st.button("Click me"):
    st.write("Clicked!")
```

### Display Widgets

```python
# Text
st.write("Simple text")
st.markdown("**Bold** text")
st.title("Title")
st.header("Header")
st.subheader("Subheader")

# Metrics
st.metric("Score", "85%", "+5%")

# Messages
st.success("Success!")
st.info("Info")
st.warning("Warning")
st.error("Error")

# Progress
st.progress(0.75)
st.spinner("Loading...")
```

### Layout Widgets

```python
# Columns
col1, col2 = st.columns(2)
with col1:
    st.write("Left")
with col2:
    st.write("Right")

# Expander
with st.expander("Click to expand"):
    st.write("Hidden content")

# Tabs
tab1, tab2 = st.tabs(["Tab 1", "Tab 2"])
with tab1:
    st.write("Content 1")
with tab2:
    st.write("Content 2")

# Container
with st.container():
    st.write("Grouped content")
```

---

## Best Practices

### 1. Use Session State for Data Persistence

```python
# ✅ Good
st.session_state.data = result

# ❌ Bad
global_data = result  # Won't persist across reruns
```

### 2. Minimize Reruns

```python
# ✅ Good - Only rerun when needed
if st.button("Process"):
    process_data()
    st.rerun()

# ❌ Bad - Unnecessary reruns
st.rerun()  # Don't call without reason
```

### 3. Use Keys for Widgets

```python
# ✅ Good - Unique keys
st.text_input("Name", key="user_name")
st.text_input("Name", key="other_name")

# ❌ Bad - Duplicate keys cause errors
st.text_input("Name")
st.text_input("Name")  # Error!
```

### 4. Handle Loading States

```python
# ✅ Good
with st.spinner("Processing..."):
    result = long_running_function()

# ❌ Bad - No feedback
result = long_running_function()  # User sees nothing
```

---

## Testing Your UI

### Test 1: Upload a File

1. Start the app
2. Upload `tests/sample_documents/python_quiz.txt`
3. Click "Process Document"
4. Verify questions are extracted

### Test 2: Review Workflow

1. Navigate through all pages
2. Check that data persists
3. Verify navigation works

### Test 3: Human Review

1. Process a document
2. Check if any questions need review
3. Provide feedback
4. Verify scores update

### Test 4: Download Report

1. Complete an assessment
2. Go to report page
3. Download the report
4. Verify content is correct

---

## Common Issues

### Issue: "Session state not persisting"

**Solution**: Make sure you're using `st.session_state`, not regular variables

### Issue: "Widget key error"

**Solution**: Ensure all widgets have unique keys

### Issue: "Page not updating"

**Solution**: Call `st.rerun()` after state changes

### Issue: "File upload not working"

**Solution**: Check file type restrictions and temp file handling

---

## Next Steps

Congratulations! You now have a complete, interactive web interface for your AI assessment system.

You've learned:
- ✅ Streamlit basics
- ✅ Session state management
- ✅ Multi-page workflows
- ✅ File uploads
- ✅ Custom styling

Next, we'll add **reporting and analysis** features to generate comprehensive assessment reports!

Continue to: **[Tutorial 06: Reporting](06_reporting.md)**

---

## Quick Reference

### Start App
```bash
streamlit run ui/streamlit_app.py
```

### Session State
```python
st.session_state.key = value
value = st.session_state.key
```

### Navigation
```python
st.session_state.current_page = "page_name"
st.rerun()
```

### File Upload
```python
file = st.file_uploader("Upload", type=['txt', 'pdf'])
if file:
    content = file.getvalue()
```
