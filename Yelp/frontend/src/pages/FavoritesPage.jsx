import { useState, useEffect } from 'react';
import { Container, Row, Col, Spinner } from 'react-bootstrap';
import { userService } from '../services/userService';
import RestaurantCard from '../components/RestaurantCard';

function FavoritesPage() {
    const [favorites, setFavorites] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadFavorites();
    }, []);

    const loadFavorites = async () => {
        try {
            const data = await userService.getFavorites();
            setFavorites(data);
        } catch (error) {
            console.error('Error loading favorites:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return <Container className="mt-5 text-center"><Spinner animation="border" /></Container>;
    }

    return (
        <Container className="mt-4">
            <h2 className="mb-4">My Favorites</h2>
            {favorites.length === 0 ? (
                <p className="text-muted">You haven't added any favorites yet.</p>
            ) : (
                <Row>
                    {favorites.map((restaurant) => (
                        <Col key={restaurant.id} md={4} sm={6} className="mb-4">
                            <RestaurantCard restaurant={restaurant} />
                        </Col>
                    ))}
                </Row>
            )}
        </Container>
    );
}

export default FavoritesPage;
