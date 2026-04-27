import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Navbar as BSNavbar, Nav, Container, Button, Image } from 'react-bootstrap';

function Navbar({ user, onLogout }) {
    const [avatarLoadFailed, setAvatarLoadFailed] = useState(false);
    const avatarUrl = user?.profile_picture
        ? user.profile_picture.startsWith('http')
            ? user.profile_picture
            : user.profile_picture.startsWith('/')
                ? user.profile_picture
                : `/uploads/${user.profile_picture}`
        : null;

    useEffect(() => {
        setAvatarLoadFailed(false);
    }, [avatarUrl]);

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
                                <Nav.Link as={Link} to="/profile" className="d-flex align-items-center gap-2">
                                    {avatarUrl && !avatarLoadFailed ? (
                                        <Image
                                            src={avatarUrl}
                                            roundedCircle
                                            width={28}
                                            height={28}
                                            style={{ objectFit: 'cover', border: '2px solid #dee2e6' }}
                                            onError={() => setAvatarLoadFailed(true)}
                                        />
                                    ) : (
                                        <div style={{
                                            width: 28, height: 28, borderRadius: '50%',
                                            background: '#dc3545', color: 'white',
                                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                                            fontSize: 12, fontWeight: 'bold', flexShrink: 0
                                        }}>
                                            {user.name?.charAt(0).toUpperCase()}
                                        </div>
                                    )}
                                    {user.name}
                                </Nav.Link>
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
