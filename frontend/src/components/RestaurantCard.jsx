import { Card } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';

function RestaurantCard({ restaurant }) {
    const navigate = useNavigate();

    const renderStars = (rating) => {
        if (!rating) return 'No ratings yet';
        const stars = '★'.repeat(Math.round(rating)) + '☆'.repeat(5 - Math.round(rating));
        return <span className="star-rating">{stars} {rating.toFixed(1)}</span>;
    };

    return (
        <Card className="restaurant-card h-100" onClick={() => navigate(`/restaurants/${restaurant.id}`)}>
            <Card.Body>
                <Card.Title>{restaurant.name}</Card.Title>
                <Card.Subtitle className="mb-2 text-muted">
                    {restaurant.cuisine_type} • <span className="price-range">{restaurant.price_range}</span>
                </Card.Subtitle>
                <Card.Text>
                    {restaurant.description?.substring(0, 100)}
                    {restaurant.description?.length > 100 && '...'}
                </Card.Text>
                <div className="d-flex justify-content-between align-items-center">
                    <div>{renderStars(restaurant.average_rating)}</div>
                    <small className="text-muted">{restaurant.review_count} reviews</small>
                </div>
                {restaurant.city && (
                    <small className="text-muted d-block mt-2">
                        📍 {restaurant.city}, {restaurant.state}
                    </small>
                )}
            </Card.Body>
        </Card>
    );
}

export default RestaurantCard;
