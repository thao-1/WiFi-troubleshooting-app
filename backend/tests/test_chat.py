import pytest
from httpx import AsyncClient
from app.main import app
from app.routes.chat import sessions, ConversationState


class TestChatFlow:
    
    @pytest.fixture
    def client(self):
        return AsyncClient(app=app, base_url="http://test")

    @pytest.mark.asyncio
    async def test_initial_greeting(self, client):
        """Test that initial greeting returns proper welcome message"""
        response = await client.post("/chat", json={"message": "Hello", "session_id": "test_session_1"})
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Got it. Running a quick test on your network..." in data["message"]

    @pytest.mark.asyncio
    async def test_auto_test_results_format(self, client):
        """Test that auto test results are properly formatted and returned"""
        session_id = "test_session_2"
        
        # First message to establish session
        await client.post("/chat", json={"message": "My WiFi is slow", "session_id": session_id})
        
        # Second message with test results
        test_results = {
            "connectivity": {"connected": True},
            "speed": {"speed": 25.5, "latency": 45},
            "connectionInfo": {"type": "wifi"},
            "deviceType": "desktop"
        }
        
        response = await client.post("/chat", json={
            "message": "", 
            "session_id": session_id,
            "auto_test_results": test_results
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "25.5 Mbps" in data["message"]  # Speed should be in results
        assert "45 ms" in data["message"]  # Latency should be in results

    @pytest.mark.asyncio
    async def test_null_test_results_handling(self, client):
        """Test that null test results are handled gracefully"""
        session_id = "test_session_3"
        
        await client.post("/chat", json={"message": "WiFi issues", "session_id": session_id})
        
        response = await client.post("/chat", json={
            "message": "", 
            "session_id": session_id,
            "auto_test_results": None
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "0 Mbps" in data["message"]  # Should handle null gracefully

    @pytest.mark.asyncio
    async def test_follow_up_questions_flow(self, client):
        """Test that follow-up questions are properly generated"""
        session_id = "test_session_4"
        
        # Initial message
        await client.post("/chat", json={"message": "Slow internet", "session_id": session_id})
        
        # Test results
        test_results = {
            "connectivity": {"connected": True},
            "speed": {"speed": 5.0, "latency": 150},
            "connectionInfo": {"type": "wifi"},
            "deviceType": "desktop"
        }
        
        response = await client.post("/chat", json={
            "message": "", 
            "session_id": session_id,
            "auto_test_results": test_results
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "next_question" in data or len(data["message"]) > 50  # Should have follow-up

    def test_session_management(self):
        """Test that sessions are properly managed"""
        session_id = "test_session_5"
        
        # Create new session
        from app.routes.chat import ChatSession
        session = ChatSession()
        sessions[session_id] = session
        
        assert session_id in sessions
        assert session.state == ConversationState.GREETING
        assert session.issue_description is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
