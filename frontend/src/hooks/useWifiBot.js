import { useState, useCallback, useEffect } from 'react';
import { sendChatMessage } from '../services/api';
import { WiFiTester } from '../services/wifiTesting';

export const useWifiBot = () => {
    const [messages, setMessages] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [isTesting, setIsTesting] = useState(false);
    const [sessionId] = useState('session_' + Date.now());
    const [showInitialOptions, setShowInitialOptions] = useState(true);
    const [conversationEnded, setConversationEnded] = useState(false);
    const [pendingQuestion, setPendingQuestion] = useState(null);

    const wifiTester = new WiFiTester();

    const addMessage = useCallback((content, isUser = false) => {
        setMessages(prev => [...prev, {
            content,
            isUser,
            timestamp: new Date().toISOString()
        }]);
    }, []);

    // Automatically run test and send results after greeting
    useEffect(() => {
        if (messages.length === 1 && messages[0].isUser && !conversationEnded) {
            (async () => {
                setIsTesting(true);
                const autoData = await wifiTester.gatherAutomaticData();
                const autoTestResults = wifiTester.formatAutoTestResults(autoData);
                setIsTesting(false);
                // Send empty message, but with autoTestResults
                setIsLoading(true);
                try {
                    const response = await sendChatMessage("", sessionId, autoTestResults);
                    if (response.message) addMessage(response.message);
                    if (response.next_question && !response.is_conversation_ended) {
                        setPendingQuestion(response.next_question);
                    } else {
                        setPendingQuestion(null);
                    }
                    setConversationEnded(!!response.is_conversation_ended);
                } catch (error) {
                    addMessage('Sorry, I encountered an error. Please try again.');
                } finally {
                    setIsLoading(false);
                }
            })();
        }
    }, [messages, conversationEnded, sessionId, addMessage]);

    const sendMessage = useCallback(async (message) => {
        if (!message.trim() || conversationEnded) return;

        // Hide options after first message
        setShowInitialOptions(false);

        addMessage(message, true);
        setIsLoading(true);

        try {
            let autoTestResults = null;
            // On first message, run tests
            if (messages.length === 0) {
                setIsTesting(true);
                const autoData = await wifiTester.gatherAutomaticData();
                autoTestResults = wifiTester.formatAutoTestResults(autoData);
                setIsTesting(false);
            }
            const response = await sendChatMessage(message, sessionId, autoTestResults);
            if (response.message) addMessage(response.message);
            if (response.next_question && !response.is_conversation_ended) {
                setPendingQuestion(response.next_question);
            } else {
                setPendingQuestion(null);
            }
            setConversationEnded(!!response.is_conversation_ended);
        } catch (error) {
            addMessage('Sorry, I encountered an error. Please try again.');
        } finally {
            setIsLoading(false);
        }
    }, [messages.length, sessionId, addMessage, conversationEnded]);

    // Show pending question as soon as it is set
    useEffect(() => {
        if (pendingQuestion) {
            addMessage(pendingQuestion);
            setPendingQuestion(null);
        }
    }, [pendingQuestion, addMessage]);

    return {
        messages,
        isLoading,
        isTesting,
        sendMessage,
        addMessage,
        showInitialOptions,
        conversationEnded
    };
};
