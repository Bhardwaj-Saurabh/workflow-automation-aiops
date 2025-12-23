# Tutorial 01: Getting Started with AI Assessment System

Welcome! This tutorial will guide you through building an AI-powered assessment evaluation system from scratch. Don't worry if you're new to AI - we'll explain everything step by step.

---

## What You'll Learn

By the end of this tutorial series, you'll understand:
- How to use AI (OpenAI) to evaluate answers
- What "human-in-the-loop" means and why it's important
- How to build workflows with LangGraph
- How to create interactive web apps with Streamlit

---

## What Is This Project About?

Imagine you're a teacher with 30 students who just took a test. Reading and grading all those answers takes hours! This project automates that process using AI, but keeps you (the human) in control for important decisions.

### The Problem We're Solving

**Manual evaluation is:**
- ⏰ Time-consuming
- 😕 Inconsistent (you might grade differently when tired)
- 📈 Hard to scale (what if you have 100 students?)

**Pure AI automation has issues:**
- 🤖 Can make mistakes on subjective questions
- ❓ Lacks context and human judgment
- 🔒 People don't always trust it

**Our Solution: Best of Both Worlds**
- 🚀 AI does the heavy lifting (fast evaluation)
- 👤 Human validates important decisions (quality control)
- 📊 Structured reports with explanations (transparency)

---

## How Does Human-in-the-Loop Work?

Think of it like a smart assistant:

1. **AI evaluates** most answers automatically
2. **AI checks confidence**: "Am I sure about this?"
3. **If confident** → Proceeds automatically ✅
4. **If uncertain** → Asks you for help 🤔
5. **You review** and make the final call
6. **System learns** from your feedback

This is called **human-in-the-loop AI** - the AI does the work, but humans stay in control.

---

## Project Architecture Overview

Here's how our system works:

```
┌─────────────────┐
│ Upload Document │  ← User uploads Q&A document
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Parse Questions │  ← Extract questions and answers
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  AI Evaluation  │  ← OpenAI evaluates each answer
└────────┬────────┘
         │
         ▼
    ┌───┴───┐
    │ Check │
    │Confidence│
    └───┬───┘
        │
    ┌───┴────────┐
    │            │
    ▼            ▼
  High         Low
Confidence   Confidence
    │            │
    │            ▼
    │      ┌──────────┐
    │      │  Human   │  ← You review uncertain cases
    │      │ Review   │
    │      └────┬─────┘
    │           │
    └─────┬─────┘
          │
          ▼
    ┌──────────┐
    │ Generate │  ← Create final report
    │  Report  │
    └──────────┘
```

---

## Technology Stack Explained

### 🐍 Python
The programming language we'll use. It's beginner-friendly and has great AI libraries.

### 🤖 OpenAI
The AI service that evaluates answers. Think of it as a very smart assistant that can read and understand text.

### 🔗 LangChain
A framework that makes it easier to work with AI models. It handles the boring stuff like API calls and error handling.

### 📊 LangGraph
Helps us build **workflows** (step-by-step processes). It's like creating a flowchart that actually runs.

### 🎨 Streamlit
Creates web interfaces with just Python code - no HTML/CSS needed! Perfect for building interactive apps quickly.

---

## Setting Up Your Development Environment

### Step 1: Check Python Installation

Open your terminal and run:
```bash
python --version
```

You should see Python 3.11 or higher. If not, download it from [python.org](https://python.org).

### Step 2: Navigate to Project Directory

```bash
cd /Users/saurabhbhardwaj/Desktop/projects/workflow-automation-aiops
```

### Step 3: Create Virtual Environment

A virtual environment keeps this project's dependencies separate from other projects:

```bash
python -m venv .venv
```

### Step 4: Activate Virtual Environment

**On Mac/Linux:**
```bash
source .venv/bin/activate
```

**On Windows:**
```bash
.venv\Scripts\activate
```

You should see `(.venv)` in your terminal prompt.

### Step 5: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs all the libraries we need. It might take a few minutes.

### Step 6: Get Your OpenAI API Key

1. Go to [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Sign up or log in
3. Click "Create new secret key"
4. Copy the key (it looks like `sk-...`)

**Important:** Keep this key secret! Don't share it or commit it to Git.

### Step 7: Configure Environment Variables

1. Copy the example file:
   ```bash
   cp .env.example .env
   ```

2. Open `.env` in your text editor

3. Replace `your_openai_api_key_here` with your actual API key:
   ```
   OPENAI_API_KEY=sk-your-actual-key-here
   ```

4. Save the file

---

## Project Structure

Here's what we just created:

```
workflow-automation-aiops/
├── src/                    # Core application code
│   ├── __init__.py        # Package marker
│   ├── models.py          # Data structures (coming next)
│   ├── document_parser.py # Document processing
│   ├── ai_evaluator.py    # AI evaluation logic
│   ├── workflow.py        # LangGraph workflow
│   └── report_generator.py # Report creation
├── ui/
│   └── streamlit_app.py   # Web interface
├── tests/
│   └── sample_documents/  # Test files
├── docs/
│   ├── business_requirements.md
│   └── tutorial/          # Step-by-step guides
├── .env                   # Your API keys (secret!)
├── .env.example           # Template for .env
├── .gitignore            # Files to ignore in Git
├── requirements.txt       # Python dependencies
└── README.md             # Project overview
```

---

## Testing Your Setup

Let's verify everything works:

```bash
python -c "import openai; import langchain; import streamlit; print('✅ All dependencies installed!')"
```

If you see the success message, you're ready to go!

---

## Key Concepts to Remember

### 🤖 What is an LLM (Large Language Model)?
Think of it as a very advanced autocomplete. You give it text (a "prompt"), and it generates a response. OpenAI's GPT models are LLMs.

### 💬 What is a Prompt?
Instructions you give to the AI. For example:
```
Evaluate this answer to the question "What is Python?"
Answer: "A programming language"
Is this correct? Explain why.
```

### 🎯 What is Confidence?
How sure the AI is about its answer. High confidence = probably correct. Low confidence = needs human review.

### 🔄 What is a Workflow?
A series of steps that happen in order. Like a recipe: first do this, then do that, if this happens do something else.

---

## Common Issues and Solutions

### Issue: "pip: command not found"
**Solution:** Use `pip3` instead of `pip`

### Issue: "Permission denied"
**Solution:** Don't use `sudo`. Make sure your virtual environment is activated.

### Issue: "Module not found"
**Solution:** Make sure you activated the virtual environment and ran `pip install -r requirements.txt`

### Issue: "Invalid API key"
**Solution:** Double-check your `.env` file. Make sure there are no extra spaces or quotes around the key.

---

## Next Steps

Great job! You've set up your development environment. In the next tutorial, we'll:
- Create data models to represent questions and evaluations
- Build a document parser to extract Q&A pairs
- Learn about Pydantic for data validation

Continue to: **[Tutorial 02: Document Formats and Data Models](02_document_formats.md)**

---

## Need Help?

- Check the [README.md](../../README.md) for quick reference
- Review the [Business Requirements](../business_requirements.md) to understand the big picture
- Common Python errors: [Python Documentation](https://docs.python.org/3/)
- OpenAI API help: [OpenAI Documentation](https://platform.openai.com/docs)
