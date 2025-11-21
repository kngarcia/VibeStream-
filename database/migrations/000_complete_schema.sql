-- ============================================
-- VIBESTREAM - COMPLETE DATABASE SCHEMA
-- PostgreSQL + Supabase Optimized
-- ============================================

-- Create schema if not exists
CREATE SCHEMA IF NOT EXISTS music_streaming;

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For full-text search

-- ============================================
-- 1. USERS & AUTH
-- ============================================

CREATE TABLE IF NOT EXISTS music_streaming.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('user', 'artist', 'admin')),
    birthdate DATE,
    profile_picture TEXT,
    bio TEXT,
    
    -- Audit fields
    registerdate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    last_username_change TIMESTAMP,
    last_email_change TIMESTAMP,
    last_password_change TIMESTAMP,
    
    -- Soft delete
    deleted_at TIMESTAMP,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_username ON music_streaming.users(username) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_email ON music_streaming.users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_role ON music_streaming.users(role);

-- ============================================
-- 2. GENRES (Catálogo de géneros musicales)
-- ============================================

CREATE TABLE IF NOT EXISTS music_streaming.genres (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    parent_genre_id INTEGER REFERENCES music_streaming.genres(id) ON DELETE SET NULL,
    icon_url TEXT,
    color_hex VARCHAR(7), -- Para UI (#FF5733)
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_genres_name ON music_streaming.genres(name);
CREATE INDEX idx_genres_parent ON music_streaming.genres(parent_genre_id);

-- ============================================
-- 3. ARTISTS
-- ============================================

CREATE TABLE IF NOT EXISTS music_streaming.artists (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES music_streaming.users(id) ON DELETE CASCADE,
    artist_name VARCHAR(100) UNIQUE NOT NULL,
    bio TEXT,
    profile_pic TEXT,
    banner_pic TEXT,
    social_links JSONB DEFAULT '{}'::jsonb, -- {spotify: url, instagram: url...}
    
    -- Stats (denormalized for performance)
    total_followers INTEGER DEFAULT 0,
    total_plays INTEGER DEFAULT 0,
    monthly_listeners INTEGER DEFAULT 0,
    
    -- Verification
    is_verified BOOLEAN DEFAULT false,
    verified_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE INDEX idx_artists_user ON music_streaming.artists(user_id);
CREATE INDEX idx_artists_name ON music_streaming.artists(artist_name);
CREATE INDEX idx_artists_verified ON music_streaming.artists(is_verified);

-- ============================================
-- 4. ALBUMS
-- ============================================

CREATE TABLE IF NOT EXISTS music_streaming.albums (
    id SERIAL PRIMARY KEY,
    artist_id INTEGER NOT NULL REFERENCES music_streaming.artists(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    album_type VARCHAR(20) DEFAULT 'album' CHECK (album_type IN ('album', 'single', 'ep', 'compilation')),
    release_date DATE,
    cover_url TEXT,
    total_tracks INTEGER DEFAULT 0,
    
    -- Stats
    total_plays INTEGER DEFAULT 0,
    total_likes INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE INDEX idx_albums_artist ON music_streaming.albums(artist_id);
CREATE INDEX idx_albums_release ON music_streaming.albums(release_date DESC);
CREATE INDEX idx_albums_type ON music_streaming.albums(album_type);

-- ============================================
-- 5. SONGS (TRACKS)
-- ============================================

CREATE TABLE IF NOT EXISTS music_streaming.songs (
    id SERIAL PRIMARY KEY,
    album_id INTEGER NOT NULL REFERENCES music_streaming.albums(id) ON DELETE CASCADE,
    genre_id INTEGER REFERENCES music_streaming.genres(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    duration INTEGER NOT NULL, -- segundos
    audio_url TEXT NOT NULL,
    track_number INTEGER,
    disc_number INTEGER DEFAULT 1,
    
    -- Audio metadata
    bitrate INTEGER, -- kbps
    sample_rate INTEGER, -- Hz
    file_size BIGINT, -- bytes
    file_format VARCHAR(10), -- mp3, flac, wav
    
    -- Lyrics
    lyrics TEXT,
    has_lyrics BOOLEAN DEFAULT false,
    
    -- Stats (denormalized)
    play_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    skip_count INTEGER DEFAULT 0,
    
    -- Flags
    is_explicit BOOLEAN DEFAULT false,
    is_available BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE INDEX idx_songs_album ON music_streaming.songs(album_id);
CREATE INDEX idx_songs_genre ON music_streaming.songs(genre_id);
CREATE INDEX idx_songs_title ON music_streaming.songs USING gin(to_tsvector('spanish', title));
CREATE INDEX idx_songs_play_count ON music_streaming.songs(play_count DESC);
CREATE INDEX idx_songs_available ON music_streaming.songs(is_available) WHERE deleted_at IS NULL;

-- ============================================
-- 6. SONG_ARTISTS (Many-to-Many)
-- ============================================

CREATE TABLE IF NOT EXISTS music_streaming.song_artists (
    song_id INTEGER REFERENCES music_streaming.songs(id) ON DELETE CASCADE,
    artist_id INTEGER REFERENCES music_streaming.artists(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'primary', -- primary, featured, producer, composer
    position INTEGER DEFAULT 1, -- orden de aparición
    
    PRIMARY KEY (song_id, artist_id, role),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_song_artists_song ON music_streaming.song_artists(song_id);
CREATE INDEX idx_song_artists_artist ON music_streaming.song_artists(artist_id);

-- ============================================
-- 7. PLAYLISTS
-- ============================================

CREATE TABLE IF NOT EXISTS music_streaming.playlists (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES music_streaming.users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    cover_image TEXT,
    
    -- Visibility
    is_public BOOLEAN DEFAULT false,
    is_collaborative BOOLEAN DEFAULT false,
    
    -- Stats
    total_songs INTEGER DEFAULT 0,
    total_duration INTEGER DEFAULT 0, -- segundos
    follower_count INTEGER DEFAULT 0,
    play_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE INDEX idx_playlists_user ON music_streaming.playlists(user_id);
CREATE INDEX idx_playlists_public ON music_streaming.playlists(is_public) WHERE deleted_at IS NULL;
CREATE INDEX idx_playlists_name ON music_streaming.playlists USING gin(to_tsvector('spanish', name));

-- ============================================
-- 8. PLAYLIST_SONGS (con orden)
-- ============================================

CREATE TABLE IF NOT EXISTS music_streaming.playlist_songs (
    playlist_id INTEGER REFERENCES music_streaming.playlists(id) ON DELETE CASCADE,
    song_id INTEGER REFERENCES music_streaming.songs(id) ON DELETE CASCADE,
    position INTEGER NOT NULL, -- orden en la playlist
    added_by INTEGER REFERENCES music_streaming.users(id) ON DELETE SET NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (playlist_id, song_id)
);

CREATE INDEX idx_playlist_songs_playlist ON music_streaming.playlist_songs(playlist_id, position);
CREATE INDEX idx_playlist_songs_song ON music_streaming.playlist_songs(song_id);

-- ============================================
-- 9. USER_LIKES (Favoritos)
-- ============================================

CREATE TABLE IF NOT EXISTS music_streaming.user_likes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES music_streaming.users(id) ON DELETE CASCADE,
    entity_type VARCHAR(20) NOT NULL CHECK (entity_type IN ('song', 'album', 'playlist', 'artist')),
    entity_id INTEGER NOT NULL,
    liked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, entity_type, entity_id)
);

CREATE INDEX idx_user_likes_user ON music_streaming.user_likes(user_id, entity_type);
CREATE INDEX idx_user_likes_entity ON music_streaming.user_likes(entity_type, entity_id);

-- ============================================
-- 10. PLAY_HISTORY (Historial de reproducción)
-- ============================================

CREATE TABLE IF NOT EXISTS music_streaming.play_history (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES music_streaming.users(id) ON DELETE CASCADE,
    song_id INTEGER NOT NULL REFERENCES music_streaming.songs(id) ON DELETE CASCADE,
    
    -- Context
    played_from VARCHAR(50), -- playlist, album, artist, search, mood_ai
    context_id INTEGER, -- id de la playlist/album si aplica
    
    -- Playback data
    played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_played INTEGER, -- segundos realmente reproducidos
    was_skipped BOOLEAN DEFAULT false,
    completion_percentage FLOAT, -- 0-100
    
    -- Device info
    device_type VARCHAR(50), -- web, mobile, desktop
    ip_address INET
);

-- Partitioning by month for performance (opcional pero recomendado)
CREATE INDEX idx_play_history_user_date ON music_streaming.play_history(user_id, played_at DESC);
CREATE INDEX idx_play_history_song ON music_streaming.play_history(song_id);
CREATE INDEX idx_play_history_recent ON music_streaming.play_history(played_at DESC) WHERE played_at > NOW() - INTERVAL '30 days';

-- ============================================
-- 11. USER_FOLLOWS (Seguir usuarios/artistas)
-- ============================================

CREATE TABLE IF NOT EXISTS music_streaming.user_follows (
    follower_id INTEGER NOT NULL REFERENCES music_streaming.users(id) ON DELETE CASCADE,
    following_id INTEGER NOT NULL REFERENCES music_streaming.users(id) ON DELETE CASCADE,
    followed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (follower_id, following_id),
    CHECK (follower_id != following_id)
);

CREATE INDEX idx_follows_follower ON music_streaming.user_follows(follower_id);
CREATE INDEX idx_follows_following ON music_streaming.user_follows(following_id);

-- ============================================
-- 12. ARTIST_SUBSCRIPTIONS (Ya existente, mejorado)
-- ============================================

CREATE TABLE IF NOT EXISTS music_streaming.artist_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES music_streaming.users(id) ON DELETE CASCADE,
    artist_id INTEGER NOT NULL REFERENCES music_streaming.artists(id) ON DELETE CASCADE,
    subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notification_enabled BOOLEAN DEFAULT true,
    
    UNIQUE(user_id, artist_id)
);

CREATE INDEX idx_artist_subs_user ON music_streaming.artist_subscriptions(user_id);
CREATE INDEX idx_artist_subs_artist ON music_streaming.artist_subscriptions(artist_id);

-- ============================================
-- 13. NOW_PLAYING (Reproducción actual)
-- ============================================

CREATE TABLE IF NOT EXISTS music_streaming.now_playing (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES music_streaming.users(id) ON DELETE CASCADE,
    song_id INTEGER NOT NULL REFERENCES music_streaming.songs(id) ON DELETE CASCADE,
    
    -- Playback state
    position INTEGER DEFAULT 0, -- segundos
    is_playing BOOLEAN DEFAULT true,
    volume INTEGER DEFAULT 100,
    repeat_mode VARCHAR(10) DEFAULT 'off' CHECK (repeat_mode IN ('off', 'one', 'all')),
    shuffle_enabled BOOLEAN DEFAULT false,
    
    -- Queue context
    queue_context VARCHAR(50), -- playlist, album, mood_ai
    queue_context_id INTEGER,
    
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_now_playing_user ON music_streaming.now_playing(user_id);

-- ============================================
-- 14. MOOD AI TABLES (Ya existentes, validadas)
-- ============================================

CREATE TABLE IF NOT EXISTS music_streaming.track_mood_features (
    id SERIAL PRIMARY KEY,
    song_id INTEGER NOT NULL UNIQUE REFERENCES music_streaming.songs(id) ON DELETE CASCADE,
    
    -- Mood classification
    primary_mood VARCHAR(50) NOT NULL,
    secondary_mood VARCHAR(50),
    
    -- Audio features
    tempo FLOAT,
    energy FLOAT,
    valence FLOAT,
    danceability FLOAT,
    acousticness FLOAT,
    instrumentalness FLOAT,
    loudness FLOAT,
    speechiness FLOAT,
    
    -- Metadata
    mood_tags JSONB DEFAULT '[]'::jsonb,
    mood_confidence FLOAT DEFAULT 0.7,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_mood_primary ON music_streaming.track_mood_features(primary_mood);
CREATE INDEX idx_mood_features ON music_streaming.track_mood_features(energy, valence);

CREATE TABLE IF NOT EXISTS music_streaming.user_mood_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES music_streaming.users(id) ON DELETE CASCADE,
    
    mood_ai_enabled BOOLEAN DEFAULT false,
    transition_smoothness VARCHAR(20) DEFAULT 'medium' CHECK (transition_smoothness IN ('low', 'medium', 'high')),
    
    last_toggle_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS music_streaming.mood_session_context (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES music_streaming.users(id) ON DELETE CASCADE,
    
    current_dominant_mood VARCHAR(50),
    recent_track_ids JSONB DEFAULT '[]'::jsonb,
    session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    playback_context_type VARCHAR(50),
    context_id INTEGER,
    
    is_active BOOLEAN DEFAULT true
);

CREATE INDEX idx_mood_session_user ON music_streaming.mood_session_context(user_id, is_active);

-- ============================================
-- 15. SEARCH_HISTORY
-- ============================================

CREATE TABLE IF NOT EXISTS music_streaming.search_history (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES music_streaming.users(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    result_count INTEGER DEFAULT 0,
    searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_search_user ON music_streaming.search_history(user_id, searched_at DESC);
CREATE INDEX idx_search_query ON music_streaming.search_history USING gin(to_tsvector('spanish', query));

-- ============================================
-- 16. ANALYTICS (Tabla agregada para reportes)
-- ============================================

CREATE TABLE IF NOT EXISTS music_streaming.daily_song_stats (
    id BIGSERIAL PRIMARY KEY,
    song_id INTEGER NOT NULL REFERENCES music_streaming.songs(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    
    total_plays INTEGER DEFAULT 0,
    total_skips INTEGER DEFAULT 0,
    total_likes INTEGER DEFAULT 0,
    unique_listeners INTEGER DEFAULT 0,
    total_duration_played BIGINT DEFAULT 0, -- segundos
    
    avg_completion_rate FLOAT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(song_id, date)
);

CREATE INDEX idx_daily_stats_song ON music_streaming.daily_song_stats(song_id, date DESC);
CREATE INDEX idx_daily_stats_date ON music_streaming.daily_song_stats(date DESC);

-- ============================================
-- TRIGGERS FOR AUTO-UPDATE timestamps
-- ============================================

CREATE OR REPLACE FUNCTION music_streaming.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables with updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON music_streaming.users
    FOR EACH ROW EXECUTE FUNCTION music_streaming.update_updated_at_column();

CREATE TRIGGER update_artists_updated_at BEFORE UPDATE ON music_streaming.artists
    FOR EACH ROW EXECUTE FUNCTION music_streaming.update_updated_at_column();

CREATE TRIGGER update_albums_updated_at BEFORE UPDATE ON music_streaming.albums
    FOR EACH ROW EXECUTE FUNCTION music_streaming.update_updated_at_column();

CREATE TRIGGER update_songs_updated_at BEFORE UPDATE ON music_streaming.songs
    FOR EACH ROW EXECUTE FUNCTION music_streaming.update_updated_at_column();

CREATE TRIGGER update_playlists_updated_at BEFORE UPDATE ON music_streaming.playlists
    FOR EACH ROW EXECUTE FUNCTION music_streaming.update_updated_at_column();

CREATE TRIGGER update_mood_features_updated_at BEFORE UPDATE ON music_streaming.track_mood_features
    FOR EACH ROW EXECUTE FUNCTION music_streaming.update_updated_at_column();

-- ============================================
-- VIEWS FOR COMMON QUERIES
-- ============================================

-- Vista: Canciones con toda su metadata
CREATE OR REPLACE VIEW music_streaming.v_songs_full AS
SELECT 
    s.id,
    s.title,
    s.duration,
    s.audio_url,
    s.track_number,
    s.play_count,
    s.like_count,
    s.is_explicit,
    
    a.id as album_id,
    a.title as album_title,
    a.cover_url as album_cover,
    a.release_date,
    
    g.id as genre_id,
    g.name as genre_name,
    
    array_agg(
        json_build_object(
            'id', art.id,
            'name', art.artist_name,
            'role', sa.role
        ) ORDER BY sa.position
    ) as artists,
    
    tmf.primary_mood,
    tmf.energy,
    tmf.valence
    
FROM music_streaming.songs s
JOIN music_streaming.albums a ON s.album_id = a.id
LEFT JOIN music_streaming.genres g ON s.genre_id = g.id
LEFT JOIN music_streaming.song_artists sa ON s.id = sa.song_id
LEFT JOIN music_streaming.artists art ON sa.artist_id = art.id
LEFT JOIN music_streaming.track_mood_features tmf ON s.id = tmf.song_id
WHERE s.deleted_at IS NULL
GROUP BY s.id, a.id, g.id, tmf.id;

-- Vista: Top canciones del día
CREATE OR REPLACE VIEW music_streaming.v_top_songs_today AS
SELECT 
    s.*,
    COUNT(ph.id) as plays_today
FROM music_streaming.songs s
JOIN music_streaming.play_history ph ON s.id = ph.song_id
WHERE ph.played_at >= CURRENT_DATE
GROUP BY s.id
ORDER BY plays_today DESC
LIMIT 100;

COMMENT ON SCHEMA music_streaming IS 'Schema principal para VibeStream - Aplicación de música streaming';
