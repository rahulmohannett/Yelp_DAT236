import { useState, useEffect, useRef } from 'react';
import { Container, Row, Col, Card, Form, Button, Alert } from 'react-bootstrap';
import { userService } from '../services/userService';
import api from '../services/api';

const CITIES = [
  'San Jose', 'San Francisco', 'Palo Alto', 'Berkeley', 'Oakland',
  'Mountain View', 'Sunnyvale', 'Cupertino', 'Santa Clara', 'Fremont',
  'Redwood City', 'San Mateo', 'Hayward', 'Milpitas', 'Campbell',
  'Los Altos', 'Menlo Park'
];
const STATES = [
  'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA',
  'KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ',
  'NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT',
  'VA','WA','WV','WI','WY','DC'
];
const LANGUAGES = [
  'English', 'Spanish', 'Mandarin', 'Hindi', 'Arabic', 'French', 'Portuguese',
  'Japanese', 'Korean', 'German', 'Italian', 'Russian', 'Vietnamese', 'Tagalog',
  'Bengali', 'Punjabi', 'Telugu', 'Tamil', 'Urdu', 'Persian', 'Turkish'
];

function ProfilePage({ user }) {
    const [profileData, setProfileData] = useState({
        name: user.name || '',
        phone: '',
        about_me: '',
        city: '',
        country: '',
        state: '',
        languages: [],
        gender: '',
    });
    const [preferences, setPreferences] = useState({
        cuisine_preferences: [],
        price_range: '',
        dietary_needs: [],
        location: '',
        ambiance_preferences: [],
        sort_preference: '',
    });
    const [profilePicture, setProfilePicture] = useState(null);
    const [loading, setLoading] = useState(true);
    const [success, setSuccess] = useState('');
    const [error, setError] = useState('');
    const fileInputRef = useRef(null);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [profile, prefs] = await Promise.all([
                api.get('/users/me'),
                userService.getPreferences().catch(() => null),
            ]);

            setProfileData({
                name: profile.data.name || '',
                phone: profile.data.phone || '',
                about_me: profile.data.about_me || '',
                city: profile.data.city || '',
                country: profile.data.country || '',
                state: profile.data.state || '',
                languages: profile.data.languages || [],
                gender: profile.data.gender || '',
            });
            setProfilePicture(profile.data.profile_picture);

            if (prefs) {
                setPreferences({
                    cuisine_preferences: prefs.cuisine_preferences || [],
                    price_range: prefs.price_range || '',
                    dietary_needs: prefs.dietary_needs || [],
                    location: prefs.location || '',
                    ambiance_preferences: prefs.ambiance_preferences || [],
                    sort_preference: prefs.sort_preference || '',
                });
            }
        } catch (err) {
            console.error('Error loading data:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleProfileSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');
        try {
            await api.put('/users/me', profileData);
            setSuccess('Profile updated successfully!');
        } catch (err) {
            setError(err.response?.data?.detail || err.response?.data?.message || err.message || 'Failed to update profile');
        }
    };

    const handlePreferencesSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');
        try {
            await userService.updatePreferences(preferences);
            setSuccess('Preferences updated successfully!');
        } catch (err) {
            setError(err.response?.data?.detail || err.response?.data?.message || err.message || 'Failed to update preferences');
        }
    };

    const handleProfilePictureUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        setError('');
        setSuccess('');
        try {
            const result = await userService.uploadProfilePicture(file);
            setProfilePicture(result.profile_picture);
            setSuccess('Profile picture updated!');
        } catch (err) {
            setError(err.response?.data?.detail || err.response?.data?.message || err.message || 'Failed to upload profile picture');
        }
    };

    const handleArrayChange = (field, value, isProfile = false) => {
        const values = value.split(',').map((v) => v.trim()).filter((v) => v);
        if (isProfile) {
            setProfileData({ ...profileData, [field]: values });
        } else {
            setPreferences({ ...preferences, [field]: values });
        }
    };

    // Build full URL for profile picture
    const pictureUrl = profilePicture
        ? profilePicture.startsWith('http')
            ? profilePicture
            : profilePicture.startsWith('/')
                ? profilePicture
                : `/uploads/${profilePicture}`
        : null;

    if (loading) {
        return <Container className="mt-5 text-center">Loading...</Container>;
    }

    return (
        <Container className="mt-4">
            <Row>
                <Col md={10} className="mx-auto">
                    <h2 className="mb-4">Profile & Preferences</h2>

                    {success && <Alert variant="success" dismissible onClose={() => setSuccess('')}>{success}</Alert>}
                    {error && <Alert variant="danger" dismissible onClose={() => setError('')}>{error}</Alert>}

                    {/* Profile Picture */}
                    <Card className="mb-4">
                        <Card.Body className="d-flex align-items-center gap-4">
                            <div className="profile-picture-container">
                                {pictureUrl ? (
                                    <img
                                        src={pictureUrl}
                                        alt="Profile"
                                        onError={() => setProfilePicture(null)}
                                    />
                                ) : (
                                    <div
                                        style={{
                                            width: 120,
                                            height: 120,
                                            borderRadius: '50%',
                                            background: '#dc3545',
                                            color: 'white',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            fontSize: 36,
                                            fontWeight: 'bold',
                                        }}
                                    >
                                        {profileData.name?.charAt(0)?.toUpperCase() || 'U'}
                                    </div>
                                )}
                                <div
                                    className="profile-picture-overlay"
                                    onClick={() => fileInputRef.current?.click()}
                                    title="Upload photo"
                                >
                                    📷
                                </div>
                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    accept="image/jpeg,image/png,image/gif,image/webp"
                                    style={{ display: 'none' }}
                                    onChange={handleProfilePictureUpload}
                                />
                            </div>
                            <div>
                                <h4 className="mb-1">{profileData.name}</h4>
                                <p className="text-muted mb-0">{user.email}</p>
                                <small className="text-muted">Role: {user.role}</small>
                            </div>
                        </Card.Body>
                    </Card>

                    {/* Profile Information */}
                    <Card className="mb-4">
                        <Card.Body>
                            <h5 className="mb-3">Account Information</h5>

                            <Form onSubmit={handleProfileSubmit}>
                                <Row>
                                    <Col md={6}>
                                        <Form.Group className="mb-3">
                                            <Form.Label>Name *</Form.Label>
                                            <Form.Control
                                                type="text"
                                                value={profileData.name}
                                                onChange={(e) => setProfileData({ ...profileData, name: e.target.value })}
                                                required
                                            />
                                        </Form.Group>
                                    </Col>
                                    <Col md={6}>
                                        <Form.Group className="mb-3">
                                            <Form.Label>Phone Number</Form.Label>
                                            <Form.Control
                                                type="tel"
                                                placeholder="e.g., +1 (555) 123-4567"
                                                value={profileData.phone}
                                                onChange={(e) => setProfileData({ ...profileData, phone: e.target.value })}
                                            />
                                        </Form.Group>
                                    </Col>
                                </Row>

                                <Form.Group className="mb-3">
                                    <Form.Label>About Me</Form.Label>
                                    <Form.Control
                                        as="textarea"
                                        rows={3}
                                        placeholder="Tell us about yourself..."
                                        value={profileData.about_me}
                                        onChange={(e) => setProfileData({ ...profileData, about_me: e.target.value })}
                                    />
                                </Form.Group>

                                <Row>
                                    <Col md={6}>
                                        <Form.Group className="mb-3">
                                            <Form.Label>City</Form.Label>
                                            <Form.Select value={profileData.city} onChange={(e) => setProfileData({ ...profileData, city: e.target.value })}>
                                                <option value="">Select a city</option>
                                                {CITIES.map(c => <option key={c} value={c}>{c}</option>)}
                                            </Form.Select>
                                        </Form.Group>
                                    </Col>
                                    <Col md={3}>
                                        <Form.Group className="mb-3">
                                            <Form.Label>State (Abbr.)</Form.Label>
                                            <Form.Select
                                                value={profileData.state}
                                                onChange={(e) => setProfileData({ ...profileData, state: e.target.value })}
                                            >
                                                <option value="">Select state</option>
                                                {STATES.map(s => <option key={s} value={s}>{s}</option>)}
                                            </Form.Select>
                                        </Form.Group>
                                    </Col>
                                    <Col md={3}>
                                        <Form.Group className="mb-3">
                                            <Form.Label>Country</Form.Label>
                                            <Form.Select
                                                value={profileData.country}
                                                onChange={(e) => setProfileData({ ...profileData, country: e.target.value })}
                                            >
                                                <option value="">Select...</option>
                                                <option value="USA">USA</option>
                                                <option value="Canada">Canada</option>
                                                <option value="UK">UK</option>
                                                <option value="India">India</option>
                                                <option value="Other">Other</option>
                                            </Form.Select>
                                        </Form.Group>
                                    </Col>
                                </Row>

                                <Row>
                                    <Col md={6}>
                                        <Form.Group className="mb-3">
                                            <Form.Label>Languages</Form.Label>
                                            <Form.Select
                                                value={(profileData.languages && profileData.languages[0]) || ''}
                                                onChange={(e) => {
                                                    setProfileData({
                                                        ...profileData,
                                                        languages: e.target.value ? [e.target.value] : [],
                                                    });
                                                }}
                                            >
                                                <option value="">Select...</option>
                                                {LANGUAGES.map((lang) => (
                                                    <option key={lang} value={lang}>{lang}</option>
                                                ))}
                                            </Form.Select>
                                        </Form.Group>
                                    </Col>
                                    <Col md={6}>
                                        <Form.Group className="mb-3">
                                            <Form.Label>Gender</Form.Label>
                                            <Form.Select
                                                value={profileData.gender}
                                                onChange={(e) => setProfileData({ ...profileData, gender: e.target.value })}
                                            >
                                                <option value="">Prefer not to say</option>
                                                <option value="Male">Male</option>
                                                <option value="Female">Female</option>
                                                <option value="Non-binary">Non-binary</option>
                                                <option value="Other">Other</option>
                                            </Form.Select>
                                        </Form.Group>
                                    </Col>
                                </Row>

                                <Button type="submit" variant="primary">Save Profile</Button>
                            </Form>
                        </Card.Body>
                    </Card>

                    {/* Dining Preferences */}
                    <Card>
                        <Card.Body>
                            <h5 className="mb-3">Dining Preferences</h5>
                            <p className="text-muted">
                                Set your preferences to help our AI assistant provide better recommendations
                            </p>

                            <Form onSubmit={handlePreferencesSubmit}>
                                <Form.Group className="mb-3">
                                    <Form.Label>Favorite Cuisines</Form.Label>
                                    <Form.Control
                                        type="text"
                                        placeholder="e.g., Italian, Mexican, Japanese (comma-separated)"
                                        value={preferences.cuisine_preferences?.join(', ') || ''}
                                        onChange={(e) => handleArrayChange('cuisine_preferences', e.target.value)}
                                    />
                                </Form.Group>

                                <Row>
                                    <Col md={6}>
                                        <Form.Group className="mb-3">
                                            <Form.Label>Preferred Price Range</Form.Label>
                                            <Form.Select
                                                value={preferences.price_range || ''}
                                                onChange={(e) => setPreferences({ ...preferences, price_range: e.target.value })}
                                            >
                                                <option value="">No preference</option>
                                                <option value="$">$ - Budget</option>
                                                <option value="$$">$$ - Moderate</option>
                                                <option value="$$$">$$$ - Expensive</option>
                                                <option value="$$$$">$$$$ - Very Expensive</option>
                                            </Form.Select>
                                        </Form.Group>
                                    </Col>
                                    <Col md={6}>
                                        <Form.Group className="mb-3">
                                            <Form.Label>Sort Preference</Form.Label>
                                            <Form.Select
                                                value={preferences.sort_preference || ''}
                                                onChange={(e) => setPreferences({ ...preferences, sort_preference: e.target.value })}
                                            >
                                                <option value="">Default</option>
                                                <option value="rating">Rating</option>
                                                <option value="price">Price</option>
                                                <option value="popularity">Popularity</option>
                                                <option value="distance">Distance</option>
                                            </Form.Select>
                                        </Form.Group>
                                    </Col>
                                </Row>

                                <Form.Group className="mb-3">
                                    <Form.Label>Dietary Needs</Form.Label>
                                    <Form.Control
                                        type="text"
                                        placeholder="e.g., Vegan, Gluten-free (comma-separated)"
                                        value={preferences.dietary_needs?.join(', ') || ''}
                                        onChange={(e) => handleArrayChange('dietary_needs', e.target.value)}
                                    />
                                </Form.Group>

                                <Form.Group className="mb-3">
                                    <Form.Label>Preferred Location</Form.Label>
                                    <Form.Control
                                        type="text"
                                        placeholder="e.g., San Francisco"
                                        value={preferences.location || ''}
                                        onChange={(e) => setPreferences({ ...preferences, location: e.target.value })}
                                    />
                                </Form.Group>

                                <Form.Group className="mb-3">
                                    <Form.Label>Ambiance Preferences</Form.Label>
                                    <Form.Control
                                        type="text"
                                        placeholder="e.g., Romantic, Casual, Upscale (comma-separated)"
                                        value={preferences.ambiance_preferences?.join(', ') || ''}
                                        onChange={(e) => handleArrayChange('ambiance_preferences', e.target.value)}
                                    />
                                </Form.Group>

                                <Button type="submit" variant="primary">Save Preferences</Button>
                            </Form>
                        </Card.Body>
                    </Card>
                </Col>
            </Row>
        </Container>
    );
}

export default ProfilePage;
