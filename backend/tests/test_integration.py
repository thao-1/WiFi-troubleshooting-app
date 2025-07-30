import pytest
from fastapi.testclient import TestClient
from app.main import app


class TestChatIntegration:
    """Integration tests for full chat flow"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_full_chat_flow_with_real_data(self, client):
        """Test complete chat flow with real browser test data"""
        session_id = "integration_test_1"
        
        # Step 1: Initial issue description
        response = client.post("/api/v1/chat", json={
            "message": "My WiFi keeps dropping every 5 minutes",
            "session_id": session_id
        })
        assert response.status_code == 200
        data = response.json()
        assert "Running a quick test" in data["message"]

        # Step 2: Send real browser test results
        real_test_data = {
            "connectivity": {"connected": True, "latency": 85},
            "speed": {"speed": 15.7, "latency": 85},
            "connectionInfo": {"type": "wifi", "downlink": 8.5, "rtt": 85},
            "deviceType": "desktop"
        }

        response = client.post("/api/v1/chat", json={
            "message": "",
            "session_id": session_id,
            "auto_test_results": real_test_data
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "15.7" in data["message"]
        assert "85" in data["message"]
        assert "wifi" in data["message"]
        assert "questions" in data["message"].lower()

    def test_chat_flow_with_slow_connection(self, client):
        """Test chat flow with slow connection data"""
        session_id = "integration_test_2"
        
        client.post("/api/v1/chat", json={
            "message": "Internet is very slow",
            "session_id": session_id
        })

        slow_test_data = {
            "connectivity": {"connected": True},
            "speed": {"speed": 2.1, "latency": 250},
            "connectionInfo": {"type": "wifi"},
            "deviceType": "laptop"
        }

        response = client.post("/api/v1/chat", json={
            "message": "",
            "session_id": session_id,
            "auto_test_results": slow_test_data
        })

        assert response.status_code == 200
        data = response.json()
        assert "2.1" in data["message"]
        assert "250" in data["message"]
        # Should ask relevant questions about slow connection
        assert "next_question" in data

    def test_chat_flow_disconnected(self, client):
        """Test chat flow with disconnected state"""
        session_id = "integration_test_3"
        
        client.post("/api/v1/chat", json={
            "message": "Can't connect to WiFi",
            "session_id": session_id
        })

        disconnected_test_data = {
            "connectivity": {"connected": False},
            "speed": {"speed": 0, "latency": 0},
            "connectionInfo": {"type": "unknown"},
            "deviceType": "phone"
        }

        response = client.post("/api/v1/chat", json={
            "message": "",
            "session_id": session_id,
            "auto_test_results": disconnected_test_data
        })

        assert response.status_code == 200
        data = response.json()
        assert "❌ Issues detected" in data["message"]
        assert "0" in data["message"]

    def test_multiple_follow_up_questions(self, client):
        """Test that follow-up questions work sequentially"""
        session_id = "integration_test_4"
        
        # Start conversation
        client.post("/api/v1/chat", json={
            "message": "WiFi issues",
            "session_id": session_id
        })

        # Send test results
        test_data = {
            "connectivity": {"connected": True},
            "speed": {"speed": 12.3, "latency": 65},
            "connectionInfo": {"type": "wifi"},
            "deviceType": "desktop"
        }

        response = client.post("/api/v1/chat", json={
            "message": "",
            "session_id": session_id,
            "auto_test_results": test_data
        })

        assert response.status_code == 200
        first_response = response.json()
        
        # Answer first question
        response = client.post("/api/v1/chat", json={
            "message": "Yes, I have restarted the router",
            "session_id": session_id
        })
        
        assert response.status_code == 200
        second_response = response.json()
        
        # Should get different follow-up questions
        assert first_response.get("next_question") != second_response.get("message")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
