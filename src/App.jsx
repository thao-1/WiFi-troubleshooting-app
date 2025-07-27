import React from 'react'
import ChatbotIcon from './components/ChatbotIcon';

const App = () => {
  return <div className="container">
    <div className="chatbot-popup">
      {/* Chatbot Header */}
      <div className="chat-header">
        <div className="header-info">
          <ChatbotIcon />
          <h2 className="logo-text">Chatbot</h2>
        </div>
        <button className="material-symbols-outlined"> arrow_downward
        </button>
      </div>

      {/* Chatbot Body */}
      <div className="chat-body">
        <div className="message bot-message">
          <ChatbotIcon />
          <p className="message-text">
            Hey there! <br /> How can I help you today?
          </p>
        </div>
        <div className="message user-message">
          <p className="message-text">
            User message
          </p>
        </div>

        {/* Chatbot Footer */}
        <div className="chat-footer">
          <form action="#" className="chat-form">
            <input type="text" placeholder="Message..."
              className="message-input" required />
            <button className="material-symbols-outlined">arrow_upward</button>
          </form>
        </div>
      </div>
    </div>
  </div>
}

export default App;