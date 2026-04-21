import api from './api';

export const restaurantService = {
    async searchRestaurants(filters = {}) {
        const params = new URLSearchParams();
        if (filters.cuisine) params.append('cuisine', filters.cuisine);
        if (filters.price_range) params.append('price_range', filters.price_range);
        if (filters.city) params.append('city', filters.city);
        if (filters.zip_code) params.append('zip_code', filters.zip_code);
        if (filters.search) params.append('search', filters.search);
        if (filters.keywords) params.append('keywords', filters.keywords);
        const response = await api.get(`/restaurants?${params.toString()}`);
        return response.data;
    },

    async getRestaurant(id) {
        const response = await api.get(`/restaurants/${id}`);
        return response.data;
    },

    async createRestaurant(restaurantData) {
        const response = await api.post('/restaurants', restaurantData);
        return response.data;
    },

    async updateRestaurant(id, restaurantData) {
        const response = await api.put(`/restaurants/${id}`, restaurantData);
        return response.data;
    },

    async deleteRestaurant(id) {
        await api.delete(`/restaurants/${id}`);
    },

    async uploadPhoto(restaurantId, file) {
        const formData = new FormData();
        formData.append('file', file);
        const response = await api.post(`/restaurants/${restaurantId}/photos`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return response.data;
    },
};

export default restaurantService;
