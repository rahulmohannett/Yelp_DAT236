import { useEffect } from 'react';
import { Container, Row, Col, Spinner } from 'react-bootstrap';
import { useDispatch, useSelector } from 'react-redux';
import { fetchFavoritesThunk } from '../store/favoritesSlice';
import RestaurantCard from '../components/RestaurantCard';

function FavoritesPage() {
    const dispatch = useDispatch();
    const { favorites, loading, error } = useSelector(state => state.favorites);

    useEffect(() => {
        dispatch(fetchFavoritesThunk());
    }, [dispatch]);

    if (loading) {
        return <Container className="mt-5 text-center"><Spinner animation="border" /></Container>;
    }

    return (
        <Container className="mt-4">
            <h2 className="mb-4">My Favorites</h2>
            {error && <p className="text-danger">{error}</p>}
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
