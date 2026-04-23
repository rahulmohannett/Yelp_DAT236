import { Routes, Route, Navigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { logoutAction } from './store/authSlice';
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

function App() {
  const { user, isAuthenticated } = useSelector(state => state.auth);
  const dispatch = useDispatch();

  const handleLogout = () => {
    dispatch(logoutAction());
  };

  return (
    <>
      <Navbar user={user} onLogout={handleLogout} />
      <Routes>
        <Route path="/" element={<HomePage user={user} />} />
        <Route path="/login" element={user ? <Navigate to="/" /> : <LoginPage />} />
        <Route path="/signup" element={user ? <Navigate to="/" /> : <SignupPage />} />
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