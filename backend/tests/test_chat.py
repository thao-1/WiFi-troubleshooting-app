import pytest
import logging
from fastapi.testclient import TestClient
from app.main import app
from app.routes.chat import sessions, ConversationState

logger = logging.getLogger(__name__)


class TestChatFlow:
    
    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_initial_greeting(self, client):
        """Test that initial greeting returns proper welcome message"""
        logger.info("Testing initial greeting flow")
        response = client.post("/api/v1/chat", json={"message": "Hello", "session_id": "test_session_1"})
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Got it. Running a quick test on your network..." in data["message"]
        logger.info("Initial greeting test passed")

    def test_auto_test_results_format(self, client):
        """Test that auto test results are properly formatted and returned"""
        session_id = "test_session_2"
        logger.info(f"Testing auto test results format with session: {session_id}")
        
        # First message to establish session
        client.post("/api/v1/chat", json={"message": "My WiFi is slow", "session_id": session_id})
        logger.info("Established test session")
        
        # Second message with test results
        test_results = {
            "connectivity": {"connected": True},
            "speed": {"speed": 25.5, "latency": 45},
            "connectionInfo": {"type": "wifi"},
            "deviceType": "desktop"
        }
        
        response = client.post("/api/v1/chat", json={
            "message": "", 
            "session_id": session_id,
            "auto_test_results": test_results
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "25.5" in data["message"]  # Speed should be in results
        assert "45" in data["message"]  # Latency should be in results
        logger.info("Auto test results format test passed")

    def test_null_test_results_handling(self, client):
        """Test that null test results are handled gracefully"""
        session_id = "test_session_3"
        logger.info(f"Testing null test results handling with session: {session_id}")
        
        client.post("/api/v1/chat", json={"message": "WiFi issues", "session_id": session_id})
        
        response = client.post("/api/v1/chat", json={
            "message": "", 
            "session_id": session_id,
            "auto_test_results": None
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "unknown" in data["message"]  # Should handle null gracefully
        logger.info("Null test results handling test passed")

    def test_follow_up_questions_flow(self, client):
        """Test that follow-up questions are properly generated"""
        session_id = "test_session_4"
        logger.info(f"Testing follow-up questions flow with session: {session_id}")
        
        # Initial message
        client.post("/api/v1/chat", json={"message": "Slow internet", "session_id": session_id})
        
        # Test results
        test_results = {
            "connectivity": {"connected": True},
            "speed": {"speed": 5.0, "latency": 150},
            "connectionInfo": {"type": "wifi"},
            "deviceType": "desktop"
        }
        
        response = client.post("/api/v1/chat", json={
            "message": "", 
            "session_id": session_id,
            "auto_test_results": test_results
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "next_question" in data or len(data["message"]) > 50  # Should have follow-up
        logger.info("Follow-up questions flow test passed")

    def test_session_management(self):
        """Test that sessions are properly managed"""
        session_id = "test_session_5"
        logger.info(f"Testing session management with session: {session_id}")
        
        # Create new session
        from app.routes.chat import ChatSession
        session = ChatSession()
        sessions[session_id] = session
        
        assert session_id in sessions
        assert session.state == ConversationState.GREETING
        assert session.issue_description == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
