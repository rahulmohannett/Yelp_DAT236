import api from './api';

export const reviewService = {
    async getRestaurantReviews(restaurantId) {
        const response = await api.get(`/reviews/restaurants/${restaurantId}/reviews`);
        return response.data;
    },

    async createReview(restaurantId, rating, reviewText) {
        const response = await api.post(`/reviews/restaurants/${restaurantId}/reviews`, {
            restaurant_id: restaurantId,
            rating,
            review_text: reviewText,
        });
        return response.data;
    },

    async updateReview(reviewId, rating, reviewText) {
        const response = await api.put(`/reviews/${reviewId}`, { rating, review_text: reviewText });
        return response.data;
    },

    async deleteReview(reviewId) {
        await api.delete(`/reviews/${reviewId}`);
    },

    async uploadReviewPhoto(reviewId, file) {
        const formData = new FormData();
        formData.append('file', file);
        const response = await api.post(`/reviews/${reviewId}/photos`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return response.data;
    },
};

export default reviewService;
