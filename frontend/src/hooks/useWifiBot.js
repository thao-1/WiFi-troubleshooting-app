import { useState, useCallback } from 'react';
import { sendChatMessage } from '../services/api';
import { WiFiTester } from '../services/wifiTesting';

export const useWifiBot = () => {
    const [messages, setMessages] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [isTesting, setIsTesting] = useState(false);
    const [sessionId] = useState('session_' + Date.now());
    const [showInitialOptions, setShowInitialOptions] = useState(true);

    const wifiTester = new WiFiTester();

    const addMessage = useCallback((content, isUser = false) => {
        setMessages(prev => [...prev, {
            content,
            isUser,
            timestamp: new Date().toISOString()
        }]);
    }, []);

    const sendMessage = useCallback(async (message) => {
        if (!message.trim()) return;

        // Hide options after first message
        setShowInitialOptions(false);
        
        addMessage(message, true);
        setIsLoading(true);

        try{
            let autoTestResults = null;

            // Run tests on first message
            if (messages.length === 0) {
                setIsTesting(true);
                const autoData = await wifiTester.gatherAutomaticData();
                autoTestResults = wifiTester.formatAutoTestResults(autoData);
                setIsTesting(false);
            }

            const response = await sendChatMessage(message, sessionId, autoTestResults);
            addMessage(response.message);
        }   catch (error) {
            addMessage('Sorry, I encountered an error. Please try again.');
        }   finally {
            setIsLoading(false);
        }
    }, [messages.length, sessionId, addMessage]);

    return {
        messages,
        isLoading,
        isTesting,
        sendMessage,
        addMessage,
        showInitialOptions
    };
};
