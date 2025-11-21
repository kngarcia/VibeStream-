# 🎵 Recommendation Service - Mood AI

Servicio de recomendación inteligente basado en **Mood/Estado de ánimo** para VibeStream.

## 🎯 Características

- **Detección automática de mood** de canciones basada en género musical
- **Recomendaciones mood-consistentes** que mantienen coherencia emocional
- **Transiciones suaves** entre diferentes estados de ánimo
- **Configuración personalizable** por usuario
- **Seguimiento de sesiones** de reproducción con contexto de mood

## 📋 Moods Soportados

| Mood | Emoji | Descripción | Géneros Típicos |
|------|-------|-------------|----------------|
| **Chill** | 😌 | Relajado, tranquilo | Lofi, Jazz, Ambient, Acoustic |
| **Happy** | 😊 | Feliz, positivo | Pop, Dance, Reggaeton, Funk |
| **Sad** | 😢 | Triste, emotivo | Blues, Ballad |
| **Energetic** | ⚡ | Energético, motivador | Rock, Electronic, Hip-Hop |
| **Intense** | 🔥 | Intenso, poderoso | Metal, Punk, Trap |
| **Melancholic** | 🌙 | Melancólico, reflexivo | Indie, Folk, Soul |

## 🏗️ Arquitectura

```
recommendation-service/
├── config.py                 # Configuración del servicio
├── main.py                   # FastAPI app
├── database/
│   ├── connection.py         # Conexión a PostgreSQL
│   └── models.py             # Modelos SQLAlchemy
├── services/
│   ├── mood_detection_service.py       # Detección de mood
│   └── mood_recommendation_service.py  # Motor de recomendación
├── handlers/
│   └── mood_handler.py       # Endpoints de la API
├── middleware/
│   └── auth_middleware.py    # Autenticación JWT
└── migrations/
    ├── 001_create_mood_tables.sql
    └── 002_populate_initial_moods.sql
```

## 🚀 Instalación y Configuración

### 1. Dependencias

```bash
cd recommendation-service
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Variables de Entorno

Agregar al archivo `.env` del proyecto:

```env
RECOMMENDATION_PORT=8009
```

### 3. Migraciones de Base de Datos

Ejecutar los scripts SQL en orden:

```bash
psql -h localhost -U your_user -d your_database -f migrations/001_create_mood_tables.sql
psql -h localhost -U your_user -d your_database -f migrations/002_populate_initial_moods.sql
```

### 4. Iniciar Servicio

#### Desarrollo:
```bash
python main.py
```

#### Producción (Docker):
```bash
docker-compose up recommendation-service
```

El servicio estará disponible en `http://localhost:8009`

## 📡 API Endpoints

### 1. Toggle Mood AI
**POST** `/recommendations/mood/toggle`

Activa o desactiva el Modo Mood AI para el usuario.

**Request:**
```json
{
  "enabled": true,
  "transition_smoothness": "medium"  // 'strict', 'medium', 'flexible'
}
```

**Response:**
```json
{
  "mood_ai_enabled": true,
  "current_mood": "chill",
  "transition_smoothness": "medium"
}
```

### 2. Get Mood Status
**GET** `/recommendations/mood/status`

Obtiene el estado actual del Modo Mood AI.

**Response:**
```json
{
  "mood_ai_enabled": true,
  "current_mood": "chill",
  "transition_smoothness": "medium",
  "recent_moods": ["chill", "chill", "happy"]
}
```

### 3. Get Next Track (Mood-Based)
**POST** `/recommendations/mood/next-track`

Obtiene la siguiente canción basada en el mood actual.

**Request:**
```json
{
  "context_type": "playlist",  // 'playlist', 'liked', 'explore'
  "context_id": 42
}
```

**Response:**
```json
{
  "id": 123,
  "title": "Lofi Dreams",
  "artist_name": "Chill Artist",
  "duration": 180,
  "mood": "chill",
  "mood_distance": 0.0
}
```

### 4. Get Current Mood
**GET** `/recommendations/mood/current`

Obtiene el mood dominante de la sesión actual.

**Response:**
```json
{
  "current_mood": "chill",
  "recent_tracks": [101, 102, 103],
  "context_type": "playlist"
}
```

### 5. Register Skip
**POST** `/recommendations/mood/skip`

Registra cuando el usuario salta una canción.

**Request:**
```json
{
  "track_id": 123
}
```

## 🔐 Autenticación

Todos los endpoints (excepto `/health`) requieren un token JWT válido:

```
Authorization: Bearer <jwt_token>
```

## 🧠 Algoritmo de Recomendación

### 1. Detección de Mood Dominante

El servicio analiza las últimas 5 canciones reproducidas y determina el mood más frecuente, ponderando:
- **Recencia**: Canciones más recientes tienen mayor peso
- **Completitud**: Canciones completadas pesan más que saltadas
- **Likes**: Canciones marcadas con "me gusta" reciben bonus

### 2. Compatibilidad de Moods

Matriz de distancia entre moods (0 = compatible, 1 = incompatible):

```python
MOOD_COMPATIBILITY = {
    'chill':       {'chill': 0.0, 'happy': 0.3, 'energetic': 0.7, 'intense': 1.0},
    'happy':       {'chill': 0.3, 'happy': 0.0, 'energetic': 0.2, 'sad': 0.8},
    'energetic':   {'happy': 0.2, 'energetic': 0.0, 'intense': 0.3, 'sad': 0.9},
    # ...
}
```

### 3. Niveles de Suavidad

- **Strict** (umbral 0.3): Solo moods muy similares
- **Medium** (umbral 0.6): Transiciones suaves permitidas
- **Flexible** (umbral 0.9): Casi cualquier transición

### 4. Selección de Canción

1. Obtener pool de candidatos según contexto (playlist/likes/explore)
2. Filtrar por compatibilidad de mood
3. Ordenar por distancia de mood (más cercano = mejor)
4. Seleccionar aleatoriamente entre top 3 (para variedad)

## 📊 Modelos de Datos

### track_mood_features
Almacena las características de mood de cada canción.

```sql
song_id INTEGER PRIMARY KEY
primary_mood VARCHAR(50)    -- 'chill', 'happy', etc.
secondary_mood VARCHAR(50)
tempo FLOAT                 -- BPM
energy FLOAT               -- 0.0 - 1.0
valence FLOAT              -- 0.0 (triste) - 1.0 (feliz)
mood_confidence FLOAT      -- Confianza del modelo
mood_tags JSONB            -- Tags adicionales
```

### user_mood_settings
Configuración del usuario.

```sql
user_id INTEGER PRIMARY KEY
mood_ai_enabled BOOLEAN
transition_smoothness VARCHAR(20)  -- 'strict', 'medium', 'flexible'
last_toggle_at TIMESTAMP
```

### mood_session_context
Contexto de sesión de reproducción.

```sql
user_id INTEGER
current_dominant_mood VARCHAR(50)
recent_track_ids JSONB
playback_context_type VARCHAR(50)
is_active BOOLEAN
```

## 🧪 Testing

```bash
# Health check
curl http://localhost:8009/health

# Get mood status (requires auth)
curl -H "Authorization: Bearer <token>" \
     http://localhost:8009/recommendations/mood/status
```

## 🚀 Roadmap

### Fase 1: MVP ✅ (Completado)
- [x] Detección simple de mood por género
- [x] Recomendación básica por compatibilidad
- [x] Toggle UI en frontend
- [x] Endpoints básicos

### Fase 2: Análisis Avanzado (Siguiente)
- [ ] Integración con Spotify API para features de audio
- [ ] Análisis de tempo, energy, valence reales
- [ ] Modelo ML de clasificación
- [ ] Feedback implícito (skips, likes)

### Fase 3: Inteligencia Predictiva (Futuro)
- [ ] Predicción de mood por contexto (hora, día)
- [ ] Recomendaciones proactivas
- [ ] Playlists automáticas por mood
- [ ] Dashboard de análisis de moods

## 🤝 Contribuciones

Para agregar nuevos moods o mejorar el algoritmo:

1. Editar `GENRE_TO_MOOD` en `mood_detection_service.py`
2. Actualizar `MOOD_COMPATIBILITY` con distancias
3. Ejecutar migraciones si es necesario
4. Actualizar constantes en frontend (`MoodAIToggle.jsx`)

## 📝 Notas Técnicas

- **Performance**: Cache de moods detectados para evitar re-cálculos
- **Escalabilidad**: Índices en `primary_mood`, `energy`, `valence`
- **Consistencia**: Transacciones para mantener integridad de sesiones
- **Fallback**: Si no hay candidatos, el algoritmo relaja restricciones gradualmente

## 📞 Soporte

Para issues o mejoras, contactar al equipo de desarrollo de VibeStream.

---

**Versión:** 1.0.0  
**Última actualización:** 2025-11-19
