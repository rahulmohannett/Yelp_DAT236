import api from './api';

export const userService = {
    async getProfile() {
        const response = await api.get('/users/me');
        return response.data;
    },

    async getPreferences() {
        const response = await api.get('/users/me/preferences');
        return response.data;
    },

    async updatePreferences(preferences) {
        const response = await api.put('/users/me/preferences', preferences);
        return response.data;
    },

    async uploadProfilePicture(file) {
        const formData = new FormData();
        formData.append('file', file);
        const response = await api.post('/users/me/profile-picture', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return response.data;
    },

    async getFavorites() {
        const response = await api.get('/favorites');
        return response.data;
    },

    async addFavorite(restaurantId) {
        const response = await api.post('/favorites', { restaurant_id: restaurantId });
        return response.data;
    },

    async removeFavorite(restaurantId) {
        await api.delete(`/favorites/${restaurantId}`);
    },
};

export default userService;
