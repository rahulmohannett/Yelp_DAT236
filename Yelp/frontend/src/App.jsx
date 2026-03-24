import { Routes, Route, Navigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import SearchPage from './pages/SearchPage';
import RestaurantDetailPage from './pages/RestaurantDetailPage';
import ProfilePage from './pages/ProfilePage';
import FavoritesPage from './pages/FavoritesPage';
import HistoryPage from './pages/HistoryPage';
import OwnerDashboard from './pages/OwnerDashboard';
import AddRestaurantPage from './pages/AddRestaurantPage';
import ChatPage from './pages/ChatPage';
import { authService } from './services/authService';

function App() {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const currentUser = authService.getCurrentUser();
        setUser(currentUser);
        setLoading(false);
    }, []);

    const handleLogin = (userData) => {
        setUser(userData);
    };

    const handleLogout = () => {
        authService.logout();
        setUser(null);
    };

    if (loading) {
        return <div className="text-center mt-5">Loading...</div>;
    }

    return (
        <>
            <Navbar user={user} onLogout={handleLogout} />
            <Routes>
                <Route path="/" element={<HomePage user={user} />} />
                <Route path="/login" element={user ? <Navigate to="/" /> : <LoginPage onLogin={handleLogin} />} />
                <Route path="/signup" element={user ? <Navigate to="/" /> : <SignupPage onLogin={handleLogin} />} />
                <Route path="/search" element={<SearchPage />} />
                <Route path="/restaurants/:id" element={<RestaurantDetailPage user={user} />} />
                <Route path="/profile" element={user ? <ProfilePage user={user} /> : <Navigate to="/login" />} />
                <Route path="/favorites" element={user ? <FavoritesPage /> : <Navigate to="/login" />} />
                <Route path="/history" element={user ? <HistoryPage /> : <Navigate to="/login" />} />
                <Route path="/add-restaurant" element={user ? <AddRestaurantPage /> : <Navigate to="/login" />} />
                <Route path="/chat" element={user ? <ChatPage /> : <Navigate to="/login" />} />
                <Route path="/owner/dashboard" element={user?.role === 'owner' ? <OwnerDashboard /> : <Navigate to="/" />} />
            </Routes>
        </>
    );
}

export default App;
