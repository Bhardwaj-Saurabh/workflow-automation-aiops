# AI-Assisted Assessment Evaluation System

> **An intelligent workflow automation system that evaluates question-and-answer documents using AI, with human-in-the-loop validation.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![OpenAI](https://img.shields.io/badge/OpenAI-API-green.svg)](https://openai.com/)
[![LangChain](https://img.shields.io/badge/LangChain-🦜-yellow.svg)](https://langchain.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-UI-red.svg)](https://streamlit.io/)

---

## 🎯 What Does This Do?

This system automates the evaluation of assessments, quizzes, and interviews by:
1. **📄 Parsing** uploaded documents to extract questions and answers
2. **🤖 Evaluating** answers using OpenAI's AI models
3. **👤 Validating** uncertain evaluations with human reviewers
4. **📊 Generating** comprehensive assessment reports with insights

Perfect for educators, interviewers, trainers, and anyone who needs to evaluate written responses at scale.

---

## ✨ Key Features

- **🚀 Automated Evaluation**: AI evaluates answers in seconds
- **🧠 Human-in-the-Loop**: Keeps humans in control for subjective decisions
- **📈 Confidence Scoring**: AI knows when it needs help
- **💡 Explainable Results**: Every score comes with an explanation
- **📑 Multiple Formats**: Supports PDF, DOCX, and TXT documents
- **🎨 Interactive UI**: User-friendly Streamlit interface
- **📊 Detailed Reports**: Strengths, weaknesses, and actionable insights

---

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Upload    │────▶│    Parse     │────▶│ AI Evaluate │
│  Document   │     │  Questions   │     │  (OpenAI)   │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                 │
                                          ┌──────▼──────┐
                                          │  Confidence │
                                          │   Check     │
                                          └──────┬──────┘
                                                 │
                                    ┌────────────┴────────────┐
                                    │                         │
                              ┌─────▼─────┐           ┌──────▼──────┐
                              │   High    │           │     Low     │
                              │Confidence │           │ Confidence  │
                              └─────┬─────┘           └──────┬──────┘
                                    │                        │
                                    │                 ┌──────▼──────┐
                                    │                 │   Human     │
                                    │                 │   Review    │
                                    │                 └──────┬──────┘
                                    │                        │
                                    └────────┬───────────────┘
                                             │
                                      ┌──────▼──────┐
                                      │  Generate   │
                                      │   Report    │
                                      └─────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Installation

```bash
# Clone the repository
git clone https://github.com/Bhardwaj-Saurabh/workflow-automation-aiops.git
cd workflow-automation-aiops

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## 🚀 Deployment

### Microservices Architecture

The application uses a microservices architecture with separate frontend and backend services:

```
Frontend (Streamlit) → Backend API (FastAPI) → OpenAI
```

### Docker Compose (Recommended for Local)

Run both services with one command:

```bash
# Set environment variables
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Start both services
docker-compose up -d

# Frontend: http://localhost:8501
# Backend API: http://localhost:8000/docs
```

See [Docker Deployment Guide](docs/deployment/docker.md) for details.

### Kubernetes with Helm

Deploy to Kubernetes cluster with separate frontend and backend deployments:

```bash
# Build and push images
docker build -f Dockerfile.backend -t ghcr.io/yourusername/ai-assessment-backend:1.0.0 .
docker build -f Dockerfile.frontend -t ghcr.io/yourusername/ai-assessment-frontend:1.0.0 .
docker push ghcr.io/yourusername/ai-assessment-backend:1.0.0
docker push ghcr.io/yourusername/ai-assessment-frontend:1.0.0

# Deploy with Helm
helm install ai-assessment ./helm \
  --namespace ai-assessment \
  --create-namespace \
  --set backend.image.repository=ghcr.io/yourusername/ai-assessment-backend \
  --set frontend.image.repository=ghcr.io/yourusername/ai-assessment-frontend \
  --set secrets.openaiApiKey=$OPENAI_API_KEY

# Access application
kubectl port-forward svc/ai-assessment-frontend 8501:80 -n ai-assessment
```

See [Kubernetes Deployment Guide](docs/deployment/kubernetes.md) for details.

### Automated Deployment

Use the deployment script:

```bash
./scripts/deploy.sh prod 1.0.0
```

### Service Endpoints

- **Frontend UI**: Port 8501 (public)
- **Backend API**: Port 8000 (internal)
  - Swagger UI: `/docs`
  - Health check: `/health`
  - API endpoints: `/api/v1/*`

---

## 📚 Tutorial Series

**New to AI development?** Follow our step-by-step tutorials:

1. **[Getting Started](docs/tutorial/01_getting_started.md)** - Setup and AI basics
2. **[Document Formats](docs/tutorial/02_document_formats.md)** - Data models and parsing
3. **[AI Evaluation](docs/tutorial/03_ai_evaluation.md)** - OpenAI integration
4. **[Workflow Orchestration](docs/tutorial/04_workflow_orchestration.md)** - LangGraph workflows
5. **[Building the UI](docs/tutorial/05_building_ui.md)** - Streamlit interface
6. **[Reporting](docs/tutorial/06_reporting.md)** - Analysis and reports
7. **[Testing](docs/tutorial/07_testing.md)** - Quality assurance
8. **[Deployment](docs/tutorial/08_deployment.md)** - Going live

---

## 📖 Documentation

- **[Business Requirements](docs/business_requirements.md)** - Detailed project specifications
- **[Architecture Guide](docs/architecture.md)** - System design and components
- **[API Documentation](docs/api.md)** - Code reference

---

## 🛠️ Technology Stack

| Component            | Technology            | Purpose                        |
| -------------------- | --------------------- | ------------------------------ |
| **AI Model**         | OpenAI GPT-4          | Answer evaluation and analysis |
| **Orchestration**    | LangChain + LangGraph | Workflow management            |
| **Frontend**         | Streamlit             | Interactive web interface      |
| **Document Parsing** | PyPDF2, python-docx   | Extract text from documents    |
| **Reporting**        | ReportLab, Markdown   | Generate PDF/MD reports        |
| **Data Validation**  | Pydantic              | Type-safe data models          |

---

## 📁 Project Structure

```
workflow-automation-aiops/
├── src/                      # Core application code
│   ├── models.py            # Data models (Question, Evaluation, Report)
│   ├── document_parser.py   # Document processing logic
│   ├── ai_evaluator.py      # OpenAI evaluation engine
│   ├── workflow.py          # LangGraph workflow orchestration
│   └── report_generator.py  # Report generation
├── ui/
│   └── streamlit_app.py     # Streamlit web interface
├── tests/
│   └── sample_documents/    # Example test files
├── docs/
│   ├── business_requirements.md
│   ├── tutorial/            # Step-by-step guides
│   └── architecture.md
├── .env.example             # Environment template
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

---

## 🎓 Use Cases

- **📚 Education**: Grade assignments and quizzes automatically
- **💼 Hiring**: Evaluate candidate interview responses
- **🎯 Training**: Assess learning outcomes and knowledge retention
- **🔍 Research**: Analyze survey responses at scale
- **✅ Self-Assessment**: Get instant feedback on your answers

---

## 🔒 Security & Privacy

- Documents are processed in-session only (no persistent storage)
- API keys stored securely in `.env` (never committed to Git)
- All data transmission encrypted via HTTPS
- Configurable data retention policies

---

## 🤝 Contributing

Contributions are welcome! This is a learning project, so beginner-friendly PRs are encouraged.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **OpenAI** for the powerful GPT models
- **LangChain** team for the excellent orchestration framework
- **Streamlit** for making web UI development simple
- The open-source community for inspiration and tools

---

## 📧 Contact

**Saurabh Bhardwaj**
- GitHub: [@Bhardwaj-Saurabh](https://github.com/Bhardwaj-Saurabh)
- Project: [workflow-automation-aiops](https://github.com/Bhardwaj-Saurabh/workflow-automation-aiops)

---

## 🗺️ Roadmap

- [x] Phase 1: Project setup and foundation
- [x] Phase 2: Document processing
- [x] Phase 3: AI evaluation engine
- [x] Phase 4: LangGraph workflow
- [ ] Phase 5: Streamlit UI
- [ ] Phase 6: Reporting and analysis
- [ ] Phase 7: Testing
- [ ] Phase 8: Deployment

**Current Status**: Phase 1 Complete ✅

---

Made with ❤️ for educators, interviewers, and AI learners
