from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from database.models import TrackMoodFeatures


class MoodDetectionService:
    """
    Servicio de detección de mood de canciones.
    Fase 1: Clasificación basada en género y metadata.
    Fase 2: Integración con análisis de audio.
    """
    
    # Mapeo simple de géneros a moods
    GENRE_TO_MOOD = {
        'lofi': 'chill',
        'lo-fi': 'chill',
        'chill': 'chill',
        'chillout': 'chill',
        'ambient': 'chill',
        'classical': 'chill',
        'acoustic': 'chill',
        'jazz': 'chill',
        'smooth jazz': 'chill',
        'bossa nova': 'chill',
        
        'rock': 'energetic',
        'metal': 'intense',
        'heavy metal': 'intense',
        'punk': 'intense',
        'hardcore': 'intense',
        'thrash': 'intense',
        'death metal': 'intense',
        
        'pop': 'happy',
        'dance': 'happy',
        'electronic': 'energetic',
        'house': 'energetic',
        'techno': 'energetic',
        'edm': 'energetic',
        'electro': 'energetic',
        'drum and bass': 'energetic',
        'dubstep': 'energetic',
        
        'blues': 'sad',
        'soul': 'melancholic',
        'indie': 'melancholic',
        'folk': 'melancholic',
        'alternative': 'melancholic',
        
        'hip-hop': 'energetic',
        'hip hop': 'energetic',
        'rap': 'energetic',
        'trap': 'intense',
        'r&b': 'chill',
        'rnb': 'chill',
        
        'reggae': 'chill',
        'reggaeton': 'happy',
        'latin': 'happy',
        'salsa': 'happy',
        'bachata': 'melancholic',
        
        'country': 'happy',
        'gospel': 'happy',
        'disco': 'happy',
        'funk': 'happy',
    }
    
    # Definición de "distancia" entre moods (0 = compatible, 1 = muy diferente)
    MOOD_COMPATIBILITY = {
        'chill': {'chill': 0.0, 'happy': 0.3, 'sad': 0.4, 'energetic': 0.7, 'intense': 1.0, 'melancholic': 0.5},
        'happy': {'chill': 0.3, 'happy': 0.0, 'sad': 0.8, 'energetic': 0.2, 'intense': 0.6, 'melancholic': 0.7},
        'sad': {'chill': 0.4, 'happy': 0.8, 'sad': 0.0, 'energetic': 0.9, 'intense': 1.0, 'melancholic': 0.2},
        'energetic': {'chill': 0.7, 'happy': 0.2, 'sad': 0.9, 'energetic': 0.0, 'intense': 0.3, 'melancholic': 0.8},
        'intense': {'chill': 1.0, 'happy': 0.6, 'sad': 1.0, 'energetic': 0.3, 'intense': 0.0, 'melancholic': 0.9},
        'melancholic': {'chill': 0.5, 'happy': 0.7, 'sad': 0.2, 'energetic': 0.8, 'intense': 0.9, 'melancholic': 0.0},
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def detect_mood_for_track(self, song_id: int) -> Optional[str]:
        """Detecta el mood de una canción basándose en su género"""
        # Buscar si ya tiene mood calculado
        result = await self.db.execute(
            select(TrackMoodFeatures).where(TrackMoodFeatures.song_id == song_id)
        )
        existing_mood = result.scalar_one_or_none()
        
        if existing_mood:
            return existing_mood.primary_mood
        
        # Si no existe, calcularlo desde el género
        query = text("""
            SELECT s.id, s.title, g.name as genre_name
            FROM music_streaming.songs s
            LEFT JOIN music_streaming.genres g ON s.genre_id = g.id
            WHERE s.id = :song_id
        """)
        
        result = await self.db.execute(query, {"song_id": song_id})
        song_data = result.fetchone()
        
        if not song_data:
            return 'happy'  # Mood por defecto
        
        genre_name = song_data.genre_name if song_data.genre_name else 'unknown'
        genre_name_lower = genre_name.lower()
        
        # Buscar en el mapeo
        detected_mood = 'happy'  # Default
        for genre_key, mood in self.GENRE_TO_MOOD.items():
            if genre_key in genre_name_lower:
                detected_mood = mood
                break
        
        # Guardar en BD
        await self._save_mood(song_id, detected_mood)
        
        return detected_mood
    
    async def _save_mood(self, song_id: int, mood: str):
        """Guarda el mood detectado en la BD"""
        mood_feature = TrackMoodFeatures(
            song_id=song_id,
            primary_mood=mood,
            mood_confidence=0.7,  # Confianza media en fase 1
            mood_tags=[mood],
            energy=0.5,
            valence=0.5,
            tempo=120.0
        )
        self.db.add(mood_feature)
        await self.db.commit()
    
    def calculate_mood_distance(self, mood1: str, mood2: str) -> float:
        """Calcula la distancia entre dos moods"""
        if mood1 not in self.MOOD_COMPATIBILITY or mood2 not in self.MOOD_COMPATIBILITY[mood1]:
            return 0.5  # Distancia media si no está definido
        
        return self.MOOD_COMPATIBILITY[mood1][mood2]
    
    def are_moods_compatible(self, mood1: str, mood2: str, smoothness: str = 'medium') -> bool:
        """Determina si dos moods son compatibles según el nivel de suavidad"""
        distance = self.calculate_mood_distance(mood1, mood2)
        
        thresholds = {
            'strict': 0.3,    # Solo moods muy similares
            'medium': 0.6,    # Transiciones suaves
            'flexible': 0.9   # Casi cualquier transición
        }
        
        threshold = thresholds.get(smoothness, 0.6)
        return distance <= threshold
