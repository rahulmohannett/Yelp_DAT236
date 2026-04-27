import { useState } from 'react';
import { Container, Row, Col, Form, Button, Alert, Card } from 'react-bootstrap';
import { Link, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { registerThunk } from '../store/authSlice';

const CITIES = [
  'San Jose', 'San Francisco', 'Palo Alto', 'Berkeley', 'Oakland',
  'Mountain View', 'Sunnyvale', 'Cupertino', 'Santa Clara', 'Fremont',
  'Redwood City', 'San Mateo', 'Hayward', 'Milpitas', 'Campbell',
  'Los Altos', 'Menlo Park'
];

function SignupPage({ onLogin }) {
    const [formData, setFormData] = useState({
        name: '', email: '', password: '', confirmPassword: '', role: 'customer', city: '',
    });
    const navigate = useNavigate();
    const dispatch = useDispatch();
    const { loading, error } = useSelector(state => state.auth);

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (formData.password !== formData.confirmPassword) {
            return;
        }
        const result = await dispatch(registerThunk({
            email: formData.email,
            password: formData.password,
            name: formData.name,
            role: formData.role,
            city: formData.role === 'owner' ? formData.city : null
        }));
        if (registerThunk.fulfilled.match(result)) {
            navigate('/');
        }
    };

    return (
        <Container className="mt-5">
            <Row className="justify-content-center">
                <Col md={6} sm={10}>
                    <Card>
                        <Card.Body className="p-5">
                            <h2 className="text-center mb-4">Sign Up</h2>
                            {error && <Alert variant="danger">{error}</Alert>}
                            <Form onSubmit={handleSubmit}>
                                <Form.Group className="mb-3">
                                    <Form.Label>Name</Form.Label>
                                    <Form.Control type="text" name="name" placeholder="Enter your name"
                                        value={formData.name} onChange={handleChange} required />
                                </Form.Group>
                                <Form.Group className="mb-3">
                                    <Form.Label>Email</Form.Label>
                                    <Form.Control type="email" name="email" placeholder="Enter email"
                                        value={formData.email} onChange={handleChange} required />
                                </Form.Group>
                                <Form.Group className="mb-3">
                                    <Form.Label>Password</Form.Label>
                                    <Form.Control type="password" name="password" placeholder="Password"
                                        value={formData.password} onChange={handleChange} required />
                                </Form.Group>
                                <Form.Group className="mb-3">
                                    <Form.Label>Confirm Password</Form.Label>
                                    <Form.Control type="password" name="confirmPassword" placeholder="Confirm password"
                                        value={formData.confirmPassword} onChange={handleChange} required />
                                </Form.Group>
                                <Form.Group className="mb-3">
                                    <Form.Label>Account Type</Form.Label>
                                    <Form.Select name="role" value={formData.role} onChange={handleChange}>
                                        <option value="customer">Customer</option>
                                        <option value="owner">Restaurant Owner</option>
                                    </Form.Select>
                                </Form.Group>
                                {formData.role === 'owner' && (
                                    <Form.Group className="mb-3">
                                        <Form.Label>City</Form.Label>
                                        <Form.Select name="city" value={formData.city} onChange={handleChange} required={formData.role === 'owner'}>
                                            <option value="">Select a city</option>
                                            {CITIES.map(c => <option key={c} value={c}>{c}</option>)}
                                        </Form.Select>
                                    </Form.Group>
                                )}
                                <Button variant="danger" type="submit" className="w-100" disabled={loading}>
                                    {loading ? 'Signing up...' : 'Sign Up'}
                                </Button>
                            </Form>
                            <div className="text-center mt-3">
                                <p className="text-muted">Already have an account? <Link to="/login">Login</Link></p>
                            </div>
                        </Card.Body>
                    </Card>
                </Col>
            </Row>
        </Container>
    );
}

export default SignupPage;
