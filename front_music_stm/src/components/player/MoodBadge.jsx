import { Sparkles } from 'lucide-react';

const MOOD_COLORS = {
  chill: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  happy: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  sad: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
  energetic: 'bg-pink-500/20 text-pink-400 border-pink-500/30',
  intense: 'bg-red-500/20 text-red-400 border-red-500/30',
  melancholic: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
};

const MOOD_LABELS = {
  chill: 'Chill',
  happy: 'Feliz',
  sad: 'Triste',
  energetic: 'Energético',
  intense: 'Intenso',
  melancholic: 'Melancólico',
};

const MoodBadge = ({ mood, size = 'sm' }) => {
  if (!mood) return null;

  const colorClass = MOOD_COLORS[mood] || 'bg-gray-500/20 text-gray-400 border-gray-500/30';
  const label = MOOD_LABELS[mood] || mood;
  const sizeClass = size === 'sm' ? 'text-xs px-2 py-0.5' : 'text-sm px-3 py-1';

  return (
    <span 
      className={`inline-flex items-center gap-1 rounded-full border ${colorClass} ${sizeClass} font-medium`}
      title={`Mood: ${label}`}
    >
      <Sparkles className="w-3 h-3" />
      {label}
    </span>
  );
};

export default MoodBadge;
