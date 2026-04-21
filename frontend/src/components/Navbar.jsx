import { Link } from 'react-router-dom';
import { Navbar as BSNavbar, Nav, Container, Button } from 'react-bootstrap';

function Navbar({ user, onLogout }) {
    return (
        <BSNavbar bg="light" expand="lg" className="shadow-sm">
            <Container>
                <BSNavbar.Brand as={Link} to="/">
                    Yelp
                </BSNavbar.Brand>
                <BSNavbar.Toggle aria-controls="basic-navbar-nav" />
                <BSNavbar.Collapse id="basic-navbar-nav">
                    <Nav className="me-auto">
                        <Nav.Link as={Link} to="/search">Search </Nav.Link>
                        {user && (
                            <>
                                <Nav.Link as={Link} to="/favorites">Favorites</Nav.Link>
                                <Nav.Link as={Link} to="/history">History</Nav.Link>
                                <Nav.Link as={Link} to="/add-restaurant">Add Restaurant</Nav.Link>
                                <Nav.Link as={Link} to="/chat"> YelpAI</Nav.Link>
                                {user.role === 'owner' && (
                                    <Nav.Link as={Link} to="/owner/dashboard">My Restaurants</Nav.Link>
                                )}
                            </>
                        )}
                    </Nav>
                    <Nav>
                        {user ? (
                            <>
                                <Nav.Link as={Link} to="/profile">{user.name}</Nav.Link>
                                <Button variant="outline-danger" size="sm" onClick={onLogout}>Logout</Button>
                            </>
                        ) : (
                            <>
                                <Nav.Link as={Link} to="/login">Login</Nav.Link>
                                <Button as={Link} to="/signup" variant="danger" size="sm">Sign Up</Button>
                            </>
                        )}
                    </Nav>
                </BSNavbar.Collapse>
            </Container>
        </BSNavbar>
    );
}

export default Navbar;
