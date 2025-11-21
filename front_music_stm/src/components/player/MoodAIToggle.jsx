import { useState, useEffect } from 'react';
import { Sparkles } from 'lucide-react';
import { moodAPI } from '@/services/moodService';
import { useAuth } from '@/contexts/AuthContexts';

const MOOD_COLORS = {
  chill: 'from-blue-500 to-cyan-500',
  happy: 'from-yellow-400 to-orange-500',
  sad: 'from-gray-500 to-blue-600',
  energetic: 'from-pink-500 to-red-500',
  intense: 'from-red-600 to-purple-700',
  melancholic: 'from-indigo-500 to-purple-600',
};

const MOOD_ICONS = {
  chill: '😌',
  happy: '😊',
  sad: '😢',
  energetic: '⚡',
  intense: '🔥',
  melancholic: '🌙',
};

const MOOD_LABELS = {
  chill: 'Chill',
  happy: 'Feliz',
  sad: 'Triste',
  energetic: 'Energético',
  intense: 'Intenso',
  melancholic: 'Melancólico',
};

const MoodAIToggle = ({ className = '' }) => {
  const { authTokens } = useAuth();
  const [enabled, setEnabled] = useState(false);
  const [currentMood, setCurrentMood] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);

  // Cargar estado inicial
  useEffect(() => {
    loadMoodStatus();
  }, []);

  const loadMoodStatus = async () => {
    try {
      const status = await moodAPI.getMoodStatus(authTokens);
      setEnabled(status.mood_ai_enabled);
      setCurrentMood(status.current_mood);
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
      setCurrentMood(response.current_mood);
      
      // Feedback visual
      if (response.mood_ai_enabled) {
        console.log('✨ Modo Mood AI activado:', response.current_mood);
      } else {
        console.log('Modo Mood AI desactivado');
      }
    } catch (error) {
      console.error('Error toggling mood AI:', error);
    } finally {
      setLoading(false);
    }
  };

  const moodColor = currentMood ? MOOD_COLORS[currentMood] : 'from-gray-600 to-gray-700';
  const moodIcon = currentMood ? MOOD_ICONS[currentMood] : '🎵';
  const moodLabel = currentMood ? MOOD_LABELS[currentMood] : 'Normal';

  return (
    <div className={`relative ${className}`}>
      {/* Toggle Button */}
      <button
        onClick={handleToggle}
        disabled={loading}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        className={`
          flex items-center gap-2 px-3 py-2 rounded-lg transition-all duration-300
          ${enabled 
            ? `bg-gradient-to-r ${moodColor} text-white shadow-lg hover:shadow-xl` 
            : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
          }
          disabled:opacity-50 disabled:cursor-not-allowed
        `}
        title={enabled ? `Mood AI: ${moodLabel}` : 'Activar Modo Mood AI'}
      >
        {loading ? (
          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
        ) : (
          <Sparkles className={`w-4 h-4 ${enabled ? 'animate-pulse' : ''}`} />
        )}
        
        <span className="text-sm font-medium hidden sm:inline">
          Mood AI
        </span>

        {enabled && currentMood && (
          <span className="text-lg leading-none">{moodIcon}</span>
        )}
      </button>

      {/* Tooltip */}
      {showTooltip && (
        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-800 text-white text-xs rounded-lg shadow-lg whitespace-nowrap z-50 border border-gray-700">
          {enabled ? (
            <>
              <div className="font-semibold mb-1">✨ Modo Mood AI Activado</div>
              <div className="text-gray-300">
                Mood actual: <span className="font-medium">{moodLabel} {moodIcon}</span>
              </div>
              <div className="text-gray-400 text-xs mt-1">
                La música se adapta a tu estado de ánimo
              </div>
            </>
          ) : (
            <>
              <div className="font-semibold mb-1">Modo Mood AI Desactivado</div>
              <div className="text-gray-400 text-xs">
                Activa para reproducción inteligente
              </div>
            </>
          )}
          {/* Flecha del tooltip */}
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-l-transparent border-r-4 border-r-transparent border-t-4 border-t-gray-800" />
        </div>
      )}

      {/* Mood Badge (visible cuando está activado) */}
      {enabled && currentMood && (
        <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full border-2 border-gray-900 animate-pulse" />
      )}
    </div>
  );
};

export default MoodAIToggle;
