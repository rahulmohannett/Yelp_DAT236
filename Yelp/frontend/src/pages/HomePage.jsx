import React from 'react';
import { Container, Row, Col, Card, Button } from 'react-bootstrap';
import { Link } from 'react-router-dom';

function HomePage({ user }) {
    return (
        <div
            style={{
                // Dark gradient overlay mixed with a new upscale restaurant interior image
                backgroundImage: `linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.7)), url('https://images.unsplash.com/photo-1555396273-367ea4eb4db5?q=80&w=2074&auto=format&fit=crop')`,
                backgroundSize: 'cover',
                backgroundPosition: 'center',
                backgroundAttachment: 'fixed',
                minHeight: '100vh',
                width: '100%',
                paddingTop: '80px',
                paddingBottom: '80px',
                color: 'white'
            }}
        >
            <Container>
                <Row>
                    <Col md={8} className="mx-auto text-center">
                        <h1 className="display-4 fw-bold mb-4">Discover Your Next Favorite Restaurant</h1>
                        <p className="lead mb-5" style={{ color: '#f8f9fa' }}>
                            Search restaurants, read reviews, and get personalized AI recommendations.
                        </p>

                        {user ? (
                            <Card className="shadow-lg text-dark border-0 mb-4" style={{ backgroundColor: 'rgba(255, 255, 255, 0.95)' }}>
                                <Card.Body className="p-5">
                                    <h3 className="mb-3 fw-bold">YelpAI Assistant</h3>
                                    <p className="text-muted mb-4">
                                        Get personalized restaurant recommendations based on your preferences,
                                        dietary needs, budget, and mood. Our AI assistant remembers your conversation
                                        so you can refine your search.
                                    </p>
                                    <Button as={Link} to="/chat" variant="danger" size="lg" className="px-5">
                                        Ask AI
                                    </Button>
                                </Card.Body>
                            </Card>
                        ) : (
                            <Card className="shadow-lg text-dark border-0 mb-4" style={{ backgroundColor: 'rgba(255, 255, 255, 0.95)' }}>
                                <Card.Body className="p-5">
                                    <h3 className="mb-3 fw-bold">Get Started</h3>
                                    <p className="text-muted mb-4">
                                        Sign up or log in to access our AI-powered restaurant assistant,
                                        save favorites, write reviews, and more.
                                    </p>
                                    <div className="d-flex gap-3 justify-content-center">
                                        <Button as={Link} to="/login" variant="outline-danger" size="lg">Log In</Button>
                                        <Button as={Link} to="/signup" variant="danger" size="lg">Sign Up</Button>
                                    </div>
                                </Card.Body>
                            </Card>
                        )}

                        <Row className="mt-5">
                            <Col md={4} className="mb-3">
                                <Card className="border-0 shadow-lg h-100 text-dark" style={{ backgroundColor: 'rgba(255, 255, 255, 0.95)' }}>
                                    <Card.Body className="text-center p-4">
                                        <div style={{ fontSize: '2rem' }}>🔍</div>
                                        <h6 className="mt-2 fw-bold">Search Restaurants</h6>
                                        <p className="text-muted" style={{ fontSize: '14px' }}>
                                            Filter by cuisine, price, location, and keywords.
                                        </p>
                                        <Button as={Link} to="/search" variant="outline-danger" size="sm">
                                            Browse
                                        </Button>
                                    </Card.Body>
                                </Card>
                            </Col>
                            <Col md={4} className="mb-3">
                                <Card className="border-0 shadow-lg h-100 text-dark" style={{ backgroundColor: 'rgba(255, 255, 255, 0.95)' }}>
                                    <Card.Body className="text-center p-4">
                                        <div style={{ fontSize: '2rem' }}>⭐</div>
                                        <h6 className="mt-2 fw-bold">Read Reviews</h6>
                                        <p className="text-muted" style={{ fontSize: '14px' }}>
                                            See what others think and share your experience.
                                        </p>
                                        <Button as={Link} to="/search" variant="outline-danger" size="sm">
                                            Explore
                                        </Button>
                                    </Card.Body>
                                </Card>
                            </Col>
                            <Col md={4} className="mb-3">
                                <Card className="border-0 shadow-lg h-100 text-dark" style={{ backgroundColor: 'rgba(255, 255, 255, 0.95)' }}>
                                    <Card.Body className="text-center p-4">
                                        <div style={{ fontSize: '2rem' }}>➕</div>
                                        <h6 className="mt-2 fw-bold">Add a Restaurant</h6>
                                        <p className="text-muted" style={{ fontSize: '14px' }}>
                                            Know a great spot? Add it to our directory.
                                        </p>
                                        {user ? (
                                            <Button as={Link} to="/add-restaurant" variant="outline-danger" size="sm">
                                                Add
                                            </Button>
                                        ) : (
                                            <Button as={Link} to="/login" variant="outline-secondary" size="sm">
                                                Log in first
                                            </Button>
                                        )}
                                    </Card.Body>
                                </Card>
                            </Col>
                        </Row>
                    </Col>
                </Row>
            </Container>
        </div>
    );
}

export default HomePage;