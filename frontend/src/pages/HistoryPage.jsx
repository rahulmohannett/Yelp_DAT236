import { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Tabs, Tab, Spinner } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import RestaurantCard from '../components/RestaurantCard';

function HistoryPage() {
    const [reviews, setReviews] = useState([]);
    const [restaurants, setRestaurants] = useState([]);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        loadHistory();
    }, []);

    const loadHistory = async () => {
        try {
            const [reviewsData, restaurantsData] = await Promise.all([
                api.get('/history/reviews'),
                api.get('/history/restaurants'),
            ]);
            setReviews(reviewsData.data);
            setRestaurants(restaurantsData.data);
        } catch (error) {
            console.error('Error loading history:', error);
        } finally {
            setLoading(false);
        }
    };

    const renderStars = (rating) => {
        const stars = '★'.repeat(Math.round(rating)) + '☆'.repeat(5 - Math.round(rating));
        return <span className="star-rating">{stars}</span>;
    };

    if (loading) {
        return <Container className="mt-5 text-center"><Spinner animation="border" /></Container>;
    }

    return (
        <Container className="mt-4">
            <h2 className="mb-4">My History</h2>
            <Tabs defaultActiveKey="reviews" className="mb-3">
                <Tab eventKey="reviews" title={`Reviews (${reviews.length})`}>
                    {reviews.length === 0 ? (
                        <p className="text-muted">You haven't written any reviews yet.</p>
                    ) : (
                        reviews.map((review) => (
                            <Card
                                key={review.id}
                                className="mb-3"
                                style={{ cursor: 'pointer' }}
                                onClick={() => navigate(`/restaurants/${review.restaurant_id}`)}
                            >
                                <Card.Body>
                                    <div className="d-flex justify-content-between">
                                        <div>
                                            <h6 className="mb-1">{review.restaurant_name || `Restaurant #${review.restaurant_id}`}</h6>
                                            <div>{renderStars(review.rating)}</div>
                                        </div>
                                        <small className="text-muted">
                                            {new Date(review.created_at).toLocaleDateString()}
                                        </small>
                                    </div>
                                    <p className="mt-2 mb-0">{review.review_text}</p>
                                </Card.Body>
                            </Card>
                        ))
                    )}
                </Tab>
                <Tab eventKey="restaurants" title={`Restaurants Added (${restaurants.length})`}>
                    {restaurants.length === 0 ? (
                        <p className="text-muted">You haven't added any restaurants yet.</p>
                    ) : (
                        <Row>
                            {restaurants.map((restaurant) => (
                                <Col key={restaurant.id} md={4} sm={6} className="mb-4">
                                    <RestaurantCard restaurant={restaurant} />
                                </Col>
                            ))}
                        </Row>
                    )}
                </Tab>
            </Tabs>
        </Container>
    );
}

export default HistoryPage;
