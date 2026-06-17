/**
 * JWT Authentication Helper
 * Handles token storage, retrieval, and injection for API calls
 */

const Auth = {
    // Token storage keys
    ACCESS_TOKEN_KEY: 'access_token',
    REFRESH_TOKEN_KEY: 'refresh_token',

    /**
     * Store access token in localStorage
     * @param {string} token - JWT access token
     */
    setAccessToken(token) {
        localStorage.setItem(this.ACCESS_TOKEN_KEY, token);
    },

    /**
     * Store refresh token in localStorage
     * @param {string} token - JWT refresh token
     */
    setRefreshToken(token) {
        localStorage.setItem(this.REFRESH_TOKEN_KEY, token);
    },

    /**
     * Get access token from localStorage
     * @returns {string|null} Access token or null if not found
     */
    getAccessToken() {
        return localStorage.getItem(this.ACCESS_TOKEN_KEY);
    },

    /**
     * Get refresh token from localStorage
     * @returns {string|null} Refresh token or null if not found
     */
    getRefreshToken() {
        return localStorage.getItem(this.REFRESH_TOKEN_KEY);
    },

    /**
     * Remove all tokens from localStorage
     */
    clearTokens() {
        localStorage.removeItem(this.ACCESS_TOKEN_KEY);
        localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    },

    /**
     * Check if user is authenticated
     * @returns {boolean} True if access token exists
     */
    isAuthenticated() {
        return !!this.getAccessToken();
    },

    /**
     * Get Authorization header with Bearer token
     * @returns {Object} Headers object with Authorization header
     */
    getAuthHeaders() {
        const token = this.getAccessToken();
        if (token) {
            return {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            };
        }
        return {
            'Content-Type': 'application/json'
        };
    },

    /**
     * Make authenticated API call
     * @param {string} url - API endpoint URL
     * @param {Object} options - Fetch options (method, body, etc.)
     * @returns {Promise} Fetch promise with response
     */
    async authenticatedFetch(url, options = {}) {
        const headers = this.getAuthHeaders();
        
        const config = {
            ...options,
            headers: {
                ...headers,
                ...options.headers
            }
        };

        try {
            const response = await fetch(url, config);
            
            // Handle 401 Unauthorized - token expired
            if (response.status === 401) {
                // Try to refresh token
                const refreshed = await this.refreshAccessToken();
                if (refreshed) {
                    // Retry original request with new token
                    return this.authenticatedFetch(url, options);
                } else {
                    // Refresh failed — guest-first: voltar ao dashboard
                    this.clearTokens();
                    window.location.href = '/';
                    return null;
                }
            }
            
            return response;
        } catch (error) {
            console.error('API call failed:', error);
            throw error;
        }
    },

    /**
     * Refresh access token using refresh token
     * @returns {Promise<boolean>} True if refresh successful
     */
    async refreshAccessToken() {
        const refreshToken = this.getRefreshToken();
        if (!refreshToken) {
            return false;
        }

        try {
            const response = await fetch('/api/token/refresh/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    refresh: refreshToken
                })
            });

            if (response.ok) {
                const data = await response.json();
                this.setAccessToken(data.access);
                return true;
            }
        } catch (error) {
            console.error('Token refresh failed:', error);
        }

        return false;
    },

    /**
     * Logout user and clear tokens
     */
    logout() {
        this.clearTokens();
        window.location.href = '/';
    }
};

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Auth;
}
