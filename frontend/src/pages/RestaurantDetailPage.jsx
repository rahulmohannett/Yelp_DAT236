import { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { fetchRestaurantByIdThunk, clearSelectedRestaurant } from '../store/restaurantSlice';
import { fetchReviewsThunk, createReviewThunk } from '../store/reviewSlice';
import { addFavoriteThunk } from '../store/favoritesSlice';
import { useState } from 'react';

function RestaurantDetailPage({ user }) {
  const { id } = useParams();
  const dispatch = useDispatch();
  const { selectedRestaurant, loading } = useSelector(state => state.restaurant);
  const { reviews, submitStatus } = useSelector(state => state.review);
  const [reviewText, setReviewText] = useState('');
  const [rating, setRating] = useState(5);

  useEffect(() => {
    dispatch(fetchRestaurantByIdThunk(id));
    dispatch(fetchReviewsThunk(id));
    return () => dispatch(clearSelectedRestaurant());
  }, [id]);

  const handleReviewSubmit = (e) => {
    e.preventDefault();
    dispatch(createReviewThunk({ restaurantId: id, reviewData: { text: reviewText, rating } }));
    setReviewText('');
    setRating(5);
  };

  const handleFavorite = () => {
    dispatch(addFavoriteThunk(id));
  };

  if (loading || !selectedRestaurant) return <div className="container mt-4">Loading...</div>;

  return (
    <div className="container mt-4">
      <div className="d-flex justify-content-between align-items-center">
        <h2>{selectedRestaurant.name}</h2>
        {user && <button className="btn btn-outline-danger" onClick={handleFavorite}>♥ Favorite</button>}
      </div>
      <p>{selectedRestaurant.cuisine} • {selectedRestaurant.city}</p>

      <hr />
      <h4>Reviews</h4>

      {submitStatus === 'pending' && <div className="alert alert-info">Your review is being processed...</div>}
      {submitStatus === 'success' && <div className="alert alert-success">Review submitted! It will appear shortly.</div>}
      {submitStatus === 'error' && <div className="alert alert-danger">Failed to submit review.</div>}

      {user && (
        <form onSubmit={handleReviewSubmit} className="mb-4">
          <div className="mb-2">
            <textarea className="form-control" rows="3" placeholder="Write a review..."
              value={reviewText} onChange={e => setReviewText(e.target.value)} required />
          </div>
          <div className="mb-2">
            <select className="form-control" value={rating} onChange={e => setRating(e.target.value)}>
              {[5,4,3,2,1].map(n => <option key={n} value={n}>{n} stars</option>)}
            </select>
          </div>
          <button type="submit" className="btn btn-primary">Submit Review</button>
        </form>
      )}

      {reviews.map(r => (
        <div className="card mb-2" key={r.id}>
          <div className="card-body">
            <p>{r.text}</p>
            <small>Rating: {r.rating}/5</small>
          </div>
        </div>
      ))}
    </div>
  );
}

export default RestaurantDetailPage;