// Mood AI Service - API calls for mood-based recommendations

const MOOD_BASE_URL = import.meta.env.VITE_RECOMMENDATION_SERVICE_URL || 'http://localhost:8009/recommendations';

/**
 * Helper para hacer requests autenticados
 */
const authenticatedFetch = async (url, options = {}, authTokens) => {
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (authTokens?.access) {
    headers['Authorization'] = `Bearer ${authTokens.access}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Error: ${response.status}`);
  }

  return response.json();
};

export const moodAPI = {
  /**
   * Toggle Mood AI on/off
   */
  toggleMoodAI: async (enabled, authTokens) => {
    return authenticatedFetch(
      `${MOOD_BASE_URL}/mood/toggle`,
      {
        method: 'POST',
        body: JSON.stringify({
          enabled: enabled,
          transition_smoothness: 'medium'
        })
      },
      authTokens
    );
  },

  /**
   * Get current Mood AI status
   */
  getMoodStatus: async (authTokens) => {
    return authenticatedFetch(
      `${MOOD_BASE_URL}/mood/status`,
      { method: 'GET' },
      authTokens
    );
  },

  /**
   * Get next track based on mood
   */
  getNextTrackMoodBased: async (contextType, contextId, authTokens) => {
    return authenticatedFetch(
      `${MOOD_BASE_URL}/mood/next-track`,
      {
        method: 'POST',
        body: JSON.stringify({
          context_type: contextType,
          context_id: contextId
        })
      },
      authTokens
    );
  },

  /**
   * Get current mood of the session
   */
  getCurrentMood: async (authTokens) => {
    return authenticatedFetch(
      `${MOOD_BASE_URL}/mood/current`,
      { method: 'GET' },
      authTokens
    );
  },

  /**
   * Register a skip event
   */
  registerSkip: async (trackId, authTokens) => {
    return authenticatedFetch(
      `${MOOD_BASE_URL}/mood/skip`,
      {
        method: 'POST',
        body: JSON.stringify({
          track_id: trackId
        })
      },
      authTokens
    );
  }
};

export default moodAPI;
