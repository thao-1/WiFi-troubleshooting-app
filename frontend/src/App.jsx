import React, { useState } from 'react';
import ChatbotIcon from './components/ChatbotIcon';
import { useWifiBot } from './hooks/useWifiBot';

const App = () => {
  const [inputValue, setInputValue] = useState('');
  const { messages, isLoading, isTesting, sendMessage, showInitialOptions, conversationEnded } = useWifiBot();

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputValue.trim()) {
      sendMessage(inputValue);
      setInputValue('');
    }
  };

  const handleOptionClick = (option) => {
    sendMessage(option);
  };

  return (
    <div className="container">
      <div className="chatbot-popup">
        {/* Chatbot Header */}
        <div className="chat-header">
          <div className="header-info">
            <ChatbotIcon />
            <h2 className="logo-text">WiFi Helper</h2>
          </div>
          <button className="material-symbols-outlined button">
            keyboard_arrow_down
          </button>
        </div>

        {/* Chatbot Body */}
        <div className="chat-body">
          {messages.length === 0 && (
            <div className="message bot-message">
              <ChatbotIcon />
              <div className="message-content">
                <p className="message-text">
                  Hey there! <br /> How can I help you with your WiFi today?
                </p>
                {showInitialOptions && (
                  <div className="option-buttons">
                    <button 
                      className="option-btn" 
                      onClick={() => handleOptionClick("My WiFi is slow")}
                    >
                      My WiFi is slow
                    </button>
                    <button 
                      className="option-btn" 
                      onClick={() => handleOptionClick("I can't connect to WiFi")}
                    >
                      I can't connect to WiFi
                    </button>
                    <button 
                      className="option-btn" 
                      onClick={() => handleOptionClick("My WiFi keeps disconnecting")}
                    >
                      My WiFi keeps disconnecting
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
          
          {messages.map((msg, index) => (
            <div key={index} className={`message ${msg.isUser ? 'user-message' : 'bot-message'}`}>
              {!msg.isUser && <ChatbotIcon />}
              <p className="message-text">{msg.content}</p>
            </div>
          ))}
          
          {isTesting && (
            <div className="message bot-message">
              <ChatbotIcon />
              <p className="message-text">🔍 Testing your connection... Please wait.</p>
            </div>
          )}
          
          {isLoading && (
            <div className="message bot-message">
              <ChatbotIcon />
              <p className="message-text">Thinking...</p>
            </div>
          )}
        </div>

        {/* Chatbot Footer */}
        <div className="chat-footer">
          {conversationEnded ? (
            <div className="chat-ended-message" style={{ color: '#888', textAlign: 'center', padding: '0.5rem 0' }}>
              This conversation has ended. Please start a new session if you need more help.
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="chat-form">
              <input 
                type="text" 
                placeholder="Message..."
                className="message-input" 
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                disabled={isLoading}
              />
              <button type="submit" className="material-symbols-outlined" disabled={isLoading}>
                arrow_upward
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default App;

