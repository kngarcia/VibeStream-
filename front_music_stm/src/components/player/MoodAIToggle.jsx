import { useState, useEffect } from 'react';
import { Sparkles } from 'lucide-react';
import { moodAPI } from '@/services/moodService';
import { useAuth } from '@/contexts/AuthContexts';

const MoodAIToggle = ({ className = '' }) => {
  const { authTokens } = useAuth();
  const [enabled, setEnabled] = useState(false);
  const [loading, setLoading] = useState(false);

  // Cargar estado inicial
  useEffect(() => {
    loadMoodStatus();
  }, []);

  const loadMoodStatus = async () => {
    try {
      const status = await moodAPI.getMoodStatus(authTokens);
      setEnabled(status.mood_ai_enabled);
    } catch (error) {
      console.error('Error loading mood status:', error);
    }
  };

  const handleToggle = async () => {
    if (loading) return;

    setLoading(true);
    try {
      const response = await moodAPI.toggleMoodAI(!enabled, authTokens);
      setEnabled(response.mood_ai_enabled);
      
      // Feedback en consola
      if (response.mood_ai_enabled) {
        console.log('✨ Modo Mood AI activado');
      } else {
        console.log('Modo Mood AI desactivado');
      }
    } catch (error) {
      console.error('Error toggling mood AI:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleToggle}
      disabled={loading}
      className={`p-1 rounded-full transition-colors ${
        enabled ? 'text-purple-500' : 'text-gray-400 hover:text-white'
      } ${className}`}
      title={enabled ? 'Modo Mood AI Activado' : 'Activar Modo Mood AI'}
    >
      {loading ? (
        <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
      ) : (
        <Sparkles className={`w-4 h-4 ${enabled ? '' : ''}`} />
      )}
    </button>
  );
};

export default MoodAIToggle;
