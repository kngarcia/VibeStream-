-- Migration script for Mood AI feature
-- Run this script to create the necessary tables for the recommendation service

-- Create track_mood_features table
CREATE TABLE IF NOT EXISTS music_streaming.track_mood_features (
    id SERIAL PRIMARY KEY,
    song_id INTEGER NOT NULL UNIQUE,
    
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
    
    -- Metadata
    mood_tags JSONB,
    mood_confidence FLOAT DEFAULT 0.7,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_song_id FOREIGN KEY (song_id) 
        REFERENCES music_streaming.songs(id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_primary_mood ON music_streaming.track_mood_features(primary_mood);
CREATE INDEX IF NOT EXISTS idx_energy_valence ON music_streaming.track_mood_features(energy, valence);

-- Create user_mood_settings table
CREATE TABLE IF NOT EXISTS music_streaming.user_mood_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    
    -- Settings
    mood_ai_enabled BOOLEAN DEFAULT FALSE,
    transition_smoothness VARCHAR(20) DEFAULT 'medium',
    
    -- Timestamps
    last_toggle_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_user_id FOREIGN KEY (user_id) 
        REFERENCES music_streaming.users(id) ON DELETE CASCADE
);

-- Create mood_session_context table
CREATE TABLE IF NOT EXISTS music_streaming.mood_session_context (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    
    -- Session data
    current_dominant_mood VARCHAR(50),
    recent_track_ids JSONB DEFAULT '[]'::jsonb,
    session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Playback context
    playback_context_type VARCHAR(50),
    context_id INTEGER,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    CONSTRAINT fk_mood_session_user FOREIGN KEY (user_id) 
        REFERENCES music_streaming.users(id) ON DELETE CASCADE
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_mood_session_user ON music_streaming.mood_session_context(user_id, last_updated);
CREATE INDEX IF NOT EXISTS idx_mood_session_active ON music_streaming.mood_session_context(user_id, is_active);

-- Add comments for documentation
COMMENT ON TABLE music_streaming.track_mood_features IS 'Características de mood/estado de ánimo de las canciones';
COMMENT ON TABLE music_streaming.user_mood_settings IS 'Configuración del Modo Mood AI por usuario';
COMMENT ON TABLE music_streaming.mood_session_context IS 'Contexto de sesión de reproducción con mood activo';

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Mood AI tables created successfully!';
END $$;
