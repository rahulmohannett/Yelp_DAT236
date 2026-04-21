import { useState, useEffect, useCallback } from 'react';
import { Container, Row, Col, Form, Button, Spinner, Badge } from 'react-bootstrap';
import { restaurantService } from '../services/restaurantService';
import RestaurantCard from '../components/RestaurantCard';

const CUISINE_OPTIONS = ['Italian', 'Mexican', 'Japanese', 'Chinese', 'Indian', 'American', 'Thai', 'Mediterranean', 'Vegetarian'];
const DIETARY_OPTIONS = ['Vegetarian', 'Vegan', 'Halal', 'Gluten-Free', 'Kosher', 'Dairy-Free', 'Nut-Free'];
const AMBIANCE_OPTIONS = ['Casual', 'Fine Dining', 'Family-Friendly', 'Romantic', 'Outdoor', 'Quiet', 'Trendy', 'Sports Bar'];
const POPULAR_KEYWORDS = ['Quiet', 'Family Friendly', 'Outdoor Seating', 'WiFi', 'Good for Groups'];

function SearchPage() {
    const [restaurants, setRestaurants] = useState([]);
    const [loading, setLoading] = useState(true);
    const [sortBy, setSortBy] = useState('');
    const [showFilters, setShowFilters] = useState(false);
    const [filters, setFilters] = useState({
        search: '',
        cuisine: '',
        price_range: '',
        city: '',
        zip_code: '',
        keywords: '',
    });
    const [selectedDietary, setSelectedDietary] = useState([]);
    const [selectedAmbiance, setSelectedAmbiance] = useState([]);

    const buildKeywords = useCallback(() => {
        const parts = [];
        if (filters.keywords.trim()) parts.push(filters.keywords.trim());
        parts.push(...selectedDietary.map((d) => d.toLowerCase()));
        parts.push(...selectedAmbiance.map((a) => a.toLowerCase()));
        return parts.join(', ');
    }, [filters.keywords, selectedDietary, selectedAmbiance]);

    const loadRestaurants = useCallback(async () => {
        setLoading(true);
        try {
            const searchFilters = {
                ...filters,
                keywords: buildKeywords() || undefined,
            };
            const data = await restaurantService.searchRestaurants(searchFilters);
            setRestaurants(data);
        } catch (error) {
            console.error('Error loading restaurants:', error);
        } finally {
            setLoading(false);
        }
    }, [filters, buildKeywords]);

    useEffect(() => {
        loadRestaurants();
    }, []);

    const handleFilterChange = (e) => {
        setFilters({ ...filters, [e.target.name]: e.target.value });
    };

    const handleSearch = (e) => {
        e.preventDefault();
        loadRestaurants();
    };

    const togglePill = (value, selected, setSelected) => {
        if (selected.includes(value)) {
            setSelected(selected.filter((v) => v !== value));
        } else {
            setSelected([...selected, value]);
        }
    };

    const handleQuickKeyword = (keyword) => {
        const lower = keyword.toLowerCase();
        if (selectedAmbiance.map((a) => a.toLowerCase()).includes(lower)) return;
        // Add to keywords input
        const current = filters.keywords.trim();
        const existing = current ? current.split(',').map((k) => k.trim().toLowerCase()) : [];
        if (!existing.includes(lower)) {
            setFilters({ ...filters, keywords: current ? `${current}, ${keyword}` : keyword });
        }
    };

    const handleClearFilters = () => {
        setFilters({ search: '', cuisine: '', price_range: '', city: '', zip_code: '', keywords: '' });
        setSelectedDietary([]);
        setSelectedAmbiance([]);
        setSortBy('');
    };

    const getSortedRestaurants = () => {
        if (!sortBy) return restaurants;
        const sorted = [...restaurants];
        switch (sortBy) {
            case 'rating':
                return sorted.sort((a, b) => (b.average_rating || 0) - (a.average_rating || 0));
            case 'price_asc':
                return sorted.sort((a, b) => (a.price_range || '').length - (b.price_range || '').length);
            case 'price_desc':
                return sorted.sort((a, b) => (b.price_range || '').length - (a.price_range || '').length);
            case 'popularity':
                return sorted.sort((a, b) => (b.review_count || 0) - (a.review_count || 0));
            case 'name':
                return sorted.sort((a, b) => (a.name || '').localeCompare(b.name || ''));
            default:
                return sorted;
        }
    };

    const sortedRestaurants = getSortedRestaurants();
    const hasActiveFilters = filters.cuisine || filters.price_range || filters.city || filters.zip_code ||
        filters.keywords || selectedDietary.length > 0 || selectedAmbiance.length > 0;

    return (
        <Container className="mt-4">
            <h2 className="mb-4">Search Restaurants</h2>

            {/* Main search bar */}
            <Form onSubmit={handleSearch} className="mb-3">
                <Row className="g-2">
                    <Col md={5}>
                        <Form.Control
                            type="text"
                            name="search"
                            placeholder="Restaurant, cuisine, amenity, or keyword..."
                            value={filters.search}
                            onChange={handleFilterChange}
                        />
                    </Col>
                    <Col md={3}>
                        <Form.Control
                            type="text"
                            name="city"
                            placeholder="City or ZIP code"
                            value={filters.city}
                            onChange={handleFilterChange}
                        />
                    </Col>
                    <Col md={2}>
                        <Button type="submit" variant="danger" className="w-100">
                            Search
                        </Button>
                    </Col>
                    <Col md={2}>
                        <Button
                            variant={showFilters ? 'secondary' : 'outline-secondary'}
                            className="w-100"
                            onClick={() => setShowFilters(!showFilters)}
                        >
                            🔍 Filters {hasActiveFilters && <Badge bg="danger" className="ms-1">!</Badge>}
                        </Button>
                    </Col>
                </Row>
            </Form>

            {/* Cuisine pills — always visible */}
            <div className="d-flex flex-wrap gap-2 mb-3">
                {CUISINE_OPTIONS.map((cuisine) => (
                    <Button
                        key={cuisine}
                        variant={filters.cuisine === cuisine ? 'danger' : 'outline-secondary'}
                        size="sm"
                        className="rounded-pill"
                        onClick={() => {
                            setFilters({ ...filters, cuisine: filters.cuisine === cuisine ? '' : cuisine });
                        }}
                    >
                        {cuisine}
                    </Button>
                ))}
                {hasActiveFilters && (
                    <Button variant="link" size="sm" className="text-danger" onClick={handleClearFilters}>
                        ✕ Clear
                    </Button>
                )}
            </div>

            {/* Expanded filters panel */}
            {showFilters && (
                <div className="border rounded p-3 mb-4 bg-light">
                    <Row className="g-3">
                        {/* Keywords */}
                        <Col md={6}>
                            <Form.Label className="fw-bold" style={{ fontSize: '14px' }}>Keywords</Form.Label>
                            <Form.Control
                                type="text"
                                name="keywords"
                                placeholder="romantic, vegan, outdoor seating..."
                                value={filters.keywords}
                                onChange={handleFilterChange}
                            />
                        </Col>
                        <Col md={3}>
                            <Form.Label className="fw-bold" style={{ fontSize: '14px' }}>ZIP Code</Form.Label>
                            <Form.Control
                                type="text"
                                name="zip_code"
                                placeholder="e.g., 94102"
                                value={filters.zip_code}
                                onChange={handleFilterChange}
                            />
                        </Col>
                        <Col md={3}>
                            <Form.Label className="fw-bold" style={{ fontSize: '14px' }}>Price Range</Form.Label>
                            <div className="d-flex gap-1">
                                {['$', '$$', '$$$', '$$$$'].map((price) => (
                                    <Button
                                        key={price}
                                        variant={filters.price_range === price ? 'danger' : 'outline-secondary'}
                                        size="sm"
                                        onClick={() => setFilters({ ...filters, price_range: filters.price_range === price ? '' : price })}
                                    >
                                        {price}
                                    </Button>
                                ))}
                            </div>
                        </Col>
                    </Row>

                    {/* Dietary pills */}
                    <div className="mt-3">
                        <Form.Label className="fw-bold" style={{ fontSize: '14px' }}>Dietary Restrictions</Form.Label>
                        <div className="d-flex flex-wrap gap-2">
                            {DIETARY_OPTIONS.map((diet) => (
                                <Button
                                    key={diet}
                                    variant={selectedDietary.includes(diet) ? 'danger' : 'outline-secondary'}
                                    size="sm"
                                    className="rounded-pill"
                                    onClick={() => togglePill(diet, selectedDietary, setSelectedDietary)}
                                >
                                    {diet}
                                </Button>
                            ))}
                        </div>
                    </div>

                    {/* Ambiance pills */}
                    <div className="mt-3">
                        <Form.Label className="fw-bold" style={{ fontSize: '14px' }}>Ambiance</Form.Label>
                        <div className="d-flex flex-wrap gap-2">
                            {AMBIANCE_OPTIONS.map((amb) => (
                                <Button
                                    key={amb}
                                    variant={selectedAmbiance.includes(amb) ? 'danger' : 'outline-secondary'}
                                    size="sm"
                                    className="rounded-pill"
                                    onClick={() => togglePill(amb, selectedAmbiance, setSelectedAmbiance)}
                                >
                                    {amb}
                                </Button>
                            ))}
                        </div>
                    </div>

                    {/* Sort */}
                    <div className="mt-3">
                        <Form.Label className="fw-bold" style={{ fontSize: '14px' }}>Sort By</Form.Label>
                        <div className="d-flex flex-wrap gap-2">
                            {[
                                { value: 'rating', label: 'Rating' },
                                { value: 'popularity', label: 'Popularity' },
                                { value: 'price_asc', label: 'Price ↑' },
                                { value: 'price_desc', label: 'Price ↓' },
                            ].map((opt) => (
                                <Button
                                    key={opt.value}
                                    variant={sortBy === opt.value ? 'danger' : 'outline-secondary'}
                                    size="sm"
                                    onClick={() => setSortBy(sortBy === opt.value ? '' : opt.value)}
                                >
                                    {opt.label}
                                </Button>
                            ))}
                        </div>
                    </div>

                    {/* Popular keyword buttons */}
                    <div className="mt-3">
                        <Form.Label className="fw-bold" style={{ fontSize: '14px' }}>Popular Searches</Form.Label>
                        <div className="d-flex flex-wrap gap-2">
                            {POPULAR_KEYWORDS.map((kw) => (
                                <Button
                                    key={kw}
                                    variant="outline-dark"
                                    size="sm"
                                    className="rounded-pill"
                                    onClick={() => handleQuickKeyword(kw)}
                                >
                                    {kw}
                                </Button>
                            ))}
                        </div>
                    </div>

                    <div className="mt-3">
                        <Button variant="danger" onClick={() => { loadRestaurants(); }} className="me-2">
                            Apply Filters
                        </Button>
                        <Button variant="outline-secondary" onClick={handleClearFilters}>
                            Clear All
                        </Button>
                    </div>
                </div>
            )}

            {/* Results */}
            <p className="text-muted mb-3" style={{ fontSize: '14px' }}>
                {sortedRestaurants.length} restaurant{sortedRestaurants.length !== 1 ? 's' : ''} found
                {hasActiveFilters ? ' for your filters' : ''}
            </p>

            {loading ? (
                <div className="text-center">
                    <Spinner animation="border" />
                </div>
            ) : (
                <Row>
                    {sortedRestaurants.length === 0 ? (
                        <Col>
                            <p className="text-center text-muted">No restaurants found. Try adjusting your filters.</p>
                        </Col>
                    ) : (
                        sortedRestaurants.map((restaurant) => (
                            <Col key={restaurant.id} md={4} sm={6} className="mb-4">
                                <RestaurantCard restaurant={restaurant} />
                            </Col>
                        ))
                    )}
                </Row>
            )}
        </Container>
    );
}

export default SearchPage;
