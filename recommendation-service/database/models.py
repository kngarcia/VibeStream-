from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, JSON, DateTime, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from database.connection import Base


class TrackMoodFeatures(Base):
    """Características de mood de una canción"""
    __tablename__ = "track_mood_features"
    __table_args__ = (
        Index('idx_primary_mood', 'primary_mood'),
        Index('idx_energy_valence', 'energy', 'valence'),
        {"schema": "music_streaming"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    song_id = Column(Integer, nullable=False, unique=True)
    
    # Mood principal (clasificación simple)
    primary_mood = Column(String(50), nullable=False)  # 'happy', 'sad', 'energetic', 'chill', 'lofi', 'intense', 'melancholic'
    secondary_mood = Column(String(50))
    
    # Features de audio (para análisis avanzado - Fase 2)
    tempo = Column(Float)  # BPM
    energy = Column(Float)  # 0.0 - 1.0
    valence = Column(Float)  # 0.0 (triste) - 1.0 (feliz)
    danceability = Column(Float)  # 0.0 - 1.0
    acousticness = Column(Float)  # 0.0 - 1.0
    instrumentalness = Column(Float)  # 0.0 - 1.0
    
    # Metadata adicional
    mood_tags = Column(JSON)  # ['relaxing', 'study', 'workout']
    mood_confidence = Column(Float, default=0.7)  # Confianza del modelo
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserMoodSettings(Base):
    """Configuración de Mood AI por usuario"""
    __tablename__ = "user_mood_settings"
    __table_args__ = {"schema": "music_streaming"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, unique=True)
    
    # Configuración del modo
    mood_ai_enabled = Column(Boolean, default=False)
    
    # Preferencias de transición
    transition_smoothness = Column(String(20), default='medium')  # 'strict', 'medium', 'flexible'
    
    # Últimas actualizaciones
    last_toggle_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MoodSessionContext(Base):
    """Contexto de sesión de reproducción con mood"""
    __tablename__ = "mood_session_context"
    __table_args__ = (
        Index('idx_mood_session_user', 'user_id', 'last_updated'),
        {"schema": "music_streaming"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    
    # Contexto actual de la sesión
    current_dominant_mood = Column(String(50))
    recent_track_ids = Column(JSON, default=list)  # Últimas 5-10 canciones
    session_start = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Contexto de reproducción
    playback_context_type = Column(String(50))  # 'playlist', 'liked', 'explore', 'album'
    context_id = Column(Integer)  # ID de la playlist/album si aplica
    
    # Estado
    is_active = Column(Boolean, default=True)
