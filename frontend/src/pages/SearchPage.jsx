import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchRestaurantsThunk, setFilters } from '../store/restaurantSlice';
import { Link } from 'react-router-dom';

function SearchPage() {
  const dispatch = useDispatch();
  const { restaurants, loading, error, filters } = useSelector(state => state.restaurant);
  const [localFilters, setLocalFilters] = useState(filters || { city: '', cuisine: '' });

  useEffect(() => {
    dispatch(fetchRestaurantsThunk(localFilters));
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    dispatch(setFilters(localFilters));
    dispatch(fetchRestaurantsThunk(localFilters));
  };

  return (
    <div className="container mt-4">
      <h2>Search Restaurants</h2>
      <form onSubmit={handleSearch} className="row g-2 mb-4">
        <div className="col">
          <input type="text" className="form-control" placeholder="City"
            value={localFilters.city} onChange={e => setLocalFilters({ ...localFilters, city: e.target.value })} />
        </div>
        <div className="col">
          <input type="text" className="form-control" placeholder="Cuisine"
            value={localFilters.cuisine} onChange={e => setLocalFilters({ ...localFilters, cuisine: e.target.value })} />
        </div>
        <div className="col-auto">
          <button type="submit" className="btn btn-primary">Search</button>
        </div>
      </form>

      {loading && <p>Loading...</p>}
      {error && <div className="alert alert-danger">{error}</div>}

      <div className="row">
        {restaurants.map(r => (
          <div className="col-md-4 mb-3" key={r.id}>
            <div className="card h-100">
              <div className="card-body">
                <h5 className="card-title">{r.name}</h5>
                <p className="card-text">{r.cuisine} • {r.city}</p>
                <Link to={`/restaurants/${r.id}`} className="btn btn-outline-primary btn-sm">View</Link>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default SearchPage;