# 🎵 VIBESTREAM - DATABASE SETUP & POPULATION GUIDE

## 📋 Tabla de Contenidos
1. [Arquitectura de Base de Datos](#arquitectura)
2. [Instalación del Schema](#instalación)
3. [Población con Datos Reales](#población)
4. [Consultas Optimizadas](#consultas)
5. [Mejores Prácticas](#mejores-prácticas)

---

## 🏗️ ARQUITECTURA DE BASE DE DATOS

### Motor y Stack
- **Motor**: PostgreSQL 14+ (Supabase)
- **Schema**: `music_streaming`
- **ORMs**: GORM (Go), SQLAlchemy (Python)
- **Extensiones**: pg_trgm (full-text search), uuid-ossp

### Tablas Principales (16 tablas)

```
┌─────────────┐
│   USERS     │ (1)
└──────┬──────┘
       │
       ├──────► ARTISTS (2)
       │           │
       │           ├──────► ALBUMS (4)
       │           │           │
       │           │           └──────► SONGS (5)
       │           │                      │
       │           └───────────────────────┘
       │                    (song_artists - N:M)
       │
       ├──────► PLAYLISTS (7)
       │           │
       │           └──────► PLAYLIST_SONGS (8)
       │                      
       ├──────► USER_LIKES (9)
       ├──────► PLAY_HISTORY (10)
       ├──────► USER_FOLLOWS (11)
       ├──────► ARTIST_SUBSCRIPTIONS (12)
       ├──────► NOW_PLAYING (13)
       ├──────► USER_MOOD_SETTINGS (14b)
       └──────► SEARCH_HISTORY (15)

GENRES (3) ──────► SONGS (5)

TRACK_MOOD_FEATURES (14a) ──────► SONGS (5)

MOOD_SESSION_CONTEXT (14c) ──────► USERS (1)

DAILY_SONG_STATS (16) ──────► SONGS (5)
```

### Mejoras Implementadas vs. Schema Anterior

| Característica | Antes | Ahora | Beneficio |
|----------------|-------|-------|-----------|
| **Likes/Favoritos** | ❌ No existía | ✅ `user_likes` | Usuarios pueden marcar favoritos |
| **Historial Persistido** | ⚠️ Solo Redis | ✅ `play_history` | Analytics y recomendaciones |
| **Tabla Géneros** | ⚠️ Parcial | ✅ `genres` completa | Clasificación consistente |
| **Follow System** | ❌ No existía | ✅ `user_follows` | Red social entre usuarios |
| **Playlists Públicas** | ❌ No | ✅ `is_public` flag | Compartir playlists |
| **Now Playing** | ❌ No | ✅ `now_playing` | Estado de reproducción |
| **Analytics** | ❌ No | ✅ `daily_song_stats` | Métricas y reportes |
| **Soft Deletes** | ❌ No | ✅ `deleted_at` | Recuperación de datos |
| **Full-text Search** | ⚠️ Básico | ✅ Índices GIN | Búsqueda rápida |
| **Triggers** | ❌ No | ✅ Auto-update timestamps | Consistencia automática |

---

## 🚀 INSTALACIÓN DEL SCHEMA

### Paso 1: Ejecutar Migración Completa

```bash
# Opción 1: Con psql (desde tu máquina)
psql "postgresql://postgres.nxbdcbqqkqeweosfefqj:bDHNtUlpLEPHFBFe@aws-1-us-east-2.pooler.supabase.com:5432/postgres" -f database/migrations/000_complete_schema.sql

# Opción 2: Desde Supabase Dashboard
# 1. Ve a: https://supabase.com/dashboard/project/_/sql
# 2. Copia y pega el contenido de 000_complete_schema.sql
# 3. Click "Run"
```

### Paso 2: Verificar Instalación

```sql
-- Verificar que se crearon las tablas
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'music_streaming'
ORDER BY table_name;

-- Debería mostrar 16+ tablas
```

---

## 📦 POBLACIÓN CON DATOS REALES (SPOTIFY API)

### Prerequisitos

1. **Obtener Credenciales de Spotify**
   
   a) Ve a: https://developer.spotify.com/dashboard
   
   b) Click en "Create an App"
   
   c) Completa el formulario:
      - **App name**: VibeStream Development
      - **App description**: Music streaming app for learning
      - **Redirect URIs**: http://localhost:3000/callback
      - Acepta los términos
   
   d) Copia tus credenciales:
      ```
      Client ID: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
      Client Secret: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
      ```

2. **Configurar Variables de Entorno**

   Agrega al archivo `.env` en la raíz del proyecto:

   ```env
   # Spotify API Credentials
   SPOTIFY_CLIENT_ID=tu_client_id_aqui
   SPOTIFY_CLIENT_SECRET=tu_client_secret_aqui
   ```

3. **Instalar Dependencias Python**

   ```bash
   pip install psycopg2-binary requests python-dotenv
   ```

### Ejecutar Script de Población

```bash
cd database/scripts
python populate_spotify.py
```

**Salida esperada:**
```
🎵 VibeStream Database Population Script
==================================================

✅ Conectado a Spotify API y Base de Datos

📂 Insertando géneros...
   ✓ 10 géneros insertados

👥 Poblando 10 artistas...

   🎤 Procesando: Bad Bunny
      ✓ Artista insertado (ID: 1)
      📀 Procesando 5 álbumes...
         ✓ Álbum: Un Verano Sin Ti
      ✓ Bad Bunny completado
   
   🎤 Procesando: Taylor Swift
      ✓ Artista insertado (ID: 2)
      ...

==================================================
✅ POBLADO COMPLETADO!

Estadísticas:
   - Artistas: 10
   - Álbumes: 25
   - Canciones: 180
   - Mood features: 180

👋 Conexión cerrada
```

### Personalizar Artistas

Edita el archivo `populate_spotify.py` línea 280:

```python
artists_to_fetch = [
    'Bad Bunny',        # Cambia por tus artistas favoritos
    'Taylor Swift',
    'The Weeknd',
    # Agrega más...
]
```

---

## 🔍 CONSULTAS OPTIMIZADAS

### 1. Obtener Canciones de una Playlist (con metadata)

```sql
SELECT 
    s.id,
    s.title,
    s.duration,
    s.audio_url,
    a.title as album_title,
    a.cover_url as album_cover,
    string_agg(ar.artist_name, ', ') as artists
FROM music_streaming.playlist_songs ps
JOIN music_streaming.songs s ON ps.song_id = s.id
JOIN music_streaming.albums a ON s.album_id = a.id
JOIN music_streaming.song_artists sa ON s.id = sa.song_id
JOIN music_streaming.artists ar ON sa.artist_id = ar.id
WHERE ps.playlist_id = 1
  AND s.deleted_at IS NULL
GROUP BY s.id, a.id
ORDER BY ps.position;
```

### 2. Top 50 Canciones Más Reproducidas (últimos 30 días)

```sql
SELECT 
    s.id,
    s.title,
    a.title as album,
    ar.artist_name,
    COUNT(ph.id) as plays,
    COUNT(DISTINCT ph.user_id) as unique_listeners
FROM music_streaming.play_history ph
JOIN music_streaming.songs s ON ph.song_id = s.id
JOIN music_streaming.albums a ON s.album_id = a.id
JOIN music_streaming.song_artists sa ON s.id = sa.song_id
JOIN music_streaming.artists ar ON sa.artist_id = ar.id
WHERE ph.played_at > NOW() - INTERVAL '30 days'
  AND s.deleted_at IS NULL
GROUP BY s.id, a.title, ar.artist_name
ORDER BY plays DESC
LIMIT 50;
```

### 3. Recomendaciones por Mood (para Mood AI)

```sql
SELECT 
    s.id,
    s.title,
    s.audio_url,
    tmf.primary_mood,
    tmf.energy,
    tmf.valence,
    a.cover_url
FROM music_streaming.songs s
JOIN music_streaming.track_mood_features tmf ON s.id = tmf.song_id
JOIN music_streaming.albums a ON s.album_id = a.id
WHERE tmf.primary_mood = 'happy'
  AND tmf.energy BETWEEN 0.6 AND 0.9
  AND tmf.valence > 0.6
  AND s.deleted_at IS NULL
ORDER BY RANDOM()
LIMIT 20;
```

### 4. Historial de un Usuario (últimas 50 canciones)

```sql
SELECT 
    s.title,
    ar.artist_name,
    a.cover_url,
    ph.played_at,
    ph.played_from as context
FROM music_streaming.play_history ph
JOIN music_streaming.songs s ON ph.song_id = s.id
JOIN music_streaming.albums a ON s.album_id = a.id
JOIN music_streaming.song_artists sa ON s.id = sa.song_id
JOIN music_streaming.artists ar ON sa.artist_id = ar.id
WHERE ph.user_id = 1
ORDER BY ph.played_at DESC
LIMIT 50;
```

### 5. Canciones Favoritas de un Usuario

```sql
SELECT 
    s.id,
    s.title,
    s.audio_url,
    a.title as album,
    a.cover_url,
    ar.artist_name,
    ul.liked_at
FROM music_streaming.user_likes ul
JOIN music_streaming.songs s ON ul.entity_id = s.id
JOIN music_streaming.albums a ON s.album_id = a.id
JOIN music_streaming.song_artists sa ON s.id = sa.song_id
JOIN music_streaming.artists ar ON sa.artist_id = ar.id
WHERE ul.user_id = 1
  AND ul.entity_type = 'song'
  AND s.deleted_at IS NULL
ORDER BY ul.liked_at DESC;
```

### 6. Búsqueda Full-Text (canciones y artistas)

```sql
-- Buscar "love" en canciones
SELECT 
    s.id,
    s.title,
    ar.artist_name,
    ts_rank(to_tsvector('spanish', s.title), query) as rank
FROM music_streaming.songs s
JOIN music_streaming.song_artists sa ON s.id = sa.song_id
JOIN music_streaming.artists ar ON sa.artist_id = ar.id,
     to_tsquery('spanish', 'love') query
WHERE to_tsvector('spanish', s.title) @@ query
  AND s.deleted_at IS NULL
ORDER BY rank DESC
LIMIT 20;
```

---

## 🎯 MEJORES PRÁCTICAS

### 1. Índices Críticos (ya implementados)

```sql
-- NUNCA eliminar estos índices
CREATE INDEX idx_songs_play_count ON music_streaming.songs(play_count DESC);
CREATE INDEX idx_play_history_user_date ON music_streaming.play_history(user_id, played_at DESC);
CREATE INDEX idx_user_likes_user ON music_streaming.user_likes(user_id, entity_type);
```

### 2. Actualizar Contadores de Forma Eficiente

```sql
-- ❌ MAL: N+1 queries
UPDATE music_streaming.songs SET play_count = play_count + 1 WHERE id = 1;
UPDATE music_streaming.songs SET play_count = play_count + 1 WHERE id = 2;
-- ...

-- ✅ BIEN: Batch update
UPDATE music_streaming.songs 
SET play_count = play_count + counts.plays
FROM (
    VALUES (1, 1), (2, 1), (3, 2)
) AS counts(song_id, plays)
WHERE songs.id = counts.song_id;
```

### 3. Usar Transacciones para Operaciones Complejas

```python
# Python + SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)

def add_song_to_playlist(playlist_id, song_id, user_id):
    session = Session()
    try:
        # 1. Obtener última posición
        last_pos = session.execute(
            "SELECT COALESCE(MAX(position), 0) FROM music_streaming.playlist_songs WHERE playlist_id = :pid",
            {"pid": playlist_id}
        ).scalar()
        
        # 2. Insertar canción
        session.execute(
            """INSERT INTO music_streaming.playlist_songs 
               (playlist_id, song_id, position, added_by)
               VALUES (:pid, :sid, :pos, :uid)""",
            {"pid": playlist_id, "sid": song_id, "pos": last_pos + 1, "uid": user_id}
        )
        
        # 3. Actualizar contador de playlist
        session.execute(
            "UPDATE music_streaming.playlists SET total_songs = total_songs + 1 WHERE id = :pid",
            {"pid": playlist_id}
        )
        
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
```

### 4. Estrategia de Caching (Redis)

```python
# Cachear consultas pesadas por 5 minutos
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_top_songs_cached():
    cache_key = "top_songs:30days"
    
    # Intentar obtener de cache
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Si no está en cache, consultar BD
    result = db.execute("""
        SELECT s.id, s.title, COUNT(*) as plays
        FROM music_streaming.play_history ph
        JOIN music_streaming.songs s ON ph.song_id = s.id
        WHERE ph.played_at > NOW() - INTERVAL '30 days'
        GROUP BY s.id
        ORDER BY plays DESC
        LIMIT 50
    """).fetchall()
    
    # Guardar en cache por 5 minutos
    redis_client.setex(cache_key, 300, json.dumps(result))
    return result
```

### 5. Monitoreo de Consultas Lentas

```sql
-- Habilitar logging de queries lentas (> 100ms)
ALTER DATABASE postgres SET log_min_duration_statement = 100;

-- Ver queries lentas recientes
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    max_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 20;
```

### 6. Particionamiento (Para alta escala)

```sql
-- Si play_history crece mucho (> 100M registros), particionar por mes
CREATE TABLE music_streaming.play_history_2025_01 PARTITION OF music_streaming.play_history
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE music_streaming.play_history_2025_02 PARTITION OF music_streaming.play_history
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
```

### 7. Backup Automático

```bash
# Agregar a crontab: backup diario a las 3 AM
0 3 * * * pg_dump -h aws-1-us-east-2.pooler.supabase.com \
  -U postgres.nxbdcbqqkqeweosfefqj \
  -d postgres \
  -n music_streaming \
  -F c -f /backups/vibestream_$(date +\%Y\%m\%d).dump
```

---

## 🧪 TESTING

### Script de Prueba de Integridad

```python
def test_database_integrity():
    """Verifica integridad referencial"""
    tests = [
        # No debe haber canciones sin álbum
        "SELECT COUNT(*) FROM music_streaming.songs s LEFT JOIN music_streaming.albums a ON s.album_id = a.id WHERE a.id IS NULL",
        
        # No debe haber álbumes sin artista
        "SELECT COUNT(*) FROM music_streaming.albums al LEFT JOIN music_streaming.artists ar ON al.artist_id = ar.id WHERE ar.id IS NULL",
        
        # Todas las canciones deben tener al menos un artista
        "SELECT COUNT(*) FROM music_streaming.songs s LEFT JOIN music_streaming.song_artists sa ON s.id = sa.song_id WHERE sa.song_id IS NULL",
    ]
    
    for i, query in enumerate(tests, 1):
        result = db.execute(query).scalar()
        assert result == 0, f"Test {i} failed: {result} inconsistencies found"
    
    print("✅ All integrity tests passed!")
```

---

## 📊 OPTIMIZACIÓN DE RENDIMIENTO

### Consultas Más Comunes a Optimizar

1. **Home Feed** → Cache 1 min
2. **Top Charts** → Cache 5 min
3. **Artist Profile** → Cache 10 min
4. **Search Results** → Cache 30 seg
5. **User Playlists** → No cachear (datos en tiempo real)

### Índices de Mantenimiento

```sql
-- Ejecutar mensualmente para mantener índices optimizados
REINDEX SCHEMA music_streaming;
VACUUM ANALYZE music_streaming.songs;
VACUUM ANALYZE music_streaming.play_history;
```

---

## 🚨 TROUBLESHOOTING

### Problema: Queries lentas en búsqueda

**Solución**: Verificar que extensión pg_trgm esté activa
```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
REINDEX INDEX idx_songs_title;
```

### Problema: Play_history crece demasiado

**Solución**: Archivar registros antiguos
```sql
-- Mover datos > 1 año a tabla de archivo
CREATE TABLE music_streaming.play_history_archive AS
SELECT * FROM music_streaming.play_history
WHERE played_at < NOW() - INTERVAL '1 year';

DELETE FROM music_streaming.play_history
WHERE played_at < NOW() - INTERVAL '1 year';
```

---

## 📚 RECURSOS ADICIONALES

- [PostgreSQL Performance Tips](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Spotify Web API Docs](https://developer.spotify.com/documentation/web-api)
- [SQLAlchemy Best Practices](https://docs.sqlalchemy.org/en/20/orm/queryguide/index.html)
- [GORM Documentation](https://gorm.io/docs/)

---

**🎵 VibeStream Database Team**
Última actualización: Noviembre 2025
