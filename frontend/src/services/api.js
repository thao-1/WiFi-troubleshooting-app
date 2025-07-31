const API_BASE_URL = '/api/v1';

export const sendChatMessage = async (message, sessionId, autoTestResults = null) => {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message: message,
      session_id: sessionId,
      auto_test_results: autoTestResults
    }),
  });
  
  return response.json();
};