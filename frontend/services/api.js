const API_BASE_URL = 'http://localhost:8000/api/v1';

export const sendChatMessage = async (message, sessionId) => {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message: message,
      session_id: sessionId,
    }),
  });
  
  return response.json();
};