import { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { Container, Row, Col, Card, Button, Form, Alert, Spinner } from 'react-bootstrap';
import { restaurantService } from '../services/restaurantService';
import { reviewService } from '../services/reviewService';
import { userService } from '../services/userService';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function RestaurantDetailPage({ user }) {
    const { id } = useParams();
    const [restaurant, setRestaurant] = useState(null);
    const [reviews, setReviews] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isFavorite, setIsFavorite] = useState(false);
    const [showReviewForm, setShowReviewForm] = useState(false);
    const [reviewData, setReviewData] = useState({ rating: 5, review_text: '' });
    const [error, setError] = useState('');
    const [editingReview, setEditingReview] = useState(null);
    const [editReviewData, setEditReviewData] = useState({ rating: 5, review_text: '' });
    const [uploadingPhoto, setUploadingPhoto] = useState(false);
    const [uploadingReviewPhoto, setUploadingReviewPhoto] = useState(null);
    const photoInputRef = useRef(null);
    const reviewPhotoInputRef = useRef(null);

    useEffect(() => {
        loadRestaurant();
        loadReviews();
        if (user) checkFavorite();
    }, [id, user]);

    const loadRestaurant = async () => {
        try {
            const data = await restaurantService.getRestaurant(id);
            setRestaurant(data);
        } catch (error) {
            console.error('Error loading restaurant:', error);
        } finally {
            setLoading(false);
        }
    };

    const loadReviews = async () => {
        try {
            const data = await reviewService.getRestaurantReviews(id);
            setReviews(data);
        } catch (error) {
            console.error('Error loading reviews:', error);
        }
    };

    const checkFavorite = async () => {
        try {
            const favorites = await userService.getFavorites();
            setIsFavorite(favorites.some((fav) => fav.id === parseInt(id)));
        } catch (error) {
            console.error('Error checking favorites:', error);
        }
    };

    const handleToggleFavorite = async () => {
        try {
            if (isFavorite) {
                await userService.removeFavorite(id);
            } else {
                await userService.addFavorite(id);
            }
            setIsFavorite(!isFavorite);
        } catch (error) {
            console.error('Error toggling favorite:', error);
        }
    };

    const handleSubmitReview = async (e) => {
        e.preventDefault();
        setError('');
        try {
            await reviewService.createReview(id, reviewData.rating, reviewData.review_text);
            setShowReviewForm(false);
            setReviewData({ rating: 5, review_text: '' });
            loadReviews();
            loadRestaurant();
        } catch (error) {
            setError(error.response?.data?.detail || 'Failed to submit review');
        }
    };

    const handleEditReview = (review) => {
        setEditingReview(review.id);
        setEditReviewData({ rating: review.rating, review_text: review.review_text || '' });
    };

    const handleUpdateReview = async (reviewId) => {
        try {
            await reviewService.updateReview(reviewId, editReviewData.rating, editReviewData.review_text);
            setEditingReview(null);
            loadReviews();
            loadRestaurant();
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to update review');
        }
    };

    const handleDeleteReview = async (reviewId) => {
        if (!window.confirm('Are you sure you want to delete this review?')) return;
        try {
            await reviewService.deleteReview(reviewId);
            loadReviews();
            loadRestaurant();
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to delete review');
        }
    };

    const handlePhotoUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        setUploadingPhoto(true);
        setError('');
        try {
            await restaurantService.uploadPhoto(id, file);
            loadRestaurant();
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to upload photo');
        } finally {
            setUploadingPhoto(false);
            if (photoInputRef.current) photoInputRef.current.value = '';
        }
    };

    const handleReviewPhotoUpload = async (e, reviewId) => {
        const file = e.target.files[0];
        if (!file) return;
        setUploadingReviewPhoto(reviewId);
        setError('');
        try {
            await reviewService.uploadReviewPhoto(reviewId, file);
            loadReviews();
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to upload review photo');
        } finally {
            setUploadingReviewPhoto(null);
            if (reviewPhotoInputRef.current) reviewPhotoInputRef.current.value = '';
        }
    };

    const renderStars = (rating) => {
        const stars = '★'.repeat(Math.round(rating)) + '☆'.repeat(5 - Math.round(rating));
        return <span className="star-rating">{stars}</span>;
    };

    const getPhotoUrl = (url) => {
        if (!url) return null;
        if (url.startsWith('http')) return url;
        return `${API_URL}${url}`;
    };

    if (loading) {
        return <Container className="mt-5 text-center"><Spinner animation="border" /></Container>;
    }

    if (!restaurant) {
        return <Container className="mt-5"><Alert variant="danger">Restaurant not found</Alert></Container>;
    }

    return (
        <Container className="mt-4">
            <Row>
                <Col md={8}>
                    <h1>{restaurant.name}</h1>
                    <p className="lead">
                        {restaurant.cuisine_type} • <span className="price-range">{restaurant.price_range}</span>
                    </p>
                    {restaurant.average_rating && (
                        <div className="mb-3">
                            {renderStars(restaurant.average_rating)} {restaurant.average_rating.toFixed(1)} ({restaurant.review_count} reviews)
                        </div>
                    )}

                    {/* Photos */}
                    {restaurant.photos && restaurant.photos.length > 0 && (
                        <div className="mb-4">
                            <div className="d-flex gap-2 overflow-auto pb-2">
                                {restaurant.photos.map((url, idx) => (
                                    <img
                                        key={idx}
                                        src={getPhotoUrl(url)}
                                        alt={`${restaurant.name} photo ${idx + 1}`}
                                        style={{ height: '200px', borderRadius: '8px', objectFit: 'cover' }}
                                    />
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Photo upload */}
                    {user && (
                        <div className="mb-3">
                            <input
                                ref={photoInputRef}
                                type="file"
                                accept="image/jpeg,image/png,image/gif,image/webp"
                                style={{ display: 'none' }}
                                onChange={handlePhotoUpload}
                            />
                            <Button
                                variant="outline-secondary"
                                size="sm"
                                onClick={() => photoInputRef.current?.click()}
                                disabled={uploadingPhoto}
                            >
                                {uploadingPhoto ? (
                                    <><Spinner animation="border" size="sm" className="me-1" /> Uploading...</>
                                ) : (
                                    '📷 Add Photo'
                                )}
                            </Button>
                        </div>
                    )}

                    <p>{restaurant.description}</p>

                    <Card className="mb-4">
                        <Card.Body>
                            <h5>Location & Contact</h5>
                            <p className="mb-0">
                                📍 {restaurant.address}<br />
                                {restaurant.city}, {restaurant.state} {restaurant.zip_code}<br />
                                {restaurant.phone && <>📞 {restaurant.phone}<br /></>}
                                {restaurant.website && (
                                    <>🌐 <a href={restaurant.website} target="_blank" rel="noopener noreferrer">{restaurant.website}</a></>
                                )}
                            </p>

                            {/* Hours of Operation */}
                            {restaurant.hours && Object.keys(restaurant.hours).length > 0 && (
                                <div className="mt-3">
                                    <h6 className="mb-2">Hours of Operation</h6>
                                    {Object.entries(restaurant.hours).map(([day, time]) => (
                                        <div key={day} className="d-flex justify-content-between" style={{ maxWidth: '300px', fontSize: '14px' }}>
                                            <span>{day}</span>
                                            <span className="text-muted">{time}</span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </Card.Body>
                    </Card>

                    <small className="text-muted d-block mb-3">Restaurant ID: {restaurant.id}</small>

                    <div className="d-flex gap-2 mb-4">
                        {user && (
                            <>
                                <Button variant={isFavorite ? 'danger' : 'outline-danger'} onClick={handleToggleFavorite}>
                                    {isFavorite ? '❤️ Favorited' : '🤍 Add to Favorites'}
                                </Button>
                                <Button variant="primary" onClick={() => setShowReviewForm(!showReviewForm)}>
                                    ✍️ Write a Review
                                </Button>
                            </>
                        )}
                    </div>

                    {showReviewForm && (
                        <Card className="mb-4">
                            <Card.Body>
                                <h5>Write a Review</h5>
                                {error && <Alert variant="danger">{error}</Alert>}
                                <Form onSubmit={handleSubmitReview}>
                                    <Form.Group className="mb-3">
                                        <Form.Label>Rating</Form.Label>
                                        <Form.Select
                                            value={reviewData.rating}
                                            onChange={(e) => setReviewData({ ...reviewData, rating: parseInt(e.target.value) })}
                                        >
                                            <option value="5">5 - Excellent</option>
                                            <option value="4">4 - Good</option>
                                            <option value="3">3 - Average</option>
                                            <option value="2">2 - Poor</option>
                                            <option value="1">1 - Terrible</option>
                                        </Form.Select>
                                    </Form.Group>
                                    <Form.Group className="mb-3">
                                        <Form.Label>Review</Form.Label>
                                        <Form.Control
                                            as="textarea" rows={4}
                                            value={reviewData.review_text}
                                            onChange={(e) => setReviewData({ ...reviewData, review_text: e.target.value })}
                                            placeholder="Share your experience..."
                                        />
                                    </Form.Group>
                                    <Button type="submit" variant="primary">Submit Review</Button>
                                </Form>
                            </Card.Body>
                        </Card>
                    )}

                    <h3 className="mb-3">Reviews</h3>
                    {error && <Alert variant="danger" dismissible onClose={() => setError('')}>{error}</Alert>}
                    {reviews.length === 0 ? (
                        <p className="text-muted">No reviews yet. Be the first to review!</p>
                    ) : (
                        reviews.map((review) => (
                            <Card key={review.id} className="mb-3">
                                <Card.Body>
                                    {editingReview === review.id ? (
                                        <>
                                            <Form.Group className="mb-2">
                                                <Form.Label>Rating</Form.Label>
                                                <Form.Select
                                                    value={editReviewData.rating}
                                                    onChange={(e) => setEditReviewData({ ...editReviewData, rating: parseInt(e.target.value) })}
                                                >
                                                    <option value="5">5 - Excellent</option>
                                                    <option value="4">4 - Good</option>
                                                    <option value="3">3 - Average</option>
                                                    <option value="2">2 - Poor</option>
                                                    <option value="1">1 - Terrible</option>
                                                </Form.Select>
                                            </Form.Group>
                                            <Form.Group className="mb-2">
                                                <Form.Label>Review</Form.Label>
                                                <Form.Control
                                                    as="textarea" rows={3}
                                                    value={editReviewData.review_text}
                                                    onChange={(e) => setEditReviewData({ ...editReviewData, review_text: e.target.value })}
                                                />
                                            </Form.Group>
                                            <div className="d-flex gap-2">
                                                <Button size="sm" variant="primary" onClick={() => handleUpdateReview(review.id)}>Save</Button>
                                                <Button size="sm" variant="outline-secondary" onClick={() => setEditingReview(null)}>Cancel</Button>
                                            </div>
                                        </>
                                    ) : (
                                        <>
                                            <div className="d-flex justify-content-between">
                                                <div>
                                                    <strong>{review.user_name}</strong>
                                                    <div>{renderStars(review.rating)}</div>
                                                </div>
                                                <div className="d-flex align-items-start gap-2">
                                                    <small className="text-muted">
                                                        {new Date(review.created_at).toLocaleDateString()}
                                                    </small>
                                                    {user && user.id === review.user_id && (
                                                        <>
                                                            <Button size="sm" variant="outline-secondary" onClick={() => handleEditReview(review)}>✏️</Button>
                                                            <Button size="sm" variant="outline-danger" onClick={() => handleDeleteReview(review.id)}>🗑️</Button>
                                                        </>
                                                    )}
                                                </div>
                                            </div>
                                            <p className="mt-2 mb-0">{review.review_text}</p>

                                            {/* Review photos */}
                                            {review.review_photos && review.review_photos.length > 0 && (
                                                <div className="d-flex gap-2 mt-2 overflow-auto">
                                                    {review.review_photos.map((url, idx) => (
                                                        <img
                                                            key={idx}
                                                            src={getPhotoUrl(url)}
                                                            alt={`Review photo ${idx + 1}`}
                                                            style={{ height: '100px', borderRadius: '6px', objectFit: 'cover' }}
                                                        />
                                                    ))}
                                                </div>
                                            )}

                                            {/* Add photo to own review */}
                                            {user && user.id === review.user_id && (
                                                <div className="mt-2">
                                                    <input
                                                        ref={uploadingReviewPhoto === review.id ? reviewPhotoInputRef : null}
                                                        type="file"
                                                        accept="image/jpeg,image/png,image/gif,image/webp"
                                                        style={{ display: 'none' }}
                                                        onChange={(e) => handleReviewPhotoUpload(e, review.id)}
                                                        id={`review-photo-${review.id}`}
                                                    />
                                                    <Button
                                                        variant="outline-secondary"
                                                        size="sm"
                                                        onClick={() => document.getElementById(`review-photo-${review.id}`).click()}
                                                        disabled={uploadingReviewPhoto === review.id}
                                                    >
                                                        {uploadingReviewPhoto === review.id ? (
                                                            <><Spinner animation="border" size="sm" className="me-1" /> Uploading...</>
                                                        ) : (
                                                            '📷 Add Photo'
                                                        )}
                                                    </Button>
                                                </div>
                                            )}
                                        </>
                                    )}
                                </Card.Body>
                            </Card>
                        ))
                    )}
                </Col>
            </Row>
        </Container>
    );
}

export default RestaurantDetailPage;
