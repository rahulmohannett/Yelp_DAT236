import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchFavoritesThunk, removeFavoriteThunk } from '../store/favoritesSlice';
import { Link } from 'react-router-dom';

function FavoritesPage() {
  const dispatch = useDispatch();
  const { favorites, loading } = useSelector(state => state.favorites);

  useEffect(() => {
    dispatch(fetchFavoritesThunk());
  }, []);

  const handleRemove = (id) => {
    dispatch(removeFavoriteThunk(id));
  };

  return (
    <div className="container mt-4">
      <h2>My Favorites</h2>
      {loading && <p>Loading...</p>}
      {favorites.length === 0 && !loading && <p>No favorites yet.</p>}
      <div className="row">
        {favorites.map(f => (
          <div className="col-md-4 mb-3" key={f.id}>
            <div className="card h-100">
              <div className="card-body">
                <h5 className="card-title">{f.restaurant?.name || f.name}</h5>
                <Link to={`/restaurants/${f.restaurantId || f.id}`} className="btn btn-outline-primary btn-sm me-2">View</Link>
                <button className="btn btn-outline-danger btn-sm" onClick={() => handleRemove(f.id)}>Remove</button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default FavoritesPage;