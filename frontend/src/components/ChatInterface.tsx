import React, { useState, useRef, useEffect } from 'react';
import './ChatInterface.css';

interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
    sources?: any[];
}

interface ChatInterfaceProps {
    apiUrl?: string;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
    apiUrl = 'http://localhost:8000'
}) => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputText, setInputText] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [useRAG, setUseRAG] = useState(true);
    const [conversationId, setConversationId] = useState<string | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const sendMessage = async () => {
        if (!inputText.trim() || isLoading) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: inputText,
            timestamp: new Date()
        };

        setMessages(prev => [...prev, userMessage]);
        setInputText('');
        setIsLoading(true);

        try {
            const response = await fetch(`${apiUrl}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: inputText,
                    use_rag: useRAG,
                    conversation_id: conversationId
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.conversation_id && !conversationId) {
                setConversationId(data.conversation_id);
            }

            const assistantMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: data.response,
                timestamp: new Date(),
                sources: data.sources
            };

            setMessages(prev => [...prev, assistantMessage]);
        } catch (error) {
            console.error('Error sending message:', error);
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: `Error: ${error instanceof Error ? error.message : 'Failed to send message. Please check if the backend server is running.'}`,
                timestamp: new Date()
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    const clearChat = () => {
        setMessages([]);
        setConversationId(null);
    };

    return (
        <div className="chat-container">
            <div className="chat-header">
                <h2>AI Chatbot</h2>
                <div className="chat-controls">
                    <label className="rag-toggle">
                        <input
                            type="checkbox"
                            checked={useRAG}
                            onChange={(e) => setUseRAG(e.target.checked)}
                        />
                        <span>Use Graph DB</span>
                    </label>
                    <button onClick={clearChat} className="clear-button">
                        Clear Chat
                    </button>
                </div>
            </div>

            <div className="messages-container">
                {messages.length === 0 && (
                    <div className="welcome-message">
                        <h3> Ask me about your infrastructure:</h3>
                        <p></p>
                        <ul>
                            <li>"What servers do we have?"</li>
                            <li>"Show me all applications"</li>
                            <li>"What runs on server1?"</li>
                            <li>"Which servers run Ubuntu?"</li>
                        </ul>
                    </div>
                )}

                {messages.map((message) => (
                    <div key={message.id} className={`message ${message.role}`}>
                        <div className="message-header">
                            <span className="message-role">
                                {message.role === 'user' ? '👤 You' : '🤖 Assistant'}
                            </span>
                            <span className="message-time">
                                {message.timestamp.toLocaleTimeString()}
                            </span>
                        </div>
                        <div className="message-content">
                            {message.content}
                        </div>
                        {message.sources && message.sources.length > 0 && (
                            <div className="message-sources">
                                <strong>Sources:</strong>
                                <ul>
                                    {message.sources.map((source, idx) => (
                                        <li key={idx}>{source.metadata?.title || 'Document'}</li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                ))}

                {isLoading && (
                    <div className="message assistant loading">
                        <div className="message-header">
                            <span className="message-role">🤖 Assistant</span>
                        </div>
                        <div className="message-content">
                            <div className="typing-indicator">
                                <span></span>
                                <span></span>
                                <span></span>
                            </div>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            <div className="input-container">
                <textarea
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Type your message... (Press Enter to send)"
                    disabled={isLoading}
                    rows={1}
                />
                <button
                    onClick={sendMessage}
                    disabled={isLoading || !inputText.trim()}
                    className="send-button"
                >
                    {isLoading ? '⏳' : ''} Send
                </button>
            </div>
        </div>
    );
};
