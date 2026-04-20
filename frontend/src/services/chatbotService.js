import api from './api';

export const chatbotService = {
    async sendMessage(message, conversationHistory = [], conversationId = null) {
        const payload = {
            message,
            conversation_history: conversationHistory,
        };
        if (conversationId) {
            payload.conversation_id = conversationId;
        }
        const response = await api.post('/ai-assistant/chat', payload);
        return response.data;
    },

    async getConversations() {
        const response = await api.get('/ai-assistant/conversations');
        return response.data;
    },

    async getConversation(conversationId) {
        const response = await api.get(`/ai-assistant/conversations/${conversationId}`);
        return response.data;
    },

    async deleteConversation(conversationId) {
        await api.delete(`/ai-assistant/conversations/${conversationId}`);
    },
};

export default chatbotService;
