import { useState, useEffect, useRef } from 'react';
import { Container, Row, Col, Card, Button, Form, Spinner, ListGroup } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import { chatbotService } from '../services/chatbotService';

function ChatPage() {
    const [conversations, setConversations] = useState([]);
    const [activeConversationId, setActiveConversationId] = useState(null);
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [loadingConversations, setLoadingConversations] = useState(true);
    const messagesEndRef = useRef(null);
    const navigate = useNavigate();

    // Load conversation list on mount
    useEffect(() => {
        loadConversations();
    }, []);

    // Scroll to bottom when messages change
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const loadConversations = async () => {
        try {
            const data = await chatbotService.getConversations();
            setConversations(data);
        } catch (err) {
            console.error('Error loading conversations:', err);
        } finally {
            setLoadingConversations(false);
        }
    };

    const loadConversation = async (conversationId) => {
        setActiveConversationId(conversationId);
        setLoading(true);
        try {
            const data = await chatbotService.getConversation(conversationId);
            // Convert DB messages to display format
            const displayMessages = data.messages.map((msg) => ({
                role: msg.role,
                content: msg.content,
                recommendations: msg.recommendations || [],
            }));
            setMessages(displayMessages);
        } catch (err) {
            console.error('Error loading conversation:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleNewChat = () => {
        setActiveConversationId(null);
        setMessages([]);
        setInput('');
    };

    const handleDeleteConversation = async (e, conversationId) => {
        e.stopPropagation();
        if (!window.confirm('Delete this conversation?')) return;
        try {
            await chatbotService.deleteConversation(conversationId);
            setConversations((prev) => prev.filter((c) => c.id !== conversationId));
            if (activeConversationId === conversationId) {
                handleNewChat();
            }
        } catch (err) {
            console.error('Error deleting conversation:', err);
        }
    };

    const handleSend = async () => {
        if (!input.trim() || loading) return;

        const userMessage = { role: 'user', content: input, recommendations: [] };
        setMessages((prev) => [...prev, userMessage]);
        const currentInput = input;
        setInput('');
        setLoading(true);

        try {
            const response = await chatbotService.sendMessage(
                currentInput,
                [],  // history is now managed server-side
                activeConversationId
            );

            // Update active conversation ID (important for new conversations)
            setActiveConversationId(response.conversation_id);

            setMessages((prev) => [
                ...prev,
                {
                    role: 'assistant',
                    content: response.message,
                    recommendations: response.recommendations || [],
                },
            ]);

            // Refresh sidebar
            loadConversations();
        } catch (error) {
            console.error('Chatbot error:', error);
            setMessages((prev) => [
                ...prev,
                {
                    role: 'assistant',
                    content: 'Sorry, I encountered an error. Please try again.',
                    recommendations: [],
                },
            ]);
        } finally {
            setLoading(false);
        }
    };

    const handleQuickAction = (action) => {
        setInput(action);
    };

    const handleRestaurantClick = (restaurantId) => {
        navigate(`/restaurants/${restaurantId}`);
    };

    const renderStars = (rating) => {
        if (!rating) return 'No ratings';
        const full = Math.round(rating);
        return '★'.repeat(full) + '☆'.repeat(5 - full) + ` ${rating.toFixed(1)}`;
    };

    const formatDate = (dateStr) => {
        const date = new Date(dateStr);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        if (diffMins < 60) return `${diffMins}m ago`;
        const diffHours = Math.floor(diffMins / 60);
        if (diffHours < 24) return `${diffHours}h ago`;
        return date.toLocaleDateString();
    };

    return (
        <Container fluid className="mt-0" style={{ height: 'calc(100vh - 56px)' }}>
            <Row className="h-100">
                {/* Sidebar */}
                <Col md={3} className="border-end bg-light p-0 d-flex flex-column" style={{ height: '100%' }}>
                    <div className="p-3 border-bottom">
                        <Button variant="danger" className="w-100" onClick={handleNewChat}>
                            + New Chat
                        </Button>
                    </div>
                    <div className="flex-grow-1 overflow-auto">
                        {loadingConversations ? (
                            <div className="text-center p-3"><Spinner animation="border" size="sm" /></div>
                        ) : conversations.length === 0 ? (
                            <p className="text-muted text-center p-3" style={{ fontSize: '14px' }}>
                                No conversations yet
                            </p>
                        ) : (
                            <ListGroup variant="flush">
                                {conversations.map((conv) => (
                                    <ListGroup.Item
                                        key={conv.id}
                                        action
                                        active={activeConversationId === conv.id}
                                        onClick={() => loadConversation(conv.id)}
                                        className="d-flex justify-content-between align-items-start py-2 px-3"
                                        style={{ fontSize: '14px' }}
                                    >
                                        <div className="text-truncate me-2" style={{ maxWidth: '180px' }}>
                                            <div className="text-truncate fw-medium">{conv.title}</div>
                                            <small className="text-muted">{formatDate(conv.updated_at)}</small>
                                        </div>
                                        <Button
                                            variant="link"
                                            size="sm"
                                            className="text-danger p-0"
                                            onClick={(e) => handleDeleteConversation(e, conv.id)}
                                            title="Delete"
                                        >
                                            🗑️
                                        </Button>
                                    </ListGroup.Item>
                                ))}
                            </ListGroup>
                        )}
                    </div>
                </Col>

                {/* Main chat area */}
                <Col md={9} className="d-flex flex-column p-0" style={{ height: '100%' }}>
                    {/* Header */}
                    <div className="p-3 border-bottom bg-white">
                        <h5 className="mb-0"> YelpAI</h5>
                        <small className="text-muted">Ask for personalized restaurant recommendations</small>
                    </div>

                    {/* Messages */}
                    <div className="flex-grow-1 overflow-auto p-3" style={{ backgroundColor: '#f8f9fa' }}>
                        {messages.length === 0 && !loading && (
                            <div className="text-center mt-5">
                                <h4 className="text-muted mb-3">👋 How can I help you today?</h4>
                                <p className="text-muted mb-4">
                                    I use your saved preferences and our restaurant database to find the perfect spot.
                                </p>
                                <div className="d-flex flex-wrap justify-content-center gap-2">
                                    <Button variant="outline-secondary" className="rounded-pill"
                                        onClick={() => handleQuickAction('Find dinner tonight near me')}>
                                        🍽️ Find dinner tonight
                                    </Button>
                                    <Button variant="outline-secondary" className="rounded-pill"
                                        onClick={() => handleQuickAction('Best rated Italian restaurant')}>
                                        ⭐ Best rated Italian
                                    </Button>
                                    <Button variant="outline-secondary" className="rounded-pill"
                                        onClick={() => handleQuickAction('Something romantic for an anniversary')}>
                                        💕 Romantic for anniversary
                                    </Button>
                                    <Button variant="outline-secondary" className="rounded-pill"
                                        onClick={() => handleQuickAction('Show me casual vegan options')}>
                                        🥗 Vegan options
                                    </Button>
                                    <Button variant="outline-secondary" className="rounded-pill"
                                        onClick={() => handleQuickAction('Surprise me with something popular!')}>
                                        🎲 Surprise me!
                                    </Button>
                                </div>
                            </div>
                        )}

                        {messages.map((msg, idx) => (
                            <div key={idx} className="mb-3">
                                <div
                                    className={`d-flex ${msg.role === 'user' ? 'justify-content-end' : 'justify-content-start'}`}
                                >
                                    <div
                                        style={{
                                            maxWidth: '75%',
                                            padding: '10px 16px',
                                            borderRadius: msg.role === 'user' ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
                                            backgroundColor: msg.role === 'user' ? '#dc3545' : '#ffffff',
                                            color: msg.role === 'user' ? '#ffffff' : '#212529',
                                            boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
                                        }}
                                    >
                                        <p className="mb-0" style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</p>
                                    </div>
                                </div>

                                {/* Restaurant recommendation cards */}
                                {msg.recommendations && msg.recommendations.length > 0 && (
                                    <div className="d-flex flex-wrap gap-2 mt-2" style={{ paddingLeft: '8px' }}>
                                        {msg.recommendations.map((rec, recIdx) => (
                                            <Card
                                                key={recIdx}
                                                className="shadow-sm"
                                                style={{ width: '260px', cursor: 'pointer' }}
                                                onClick={() => handleRestaurantClick(rec.restaurant.id)}
                                                role="button"
                                                tabIndex={0}
                                                onKeyDown={(e) => { if (e.key === 'Enter') handleRestaurantClick(rec.restaurant.id); }}
                                            >
                                                <Card.Body className="p-2">
                                                    <div className="d-flex justify-content-between align-items-start">
                                                        <div>
                                                            <strong style={{ fontSize: '14px' }}>{rec.restaurant.name}</strong>
                                                            <div className="text-muted" style={{ fontSize: '12px' }}>
                                                                {rec.restaurant.cuisine_type} • {rec.restaurant.price_range}
                                                            </div>
                                                            <div className="star-rating" style={{ fontSize: '12px', color: '#ffc107' }}>
                                                                {renderStars(rec.restaurant.average_rating)}
                                                            </div>
                                                        </div>
                                                        <small className="text-muted" style={{ fontSize: '11px' }}>
                                                            {rec.restaurant.review_count} reviews
                                                        </small>
                                                    </div>
                                                    <small className="text-muted d-block mt-1" style={{ fontSize: '12px' }}>
                                                        💡 {rec.reason}
                                                    </small>
                                                    {rec.restaurant.city && (
                                                        <small className="text-muted d-block" style={{ fontSize: '12px' }}>
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
                            <div className="d-flex justify-content-start mb-3">
                                <div style={{
                                    padding: '10px 16px',
                                    borderRadius: '18px 18px 18px 4px',
                                    backgroundColor: '#ffffff',
                                    boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
                                }}>
                                    <Spinner animation="border" size="sm" className="me-2" />
                                    Thinking...
                                </div>
                            </div>
                        )}

                        <div ref={messagesEndRef} />
                    </div>

                    {/* Quick actions row (shown when conversation has messages) */}
                    {messages.length > 0 && (
                        <div className="px-3 pt-2 bg-white border-top d-flex gap-2 overflow-auto"
                            style={{ whiteSpace: 'nowrap', scrollbarWidth: 'none' }}>
                            <Button variant="outline-secondary" size="sm" className="rounded-pill flex-shrink-0"
                                onClick={() => handleQuickAction('Find nearby Italian')}>🍝 Italian</Button>
                            <Button variant="outline-secondary" size="sm" className="rounded-pill flex-shrink-0"
                                onClick={() => handleQuickAction('Surprise me!')}>🎲 Surprise me</Button>
                            <Button variant="outline-secondary" size="sm" className="rounded-pill flex-shrink-0"
                                onClick={() => handleQuickAction('Vegan-friendly options')}>🥗 Vegan</Button>
                            <Button variant="outline-secondary" size="sm" className="rounded-pill flex-shrink-0"
                                onClick={() => handleQuickAction('Best rated near me')}>⭐ Best rated</Button>
                        </div>
                    )}

                    {/* Input */}
                    <div className="p-3 bg-white border-top">
                        <Form onSubmit={(e) => { e.preventDefault(); handleSend(); }}>
                            <div className="d-flex gap-2">
                                <Form.Control
                                    type="text"
                                    placeholder="Ask about cuisine, budget, dietary needs, mood, or hours..."
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    disabled={loading}
                                    aria-label="Chat message"
                                    className="rounded-pill"
                                />
                                <Button type="submit" variant="danger" disabled={loading} className="rounded-pill px-4">
                                    Send
                                </Button>
                            </div>
                        </Form>
                    </div>
                </Col>
            </Row>
        </Container>
    );
}

export default ChatPage;
