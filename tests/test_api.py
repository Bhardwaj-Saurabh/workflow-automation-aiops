"""
Unit tests for API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from src.api import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint."""
    
    def test_health_check(self, client):
        """Test health check returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestDocumentUpload:
    """Tests for document upload endpoints."""
    
    def test_submit_text(self, client):
        """Test submitting text directly."""
        text = """
Q: What is Python?
A: A programming language
"""
        response = client.post("/api/v1/submit-text", params={"text": text})
        
        assert response.status_code == 200
        data = response.json()
        assert "workflow_id" in data
        assert "questions" in data
        assert len(data["questions"]) == 1
    
    def test_submit_empty_text(self, client):
        """Test submitting empty text."""
        response = client.post("/api/v1/submit-text", params={"text": ""})
        
        # Should still return 200 but with 0 questions
        assert response.status_code == 200
        data = response.json()
        assert len(data["questions"]) == 0


class TestWorkflowEndpoints:
    """Tests for workflow management endpoints."""
    
    def test_get_nonexistent_workflow(self, client):
        """Test getting a workflow that doesn't exist."""
        response = client.get("/api/v1/workflow/nonexistent-id")
        assert response.status_code == 404
    
    def test_list_workflows(self, client):
        """Test listing all workflows."""
        response = client.get("/api/v1/workflows")
        assert response.status_code == 200
        data = response.json()
        assert "workflows" in data
        assert isinstance(data["workflows"], list)
    
    def test_workflow_lifecycle(self, client):
        """Test complete workflow lifecycle."""
        # 1. Submit text
        text = """
Q: What is 2+2?
A: 4
"""
        response = client.post("/api/v1/submit-text", params={"text": text})
        assert response.status_code == 200
        workflow_id = response.json()["workflow_id"]
        
        # 2. Get workflow status
        response = client.get(f"/api/v1/workflow/{workflow_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "parsed"
        
        # 3. Start evaluation (will run in background)
        response = client.post("/api/v1/evaluate", json={"workflow_id": workflow_id})
        assert response.status_code == 200
        
        # Note: In real tests, you'd mock the AI evaluator
        # to avoid actual API calls and async complexity
