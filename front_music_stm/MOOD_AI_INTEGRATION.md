# 🎵 Modo Mood AI - Guía de Integración Frontend

## 📦 Archivos Creados

### 1. Componentes
- `src/components/player/MoodAIToggle.jsx` - Toggle principal del Modo Mood AI
- `src/components/player/MoodBadge.jsx` - Badge para mostrar mood actual

### 2. Servicios
- `src/services/moodService.js` - API client para el servicio de recomendaciones

## 🔧 Configuración

### 1. Variables de Entorno

Agregar al archivo `.env` del frontend:

```env
VITE_RECOMMENDATION_SERVICE_URL=http://localhost:8009/recommendations
```

### 2. Verificar AuthContext

El componente `MoodAIToggle` usa `useAuth()` de `@/contexts/AuthContext`.

Asegurarse de que exporta:
```javascript
const { authTokens } = useAuth();
// authTokens.access debe contener el JWT
```

## 🎨 Integración en Player

Ya integrado en `src/components/player/Player.jsx`:

```jsx
import MoodAIToggle from "./MoodAIToggle";

// En el render:
<MoodAIToggle className="mr-2" />
```

## 🚀 Uso en Otros Componentes

### Mostrar Mood Badge en Track Info

```jsx
import MoodBadge from '@/components/player/MoodBadge';

// En tu componente:
<MoodBadge mood="chill" size="sm" />
```

### Obtener Siguiente Canción con Mood AI

```jsx
import { moodAPI } from '@/services/moodService';
import { useAuth } from '@/contexts/AuthContext';

const MyComponent = () => {
  const { authTokens } = useAuth();

  const getNextSong = async () => {
    try {
      const track = await moodAPI.getNextTrackMoodBased(
        'playlist',  // context_type: 'playlist', 'liked', 'explore'
        42,          // context_id: ID de la playlist
        authTokens
      );
      
      console.log('Next track:', track);
      // track = { id, title, artist_name, duration, mood, mood_distance }
      
    } catch (error) {
      console.error('Error getting next track:', error);
    }
  };

  return <button onClick={getNextSong}>Get Next</button>;
};
```

### Registrar Skip de Canción

```jsx
const handleSkip = async (trackId) => {
  try {
    await moodAPI.registerSkip(trackId, authTokens);
    console.log('Skip registered');
  } catch (error) {
    console.error('Error registering skip:', error);
  }
};
```

## 🎨 Personalización de Estilos

### Colores de Mood

Editar en `MoodAIToggle.jsx` y `MoodBadge.jsx`:

```javascript
const MOOD_COLORS = {
  chill: 'from-blue-500 to-cyan-500',      // Azul frío
  happy: 'from-yellow-400 to-orange-500',  // Amarillo cálido
  sad: 'from-gray-500 to-blue-600',        // Gris azulado
  energetic: 'from-pink-500 to-red-500',   // Rosa-rojo
  intense: 'from-red-600 to-purple-700',   // Rojo-púrpura
  melancholic: 'from-indigo-500 to-purple-600', // Índigo-púrpura
};
```

### Íconos de Mood

```javascript
const MOOD_ICONS = {
  chill: '😌',
  happy: '😊',
  sad: '😢',
  energetic: '⚡',
  intense: '🔥',
  melancholic: '🌙',
};
```

## 🧩 Componentes Adicionales (Opcional)

### MoodSelector - Selector Manual de Mood

```jsx
// src/components/mood/MoodSelector.jsx
import { useState } from 'react';
import { moodAPI } from '@/services/moodService';

const MOODS = [
  { id: 'chill', label: 'Chill', emoji: '😌', color: 'blue' },
  { id: 'happy', label: 'Feliz', emoji: '😊', color: 'yellow' },
  { id: 'energetic', label: 'Energético', emoji: '⚡', color: 'pink' },
  { id: 'sad', label: 'Triste', emoji: '😢', color: 'gray' },
];

const MoodSelector = ({ onMoodSelect }) => {
  const [selected, setSelected] = useState(null);

  const handleSelect = (mood) => {
    setSelected(mood.id);
    onMoodSelect?.(mood.id);
  };

  return (
    <div className="grid grid-cols-2 gap-2">
      {MOODS.map(mood => (
        <button
          key={mood.id}
          onClick={() => handleSelect(mood)}
          className={`p-3 rounded-lg border-2 transition-all ${
            selected === mood.id
              ? 'border-purple-500 bg-purple-500/20'
              : 'border-gray-700 hover:border-gray-600'
          }`}
        >
          <span className="text-2xl">{mood.emoji}</span>
          <span className="block text-sm mt-1">{mood.label}</span>
        </button>
      ))}
    </div>
  );
};

export default MoodSelector;
```

### MoodFlow - Visualización de Moods

```jsx
// src/components/mood/MoodFlow.jsx
import { useEffect, useState } from 'react';
import { moodAPI } from '@/services/moodService';
import { useAuth } from '@/contexts/AuthContext';

const MoodFlow = () => {
  const { authTokens } = useAuth();
  const [moodHistory, setMoodHistory] = useState([]);

  useEffect(() => {
    const loadStatus = async () => {
      try {
        const status = await moodAPI.getMoodStatus(authTokens);
        setMoodHistory(status.recent_moods || []);
      } catch (error) {
        console.error('Error loading mood history:', error);
      }
    };
    
    loadStatus();
    const interval = setInterval(loadStatus, 30000); // Actualizar cada 30s
    
    return () => clearInterval(interval);
  }, [authTokens]);

  return (
    <div className="flex items-center gap-2">
      <span className="text-sm text-gray-400">Mood Flow:</span>
      <div className="flex gap-1">
        {moodHistory.map((mood, idx) => (
          <div
            key={idx}
            className="w-2 h-2 rounded-full bg-purple-500"
            style={{ opacity: 1 - (idx * 0.15) }}
          />
        ))}
      </div>
    </div>
  );
};

export default MoodFlow;
```

## 🔄 Integración con PlayerContext

Si quieres que el PlayerContext use Mood AI automáticamente:

```jsx
// En PlayerContext.jsx
import { moodAPI } from '@/services/moodService';

const nextTrack = async () => {
  try {
    // Verificar si Mood AI está activado
    const status = await moodAPI.getMoodStatus(authTokens);
    
    if (status.mood_ai_enabled) {
      // Usar recomendación basada en mood
      const track = await moodAPI.getNextTrackMoodBased(
        'explore',
        null,
        authTokens
      );
      setCurrentTrack(track);
    } else {
      // Comportamiento normal
      // ... tu lógica existente
    }
  } catch (error) {
    console.error('Error getting next track:', error);
  }
};
```

## 🎯 Tips de UX

1. **Feedback Visual**: El toggle muestra un glow cuando está activo
2. **Tooltip Informativo**: Hover sobre el toggle muestra el mood actual
3. **Badge de Estado**: Punto verde indica que Mood AI está activo
4. **Transiciones Suaves**: Animaciones CSS para cambios de estado

## 🐛 Troubleshooting

### El toggle no se muestra
- Verificar que el componente está importado correctamente
- Revisar que AuthContext está disponible
- Comprobar consola por errores de autenticación

### Error "Token no proporcionado"
- Asegurarse de que `authTokens.access` existe
- Verificar que el usuario está autenticado

### Error de CORS
- Agregar la URL del frontend a `FRONTEND_ORIGINS` en el backend
- Verificar que el servicio está corriendo en el puerto correcto

### El mood no se actualiza
- Verificar que hay canciones en el historial reciente
- Revisar que las canciones tienen género asignado en la BD
- Comprobar que las migraciones se ejecutaron correctamente

## 📞 Soporte

Para dudas sobre la integración frontend, revisar:
- `recommendation-service/README.md` - Documentación del backend
- API docs: `http://localhost:8009/docs` - Swagger UI interactivo

---

**Happy Coding!** 🎵✨
