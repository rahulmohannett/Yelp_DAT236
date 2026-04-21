import { useState, useEffect, useRef } from 'react';
import { Form, Button, Spinner, Card } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import { chatbotService } from '../services/chatbotService';

function AIChatbot({ user }) {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [isOpen, setIsOpen] = useState(true);
    const messagesEndRef = useRef(null);
    const navigate = useNavigate();

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim() || loading) return;

        const userMessage = { role: 'user', content: input };
        setMessages((prev) => [...prev, userMessage]);
        setInput('');
        setLoading(true);

        try {
            const timeoutPromise = new Promise((_, reject) =>
                setTimeout(() => reject(new Error('Request timed out')), 30000)
            );

            const response = await Promise.race([
                chatbotService.sendMessage(input, messages),
                timeoutPromise,
            ]);

            setMessages((prev) => [
                ...prev,
                {
                    role: 'assistant',
                    content: response.message,
                    recommendations: response.recommendations || [],
                },
            ]);
        } catch (error) {
            console.error('Chatbot error:', error);
            setMessages((prev) => [
                ...prev,
                {
                    role: 'assistant',
                    content:
                        error.message === 'Request timed out'
                            ? 'Request timed out, please try again.'
                            : 'Sorry, I encountered an error. Please try again.',
                },
            ]);
        } finally {
            setLoading(false);
        }
    };

    const handleClearChat = () => {
        setMessages([]);
    };

    const handleQuickAction = (action) => {
        setInput(action);
    };

    // Navigate to restaurant detail page
    const handleRestaurantClick = (restaurantId) => {
        navigate(`/restaurants/${restaurantId}`);
    };

    const renderStars = (rating) => {
        if (!rating) return 'No ratings';
        const full = Math.round(rating);
        return '★'.repeat(full) + '☆'.repeat(5 - full) + ` ${rating.toFixed(1)}`;
    };

    if (!isOpen) {
        return (
            <Button
                variant="danger"
                className="position-fixed bottom-0 end-0 m-4 rounded-circle shadow"
                style={{ width: '60px', height: '60px', fontSize: '24px' }}
                onClick={() => setIsOpen(true)}
                aria-label="Open AI Assistant"
            >
                💬
            </Button>
        );
    }

    return (
        <div className="chatbot-container">
            {/* Header with close + clear buttons */}
            <div className="chatbot-header d-flex justify-content-between align-items-center">
                <span> YelpAI</span>
                <div className="d-flex gap-2 align-items-center">
                    {messages.length > 0 && (
                        <Button
                            variant="outline-light"
                            size="sm"
                            onClick={handleClearChat}
                            title="New Conversation"
                            style={{ fontSize: '12px', padding: '2px 8px' }}
                        >
                            🔄 New Chat
                        </Button>
                    )}
                    <Button variant="link" className="text-white p-0" onClick={() => setIsOpen(false)}>
                        ✕
                    </Button>
                </div>
            </div>

            {/* Messages */}
            <div className="chatbot-messages">
                {messages.length === 0 && (
                    <div className="text-center text-muted mt-3">
                        <p>👋 Hi! I'm your YelpAI.</p>
                        <p>Ask me anything about restaurants!</p>
                    </div>
                )}

                {messages.map((msg, idx) => (
                    <div key={idx}>
                        <div className={`message ${msg.role}`}>
                            <strong>{msg.role === 'user' ? 'You' : 'AI'}:</strong>
                            <p className="mb-0 mt-1">{msg.content}</p>
                        </div>

                        {/* Clickable restaurant recommendation cards */}
                        {msg.recommendations && msg.recommendations.length > 0 && (
                            <div className="mt-2">
                                {msg.recommendations.map((rec, recIdx) => (
                                    <Card
                                        key={recIdx}
                                        className="mb-2 chatbot-rec-card"
                                        onClick={() => handleRestaurantClick(rec.restaurant.id)}
                                        role="button"
                                        tabIndex={0}
                                        onKeyDown={(e) => {
                                            if (e.key === 'Enter') handleRestaurantClick(rec.restaurant.id);
                                        }}
                                    >
                                        <Card.Body className="p-2">
                                            <div className="d-flex justify-content-between align-items-start">
                                                <div>
                                                    <strong>{rec.restaurant.name}</strong>
                                                    <div className="text-muted" style={{ fontSize: '13px' }}>
                                                        {rec.restaurant.cuisine_type} •{' '}
                                                        <span className="price-range">{rec.restaurant.price_range}</span>
                                                    </div>
                                                    <div className="star-rating" style={{ fontSize: '13px' }}>
                                                        {renderStars(rec.restaurant.average_rating)}
                                                    </div>
                                                </div>
                                                <small className="text-muted">
                                                    {rec.restaurant.review_count} reviews
                                                </small>
                                            </div>
                                            <small className="text-muted d-block mt-1">
                                                💡 {rec.reason}
                                            </small>
                                            {rec.restaurant.city && (
                                                <small className="text-muted d-block">
                                                    📍 {rec.restaurant.city}
                                                </small>
                                            )}
                                        </Card.Body>
                                    </Card>
                                ))}
                            </div>
                        )}
                    </div>
                ))}

                {loading && (
                    <div className="message assistant">
                        <Spinner animation="border" size="sm" /> Thinking...
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Input area with quick actions */}
            <div className="chatbot-input">
                <div
                    className="d-flex overflow-auto gap-2 mb-2 pb-1"
                    style={{ whiteSpace: 'nowrap', scrollbarWidth: 'none', msOverflowStyle: 'none' }}
                >
                    <Button variant="outline-secondary" size="sm" className="rounded-pill flex-shrink-0"
                        onClick={() => handleQuickAction('Find nearby Italian')}>
                        🍝 Find Italian
                    </Button>
                    <Button variant="outline-secondary" size="sm" className="rounded-pill flex-shrink-0"
                        onClick={() => handleQuickAction('Surprise me with something popular!')}>
                        🎲 Surprise me!
                    </Button>
                    <Button variant="outline-secondary" size="sm" className="rounded-pill flex-shrink-0"
                        onClick={() => handleQuickAction('Vegan-friendly options')}>
                        🥗 Vegan options
                    </Button>
                    <Button variant="outline-secondary" size="sm" className="rounded-pill flex-shrink-0"
                        onClick={() => handleQuickAction('Best rated near me')}>
                        ⭐ Best rated
                    </Button>
                </div>
                <Form onSubmit={(e) => { e.preventDefault(); handleSend(); }}>
                    <div className="d-flex gap-2">
                        <Form.Control
                            type="text"
                            placeholder="Ask me anything..."
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            disabled={loading}
                            aria-label="Chat message"
                        />
                        <Button type="submit" variant="danger" disabled={loading}>
                            Send
                        </Button>
                    </div>
                </Form>
            </div>
        </div>
    );
}

export default AIChatbot;
