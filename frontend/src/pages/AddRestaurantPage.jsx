import { useState } from 'react';
import { Container, Row, Col, Card, Form, Button, Alert } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import { restaurantService } from '../services/restaurantService';

const DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

function AddRestaurantPage() {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        name: '',
        description: '',
        cuisine_type: '',
        price_range: '',
        address: '',
        city: '',
        state: '',
        zip_code: '',
        phone: '',
        website: '',
    });
    const [amenitiesInput, setAmenitiesInput] = useState('');
    const [photoUrlInput, setPhotoUrlInput] = useState('');
    const [photoUrls, setPhotoUrls] = useState([]);
    const [hours, setHours] = useState({});
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    // Hours helpers
    const handleHoursChange = (day, value) => {
        setHours((prev) => {
            const updated = { ...prev };
            if (value.trim()) {
                updated[day] = value;
            } else {
                delete updated[day];
            }
            return updated;
        });
    };

    const handleApplyToAll = (value) => {
        if (!value.trim()) return;
        const allHours = {};
        DAYS_OF_WEEK.forEach((day) => { allHours[day] = value; });
        setHours(allHours);
    };

    // Photo URL helpers
    const handleAddPhotoUrl = () => {
        const url = photoUrlInput.trim();
        if (!url) return;
        setPhotoUrls((prev) => [...prev, url]);
        setPhotoUrlInput('');
    };

    const handleRemovePhotoUrl = (index) => {
        setPhotoUrls((prev) => prev.filter((_, i) => i !== index));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        if (!formData.name.trim()) {
            setError('Restaurant name is required');
            return;
        }

        setLoading(true);
        try {
            const amenities = amenitiesInput
                .split(',')
                .map((a) => a.trim().toLowerCase())
                .filter((a) => a);

            const payload = {
                ...formData,
                amenities: amenities.length > 0 ? amenities : null,
                description: formData.description || null,
                cuisine_type: formData.cuisine_type || null,
                price_range: formData.price_range || null,
                phone: formData.phone || null,
                website: formData.website || null,
                hours: Object.keys(hours).length > 0 ? hours : null,
                photo_urls: photoUrls.length > 0 ? photoUrls : undefined,
            };

            const result = await restaurantService.createRestaurant(payload);
            navigate(`/restaurants/${result.id}`);
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to create restaurant');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Container className="mt-4">
            <Row className="justify-content-center">
                <Col md={8}>
                    <Card>
                        <Card.Body className="p-4">
                            <h2 className="mb-4">Add a Restaurant</h2>

                            {error && <Alert variant="danger">{error}</Alert>}

                            <Form onSubmit={handleSubmit}>
                                <Form.Group className="mb-3">
                                    <Form.Label>Restaurant Name *</Form.Label>
                                    <Form.Control
                                        type="text"
                                        name="name"
                                        placeholder="e.g., Pasta Paradise"
                                        value={formData.name}
                                        onChange={handleChange}
                                        required
                                    />
                                </Form.Group>

                                <Form.Group className="mb-3">
                                    <Form.Label>Description</Form.Label>
                                    <Form.Control
                                        as="textarea"
                                        rows={3}
                                        name="description"
                                        placeholder="Describe the restaurant..."
                                        value={formData.description}
                                        onChange={handleChange}
                                    />
                                </Form.Group>

                                <Row>
                                    <Col md={6}>
                                        <Form.Group className="mb-3">
                                            <Form.Label>Cuisine Type</Form.Label>
                                            <Form.Select name="cuisine_type" value={formData.cuisine_type} onChange={handleChange}>
                                                <option value="">Select cuisine...</option>
                                                <option value="Italian">Italian</option>
                                                <option value="Mexican">Mexican</option>
                                                <option value="Japanese">Japanese</option>
                                                <option value="Chinese">Chinese</option>
                                                <option value="Indian">Indian</option>
                                                <option value="American">American</option>
                                                <option value="French">French</option>
                                                <option value="Thai">Thai</option>
                                                <option value="Korean">Korean</option>
                                                <option value="Mediterranean">Mediterranean</option>
                                                <option value="Vegetarian">Vegetarian</option>
                                                <option value="Other">Other</option>
                                            </Form.Select>
                                        </Form.Group>
                                    </Col>
                                    <Col md={6}>
                                        <Form.Group className="mb-3">
                                            <Form.Label>Price Range</Form.Label>
                                            <Form.Select name="price_range" value={formData.price_range} onChange={handleChange}>
                                                <option value="">Select price range...</option>
                                                <option value="$">$ - Budget</option>
                                                <option value="$$">$$ - Moderate</option>
                                                <option value="$$$">$$$ - Expensive</option>
                                                <option value="$$$$">$$$$ - Very Expensive</option>
                                            </Form.Select>
                                        </Form.Group>
                                    </Col>
                                </Row>

                                <Form.Group className="mb-3">
                                    <Form.Label>Address</Form.Label>
                                    <Form.Control
                                        type="text"
                                        name="address"
                                        placeholder="e.g., 123 Main St"
                                        value={formData.address}
                                        onChange={handleChange}
                                    />
                                </Form.Group>

                                <Row>
                                    <Col md={5}>
                                        <Form.Group className="mb-3">
                                            <Form.Label>City</Form.Label>
                                            <Form.Control
                                                type="text"
                                                name="city"
                                                placeholder="e.g., San Francisco"
                                                value={formData.city}
                                                onChange={handleChange}
                                            />
                                        </Form.Group>
                                    </Col>
                                    <Col md={3}>
                                        <Form.Group className="mb-3">
                                            <Form.Label>State (Abbr.)</Form.Label>
                                            <Form.Control
                                                type="text"
                                                name="state"
                                                placeholder="e.g., CA"
                                                maxLength={2}
                                                value={formData.state}
                                                onChange={(e) => setFormData({ ...formData, state: e.target.value.toUpperCase() })}
                                            />
                                        </Form.Group>
                                    </Col>
                                    <Col md={4}>
                                        <Form.Group className="mb-3">
                                            <Form.Label>Zip Code</Form.Label>
                                            <Form.Control
                                                type="text"
                                                name="zip_code"
                                                placeholder="e.g., 94102"
                                                value={formData.zip_code}
                                                onChange={handleChange}
                                            />
                                        </Form.Group>
                                    </Col>
                                </Row>

                                <Row>
                                    <Col md={6}>
                                        <Form.Group className="mb-3">
                                            <Form.Label>Phone</Form.Label>
                                            <Form.Control
                                                type="tel"
                                                name="phone"
                                                placeholder="e.g., 415-555-0100"
                                                value={formData.phone}
                                                onChange={handleChange}
                                            />
                                        </Form.Group>
                                    </Col>
                                    <Col md={6}>
                                        <Form.Group className="mb-3">
                                            <Form.Label>Website</Form.Label>
                                            <Form.Control
                                                type="url"
                                                name="website"
                                                placeholder="e.g., https://example.com"
                                                value={formData.website}
                                                onChange={handleChange}
                                            />
                                        </Form.Group>
                                    </Col>
                                </Row>

                                {/* Hours of Operation */}
                                <Card className="mb-3">
                                    <Card.Body>
                                        <div className="d-flex justify-content-between align-items-center mb-2">
                                            <Form.Label className="mb-0 fw-bold">Hours of Operation</Form.Label>
                                            <Button
                                                variant="outline-secondary"
                                                size="sm"
                                                onClick={() => handleApplyToAll(hours['Monday'] || '9:00 AM - 9:00 PM')}
                                            >
                                                Apply Monday to all
                                            </Button>
                                        </div>
                                        {DAYS_OF_WEEK.map((day) => (
                                            <Row key={day} className="mb-1 align-items-center">
                                                <Col xs={4} sm={3}>
                                                    <small>{day}</small>
                                                </Col>
                                                <Col xs={8} sm={9}>
                                                    <Form.Control
                                                        type="text"
                                                        size="sm"
                                                        placeholder="e.g., 9:00 AM - 9:00 PM or Closed"
                                                        value={hours[day] || ''}
                                                        onChange={(e) => handleHoursChange(day, e.target.value)}
                                                    />
                                                </Col>
                                            </Row>
                                        ))}
                                        <Form.Text className="text-muted">
                                            Leave blank for days the restaurant is closed
                                        </Form.Text>
                                    </Card.Body>
                                </Card>

                                <Form.Group className="mb-3">
                                    <Form.Label>Amenities</Form.Label>
                                    <Form.Control
                                        type="text"
                                        placeholder="e.g., wifi, outdoor seating, family-friendly, quiet (comma-separated)"
                                        value={amenitiesInput}
                                        onChange={(e) => setAmenitiesInput(e.target.value)}
                                    />
                                    <Form.Text className="text-muted">
                                        Comma-separated keywords that describe the restaurant
                                    </Form.Text>
                                </Form.Group>

                                {/* Photo URLs */}
                                <Form.Group className="mb-4">
                                    <Form.Label>Photos</Form.Label>
                                    <div className="d-flex gap-2 mb-2">
                                        <Form.Control
                                            type="url"
                                            placeholder="Paste a photo URL and click Add"
                                            value={photoUrlInput}
                                            onChange={(e) => setPhotoUrlInput(e.target.value)}
                                            onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); handleAddPhotoUrl(); } }}
                                        />
                                        <Button variant="outline-secondary" onClick={handleAddPhotoUrl}>Add</Button>
                                    </div>
                                    {photoUrls.length > 0 && (
                                        <div className="d-flex flex-wrap gap-2">
                                            {photoUrls.map((url, idx) => (
                                                <div key={idx} className="position-relative">
                                                    <img
                                                        src={url}
                                                        alt={`Photo ${idx + 1}`}
                                                        style={{ height: '80px', borderRadius: '6px', objectFit: 'cover' }}
                                                        onError={(e) => { e.target.style.display = 'none'; }}
                                                    />
                                                    <Button
                                                        variant="danger"
                                                        size="sm"
                                                        className="position-absolute top-0 end-0"
                                                        style={{ padding: '0 4px', fontSize: '10px', lineHeight: '1.2' }}
                                                        onClick={() => handleRemovePhotoUrl(idx)}
                                                    >
                                                        ✕
                                                    </Button>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                    <Form.Text className="text-muted">
                                        Add photo URLs for the restaurant (images will preview above)
                                    </Form.Text>
                                </Form.Group>

                                <div className="d-flex gap-2">
                                    <Button type="submit" variant="danger" disabled={loading}>
                                        {loading ? 'Creating...' : 'Create Restaurant'}
                                    </Button>
                                    <Button variant="outline-secondary" onClick={() => navigate(-1)}>
                                        Cancel
                                    </Button>
                                </div>
                            </Form>
                        </Card.Body>
                    </Card>
                </Col>
            </Row>
        </Container>
    );
}

export default AddRestaurantPage;
