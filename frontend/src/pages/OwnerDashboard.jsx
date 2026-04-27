import { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Button, Modal, Form, Alert, Spinner, Tabs, Tab } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

const DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

function OwnerDashboard() {
    const navigate = useNavigate();
    const [restaurants, setRestaurants] = useState([]);
    const [dashboard, setDashboard] = useState(null);
    const [loading, setLoading] = useState(true);
    // Claim modal
    const [showClaimModal, setShowClaimModal] = useState(false);
    const [claimSearch, setClaimSearch] = useState('');
    const [claimResults, setClaimResults] = useState([]);
    const [claimSearching, setClaimSearching] = useState(false);
    const [claimError, setClaimError] = useState('');
    const [claimSuccess, setClaimSuccess] = useState('');
    // Analytics
    const [analytics, setAnalytics] = useState(null);
    const [selectedRestaurant, setSelectedRestaurant] = useState(null);
    // Edit modal
    const [showEditModal, setShowEditModal] = useState(false);
    const [editData, setEditData] = useState({});
    const [editHours, setEditHours] = useState({});
    const [editAmenities, setEditAmenities] = useState('');
    const [editError, setEditError] = useState('');
    const [editSuccess, setEditSuccess] = useState('');

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [restRes, dashRes] = await Promise.all([
                api.get('/owner/restaurants'),
                api.get('/owner/dashboard'),
            ]);
            setRestaurants(restRes.data);
            setDashboard(dashRes.data);
        } catch (error) {
            console.error('Error loading data:', error);
        } finally {
            setLoading(false);
        }
    };

    // Claim handlers
    const handleClaimSearch = async () => {
        if (!claimSearch.trim()) return;
        setClaimSearching(true);
        setClaimError('');
        setClaimResults([]);
        try {
            const res = await api.get(`/owner/claim/search?q=${encodeURIComponent(claimSearch)}`);
            setClaimResults(res.data);
            if (res.data.length === 0) setClaimError('No unclaimed restaurants found matching your search.');
        } catch (err) {
            setClaimError(err.response?.data?.detail || err.response?.data?.message || err.message || 'Search failed.');
        } finally {
            setClaimSearching(false);
        }
    };

    const handleClaimRestaurant = async (restaurantId) => {
        setClaimError('');
        setClaimSuccess('');
        try {
            await api.post('/owner/claims', { restaurant_id: restaurantId });
            setClaimSuccess('Restaurant claimed successfully!');
            setClaimResults([]);
            setClaimSearch('');
            loadData();
        } catch (error) {
            setClaimError(error.response?.data?.detail || error.response?.data?.message || error.message || 'Failed to claim restaurant');
        }
    };

    // Analytics
    const handleViewAnalytics = async (restaurantId) => {
        if (selectedRestaurant === restaurantId) {
            setSelectedRestaurant(null);
            setAnalytics(null);
            return;
        }
        try {
            const response = await api.get(`/owner/restaurants/${restaurantId}/analytics`);
            setAnalytics(response.data);
            setSelectedRestaurant(restaurantId);
        } catch (error) {
            console.error('Error loading analytics:', error);
        }
    };

    // Edit handlers
    const handleOpenEdit = (restaurant) => {
        setEditData({
            id: restaurant.id,
            name: restaurant.name || '',
            description: restaurant.description || '',
            cuisine_type: restaurant.cuisine_type || '',
            price_range: restaurant.price_range || '',
            address: restaurant.address || '',
            city: restaurant.city || '',
            state: restaurant.state || '',
            zip_code: restaurant.zip_code || '',
            phone: restaurant.phone || '',
            website: restaurant.website || '',
        });
        setEditHours(restaurant.hours || {});
        setEditAmenities(Array.isArray(restaurant.amenities) ? restaurant.amenities.join(', ') : '');
        setEditError('');
        setEditSuccess('');
        setShowEditModal(true);
    };

    const handleHoursChange = (day, value) => {
        setEditHours((prev) => {
            const updated = { ...prev };
            if (value.trim()) { updated[day] = value; } else { delete updated[day]; }
            return updated;
        });
    };

    const handleApplyToAll = (value) => {
        if (!value.trim()) return;
        const allHours = {};
        DAYS_OF_WEEK.forEach((day) => { allHours[day] = value; });
        setEditHours(allHours);
    };

    const handleEditSubmit = async () => {
        setEditError('');
        setEditSuccess('');
        try {
            const { id, ...data } = editData;
            const amenities = editAmenities.split(',').map((a) => a.trim().toLowerCase()).filter((a) => a);
            const payload = {
                ...data,
                hours: Object.keys(editHours).length > 0 ? editHours : null,
                amenities: amenities.length > 0 ? amenities : null,
            };
            await api.put(`/restaurants/${id}`, payload);
            setEditSuccess('Restaurant updated!');
            loadData();
            setTimeout(() => setShowEditModal(false), 1000);
        } catch (error) {
            setEditError(error.response?.data?.detail || error.response?.data?.message || error.message || 'Failed to update restaurant');
        }
    };

    const renderStars = (rating) => {
        if (!rating) return 'N/A';
        const stars = '★'.repeat(Math.round(rating)) + '☆'.repeat(5 - Math.round(rating));
        return <span className="star-rating">{stars} {rating.toFixed(1)}</span>;
    };

    if (loading) {
        return <Container className="mt-5 text-center"><Spinner animation="border" /></Container>;
    }

    return (
        <Container className="mt-4">
            {/* Header */}
            <div className="d-flex justify-content-between align-items-center mb-4">
                <div>
                    <h2 className="mb-0">Owner Dashboard</h2>
                    <small className="text-muted">Manage your restaurants and track performance</small>
                </div>
                <div className="d-flex gap-2">
                    <Button variant="outline-primary" onClick={() => navigate('/chat')}> YelpAI </Button>
                    <Button variant="danger" onClick={() => navigate('/add-restaurant')}>+ Add Restaurant</Button>
                    <Button variant="outline-primary" onClick={() => { setShowClaimModal(true); setClaimError(''); setClaimSuccess(''); setClaimResults([]); setClaimSearch(''); }}>
                        🏷️ Claim Restaurant
                    </Button>
                </div>
            </div>

            {/* Overview Stats */}
            {dashboard && (
                <Row className="mb-4 g-3">
                    <Col md={3}>
                        <Card className="text-center border-0 shadow-sm">
                            <Card.Body>
                                <h3 className="mb-0 text-danger">{dashboard.total_restaurants}</h3>
                                <small className="text-muted">Restaurants</small>
                            </Card.Body>
                        </Card>
                    </Col>
                    <Col md={3}>
                        <Card className="text-center border-0 shadow-sm">
                            <Card.Body>
                                <h3 className="mb-0 text-danger">{dashboard.total_views}</h3>
                                <small className="text-muted">Total Views</small>
                            </Card.Body>
                        </Card>
                    </Col>
                    <Col md={3}>
                        <Card className="text-center border-0 shadow-sm">
                            <Card.Body>
                                <h3 className="mb-0 text-danger">{dashboard.total_reviews}</h3>
                                <small className="text-muted">Total Reviews</small>
                            </Card.Body>
                        </Card>
                    </Col>
                    <Col md={3}>
                        <Card className="text-center border-0 shadow-sm">
                            <Card.Body>
                                <h3 className="mb-0 text-danger">{dashboard.average_rating || 'N/A'}</h3>
                                <small className="text-muted">Avg Rating</small>
                            </Card.Body>
                        </Card>
                    </Col>
                </Row>
            )}

            {/* Sentiment + Recent Reviews row */}
            {dashboard && dashboard.total_reviews > 0 && (
                <Row className="mb-4 g-3">
                    <Col md={4}>
                        <Card className="border-0 shadow-sm h-100">
                            <Card.Body>
                                <h6>📊 Public Sentiment</h6>
                                <p className="mb-1">Overall: <strong className={
                                    dashboard.sentiment.overall === 'Positive' ? 'text-success' :
                                    dashboard.sentiment.overall === 'Negative' ? 'text-danger' : 'text-warning'
                                }>{dashboard.sentiment.overall}</strong></p>
                                <div style={{ fontSize: '14px' }}>
                                    <div className="d-flex justify-content-between"><span>Positive</span><span>{dashboard.sentiment.positive}</span></div>
                                    <div className="d-flex justify-content-between"><span>Neutral</span><span>{dashboard.sentiment.neutral}</span></div>
                                    <div className="d-flex justify-content-between"><span>Negative</span><span>{dashboard.sentiment.negative}</span></div>
                                </div>
                            </Card.Body>
                        </Card>
                    </Col>
                    <Col md={8}>
                        <Card className="border-0 shadow-sm h-100">
                            <Card.Body>
                                <h6>🕐 Recent Reviews</h6>
                                {dashboard.recent_reviews?.map((r) => (
                                    <div key={r.id} className="d-flex justify-content-between align-items-start border-bottom py-2" style={{ fontSize: '13px' }}>
                                        <div>
                                            <strong>{r.user_name}</strong>
                                            <span className="text-muted ms-2">{r.review_text?.substring(0, 60)}...</span>
                                        </div>
                                        <div className="text-end text-nowrap ms-2">
                                            <span className="star-rating">{'★'.repeat(r.rating)}</span>
                                            <small className="d-block text-muted">{r.restaurant_name}</small>
                                        </div>
                                    </div>
                                ))}
                            </Card.Body>
                        </Card>
                    </Col>
                </Row>
            )}

            {/* Restaurants tab */}
            <Tabs defaultActiveKey="restaurants" className="mb-3">
                <Tab eventKey="restaurants" title={`My Restaurants (${restaurants.length})`}>
                    {restaurants.length === 0 ? (
                        <Card>
                            <Card.Body className="text-center py-5">
                                <h5>No restaurants yet</h5>
                                <p className="text-muted">Start by adding your first restaurant or claiming an existing one</p>
                            </Card.Body>
                        </Card>
                    ) : (
                        restaurants.map((restaurant) => (
                            <Card key={restaurant.id} className="mb-3 shadow-sm">
                                <Card.Body>
                                    <Row>
                                        <Col md={8}>
                                            <h5 className="mb-1">{restaurant.name}</h5>
                                            <p className="text-muted mb-1" style={{ fontSize: '14px' }}>
                                                {restaurant.cuisine_type} • {restaurant.price_range}
                                                {restaurant.city && <> • 📍 {restaurant.city}, {restaurant.state}</>}
                                            </p>
                                            <p className="mb-0" style={{ fontSize: '14px' }}>{restaurant.description?.substring(0, 120)}</p>
                                        </Col>
                                        <Col md={4} className="text-end">
                                            <div className="mb-2">{renderStars(restaurant.average_rating)}</div>
                                            <small className="text-muted d-block">{restaurant.review_count} reviews</small>
                                            <div className="d-flex gap-2 justify-content-end mt-2">
                                                <Button variant="outline-primary" size="sm" onClick={() => navigate(`/restaurants/${restaurant.id}`)}>View</Button>
                                                <Button variant="outline-secondary" size="sm" onClick={() => handleOpenEdit(restaurant)}>Edit</Button>
                                                <Button
                                                    variant={selectedRestaurant === restaurant.id ? 'primary' : 'outline-primary'}
                                                    size="sm"
                                                    onClick={() => handleViewAnalytics(restaurant.id)}
                                                >
                                                    Analytics
                                                </Button>
                                            </div>
                                        </Col>
                                    </Row>

                                    {/* Inline Analytics */}
                                    {selectedRestaurant === restaurant.id && analytics && (
                                        <div className="mt-3 pt-3 border-top">
                                            <Row>
                                                <Col md={3}>
                                                    <p className="mb-1"><strong>Total Reviews:</strong> {analytics.total_reviews}</p>
                                                    <p className="mb-1"><strong>Avg Rating:</strong> {analytics.average_rating?.toFixed(1) || 'N/A'}</p>
                                                    <p className="mb-1"><strong>Views:</strong> {analytics.view_count}</p>
                                                </Col>
                                                <Col md={3}>
                                                    <p className="mb-1"><strong>Rating Distribution:</strong></p>
                                                    {[5, 4, 3, 2, 1].map((star) => (
                                                        <div key={star} className="d-flex align-items-center gap-1" style={{ fontSize: '13px' }}>
                                                            <span>{star}★</span>
                                                            <div style={{
                                                                width: `${(analytics.rating_distribution[String(star)] || 0) / Math.max(analytics.total_reviews, 1) * 100}%`,
                                                                minWidth: '4px', height: '12px', background: '#ffc107', borderRadius: '2px',
                                                            }} />
                                                            <span className="text-muted">{analytics.rating_distribution[String(star)] || 0}</span>
                                                        </div>
                                                    ))}
                                                </Col>
                                                <Col md={3}>
                                                    <p className="mb-1"><strong>Sentiment:</strong></p>
                                                    <div style={{ fontSize: '13px' }}>
                                                        <div>Positive: {analytics.sentiment?.positive || 0}</div>
                                                        <div>Neutral: {analytics.sentiment?.neutral || 0}</div>
                                                        <div>Negative: {analytics.sentiment?.negative || 0}</div>
                                                    </div>
                                                </Col>
                                                <Col md={3}>
                                                    <p className="mb-1"><strong>Recent Reviews:</strong></p>
                                                    {analytics.recent_reviews?.map((r) => (
                                                        <div key={r.id} className="mb-1" style={{ fontSize: '13px' }}>
                                                            <span className="star-rating">{'★'.repeat(r.rating)}</span>{' '}
                                                            {r.review_text?.substring(0, 40)}...
                                                        </div>
                                                    ))}
                                                </Col>
                                            </Row>
                                        </div>
                                    )}
                                </Card.Body>
                            </Card>
                        ))
                    )}
                </Tab>
            </Tabs>

            {/* Claim Restaurant Modal — with search */}
            <Modal show={showClaimModal} onHide={() => setShowClaimModal(false)} size="lg">
                <Modal.Header closeButton>
                    <Modal.Title>Claim Your Restaurant</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <p className="text-muted">Search for your restaurant and link it to your owner account.</p>
                    {claimError && <Alert variant="danger">{claimError}</Alert>}
                    {claimSuccess && <Alert variant="success">{claimSuccess}</Alert>}
                    <div className="d-flex gap-2 mb-3">
                        <Form.Control
                            type="text"
                            placeholder="Restaurant name or ZIP code..."
                            value={claimSearch}
                            onChange={(e) => setClaimSearch(e.target.value)}
                            onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); handleClaimSearch(); } }}
                        />
                        <Button variant="danger" onClick={handleClaimSearch} disabled={claimSearching}>
                            {claimSearching ? <Spinner animation="border" size="sm" /> : 'Search'}
                        </Button>
                    </div>
                    {claimResults.map((r) => (
                        <Card key={r.id} className="mb-2">
                            <Card.Body className="d-flex justify-content-between align-items-center py-2">
                                <div>
                                    <strong>{r.name}</strong>
                                    <div className="text-muted" style={{ fontSize: '13px' }}>
                                        {r.cuisine_type} • {r.price_range} • {r.city}, {r.state}
                                    </div>
                                    <small className="text-muted">
                                        {r.average_rating ? `${r.average_rating.toFixed(1)}★` : 'No ratings'} • {r.review_count} reviews
                                    </small>
                                </div>
                                <Button variant="danger" size="sm" onClick={() => handleClaimRestaurant(r.id)}>
                                    Claim This
                                </Button>
                            </Card.Body>
                        </Card>
                    ))}
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="secondary" onClick={() => setShowClaimModal(false)}>Close</Button>
                </Modal.Footer>
            </Modal>

            {/* Edit Restaurant Modal */}
            <Modal show={showEditModal} onHide={() => setShowEditModal(false)} size="lg">
                <Modal.Header closeButton>
                    <Modal.Title>Edit Restaurant</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    {editError && <Alert variant="danger">{editError}</Alert>}
                    {editSuccess && <Alert variant="success">{editSuccess}</Alert>}
                    <Row>
                        <Col md={6}>
                            <Form.Group className="mb-3">
                                <Form.Label>Name</Form.Label>
                                <Form.Control value={editData.name || ''} onChange={(e) => setEditData({ ...editData, name: e.target.value })} />
                            </Form.Group>
                        </Col>
                        <Col md={6}>
                            <Form.Group className="mb-3">
                                <Form.Label>Cuisine Type</Form.Label>
                                <Form.Control value={editData.cuisine_type || ''} onChange={(e) => setEditData({ ...editData, cuisine_type: e.target.value })} />
                            </Form.Group>
                        </Col>
                    </Row>
                    <Form.Group className="mb-3">
                        <Form.Label>Description</Form.Label>
                        <Form.Control as="textarea" rows={2} value={editData.description || ''} onChange={(e) => setEditData({ ...editData, description: e.target.value })} />
                    </Form.Group>
                    <Row>
                        <Col md={4}>
                            <Form.Group className="mb-3">
                                <Form.Label>Price Range</Form.Label>
                                <Form.Select value={editData.price_range || ''} onChange={(e) => setEditData({ ...editData, price_range: e.target.value })}>
                                    <option value="$">$</option><option value="$$">$$</option><option value="$$$">$$$</option><option value="$$$$">$$$$</option>
                                </Form.Select>
                            </Form.Group>
                        </Col>
                        <Col md={4}>
                            <Form.Group className="mb-3">
                                <Form.Label>Phone</Form.Label>
                                <Form.Control value={editData.phone || ''} onChange={(e) => setEditData({ ...editData, phone: e.target.value })} />
                            </Form.Group>
                        </Col>
                        <Col md={4}>
                            <Form.Group className="mb-3">
                                <Form.Label>Website</Form.Label>
                                <Form.Control value={editData.website || ''} onChange={(e) => setEditData({ ...editData, website: e.target.value })} />
                            </Form.Group>
                        </Col>
                    </Row>
                    <Row>
                        <Col md={5}><Form.Group className="mb-3"><Form.Label>Address</Form.Label><Form.Control value={editData.address || ''} onChange={(e) => setEditData({ ...editData, address: e.target.value })} /></Form.Group></Col>
                        <Col md={3}><Form.Group className="mb-3"><Form.Label>City</Form.Label><Form.Control value={editData.city || ''} onChange={(e) => setEditData({ ...editData, city: e.target.value })} /></Form.Group></Col>
                        <Col md={2}><Form.Group className="mb-3"><Form.Label>State</Form.Label><Form.Control maxLength={2} value={editData.state || ''} onChange={(e) => setEditData({ ...editData, state: e.target.value.toUpperCase() })} /></Form.Group></Col>
                        <Col md={2}><Form.Group className="mb-3"><Form.Label>Zip</Form.Label><Form.Control value={editData.zip_code || ''} onChange={(e) => setEditData({ ...editData, zip_code: e.target.value })} /></Form.Group></Col>
                    </Row>
                    <Card className="mb-3">
                        <Card.Body>
                            <div className="d-flex justify-content-between align-items-center mb-2">
                                <Form.Label className="mb-0 fw-bold">Hours of Operation</Form.Label>
                                <Button variant="outline-secondary" size="sm" onClick={() => handleApplyToAll(editHours['Monday'] || '9:00 AM - 9:00 PM')}>Apply Monday to all</Button>
                            </div>
                            {DAYS_OF_WEEK.map((day) => (
                                <Row key={day} className="mb-1 align-items-center">
                                    <Col xs={4} sm={3}><small>{day}</small></Col>
                                    <Col xs={8} sm={9}><Form.Control type="text" size="sm" placeholder="e.g., 9:00 AM - 9:00 PM or Closed" value={editHours[day] || ''} onChange={(e) => handleHoursChange(day, e.target.value)} /></Col>
                                </Row>
                            ))}
                        </Card.Body>
                    </Card>
                    <Form.Group className="mb-3">
                        <Form.Label>Amenities</Form.Label>
                        <Form.Control type="text" placeholder="e.g., wifi, outdoor seating, family-friendly (comma-separated)" value={editAmenities} onChange={(e) => setEditAmenities(e.target.value)} />
                    </Form.Group>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="secondary" onClick={() => setShowEditModal(false)}>Cancel</Button>
                    <Button variant="primary" onClick={handleEditSubmit}>Save Changes</Button>
                </Modal.Footer>
            </Modal>
        </Container>
    );
}

export default OwnerDashboard;
