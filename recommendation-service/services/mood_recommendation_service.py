from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from database.models import UserMoodSettings, MoodSessionContext
from services.mood_detection_service import MoodDetectionService
import random
from datetime import datetime


class MoodRecommendationService:
    """Servicio de recomendación basada en mood"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.mood_detector = MoodDetectionService(db)
    
    async def get_dominant_mood(self, user_id: int, recent_track_ids: List[int]) -> str:
        """Determina el mood dominante basado en las últimas canciones escuchadas"""
        if not recent_track_ids:
            return 'happy'  # Default
        
        # Obtener moods de las últimas 5 canciones
        moods = []
        for track_id in recent_track_ids[-5:]:
            mood = await self.mood_detector.detect_mood_for_track(track_id)
            if mood:
                moods.append(mood)
        
        if not moods:
            return 'happy'
        
        # Mood más frecuente
        from collections import Counter
        mood_counter = Counter(moods)
        dominant_mood = mood_counter.most_common(1)[0][0]
        
        return dominant_mood
    
    async def get_next_track_mood_based(
        self,
        user_id: int,
        context_type: str,  # 'playlist', 'liked', 'explore'
        context_id: Optional[int] = None
    ) -> Optional[Dict]:
        """Obtiene la siguiente canción respetando el mood"""
        
        # 1. Verificar si el modo está activado
        settings_result = await self.db.execute(
            select(UserMoodSettings).where(UserMoodSettings.user_id == user_id)
        )
        settings = settings_result.scalar_one_or_none()
        
        if not settings or not settings.mood_ai_enabled:
            # Modo desactivado: comportamiento normal
            return await self._get_next_track_normal(user_id, context_type, context_id)
        
        # 2. Obtener contexto de sesión
        session_result = await self.db.execute(
            select(MoodSessionContext)
            .where(MoodSessionContext.user_id == user_id)
            .where(MoodSessionContext.is_active == True)
            .order_by(MoodSessionContext.last_updated.desc())
            .limit(1)
        )
        session = session_result.scalar_one_or_none()
        
        recent_tracks = session.recent_track_ids if session and session.recent_track_ids else []
        
        # 3. Determinar mood dominante
        dominant_mood = await self.get_dominant_mood(user_id, recent_tracks)
        
        # 4. Obtener candidatos según contexto
        candidates = await self._get_candidate_tracks(user_id, context_type, context_id, recent_tracks)
        
        if not candidates:
            return None
        
        # 5. Filtrar por mood compatible
        compatible_tracks = []
        smoothness = settings.transition_smoothness
        
        for track in candidates:
            track_mood = await self.mood_detector.detect_mood_for_track(track['id'])
            if self.mood_detector.are_moods_compatible(dominant_mood, track_mood, smoothness):
                compatible_tracks.append({
                    **track,
                    'mood': track_mood,
                    'mood_distance': self.mood_detector.calculate_mood_distance(dominant_mood, track_mood)
                })
        
        if not compatible_tracks:
            # Si no hay compatibles, relajar restricciones
            compatible_tracks = [{
                **track,
                'mood': await self.mood_detector.detect_mood_for_track(track['id']),
                'mood_distance': 0.5
            } for track in candidates[:10]]
        
        # 6. Ordenar por distancia de mood (más cercano primero) con algo de aleatoriedad
        compatible_tracks.sort(key=lambda x: x['mood_distance'])
        
        # Seleccionar entre los top 3 aleatoriamente (para variedad)
        top_candidates = compatible_tracks[:min(3, len(compatible_tracks))]
        selected_track = random.choice(top_candidates)
        
        # 7. Actualizar contexto de sesión
        await self._update_session_context(user_id, selected_track['id'], dominant_mood, context_type, context_id)
        
        return selected_track
    
    async def _get_candidate_tracks(
        self,
        user_id: int,
        context_type: str,
        context_id: Optional[int],
        exclude_ids: List[int] = None
    ) -> List[Dict]:
        """Obtiene canciones candidatas según el contexto"""
        
        exclude_ids = exclude_ids or []
        exclude_clause = ""
        if exclude_ids:
            exclude_str = ",".join(str(id) for id in exclude_ids)
            exclude_clause = f"AND s.id NOT IN ({exclude_str})"
        
        if context_type == 'playlist' and context_id:
            # Canciones de una playlist específica
            query = text(f"""
                SELECT s.id, s.title, s.artist_name, s.duration, s.cover_url
                FROM music_streaming.songs s
                INNER JOIN music_streaming.playlist_songs ps ON ps.song_id = s.id
                WHERE ps.playlist_id = :context_id
                {exclude_clause}
                ORDER BY ps.position
                LIMIT 50
            """)
            result = await self.db.execute(query, {"context_id": context_id})
            
        elif context_type == 'liked':
            # Canciones marcadas como favoritas (asumir tabla user_likes)
            query = text(f"""
                SELECT s.id, s.title, s.artist_name, s.duration, s.cover_url
                FROM music_streaming.songs s
                WHERE s.id > 0
                {exclude_clause}
                ORDER BY RANDOM()
                LIMIT 100
            """)
            result = await self.db.execute(query)
            
        elif context_type == 'explore':
            # Modo exploración: canciones aleatorias populares
            query = text(f"""
                SELECT s.id, s.title, s.artist_name, s.duration, s.cover_url
                FROM music_streaming.songs s
                WHERE s.id > 0
                {exclude_clause}
                ORDER BY RANDOM()
                LIMIT 100
            """)
            result = await self.db.execute(query)
            
        else:
            # Fallback: canciones aleatorias
            query = text(f"""
                SELECT s.id, s.title, s.artist_name, s.duration, s.cover_url
                FROM music_streaming.songs s
                WHERE s.id > 0
                {exclude_clause}
                ORDER BY RANDOM()
                LIMIT 50
            """)
            result = await self.db.execute(query)
        
        # Convertir a diccionarios
        rows = result.fetchall()
        return [
            {
                'id': row.id,
                'title': row.title,
                'artist_name': row.artist_name or 'Unknown',
                'duration': row.duration,
                'cover_url': row.cover_url if hasattr(row, 'cover_url') else None
            }
            for row in rows
        ]
    
    async def _get_next_track_normal(
        self, 
        user_id: int, 
        context_type: str, 
        context_id: Optional[int]
    ) -> Optional[Dict]:
        """Obtiene siguiente canción sin filtro de mood"""
        candidates = await self._get_candidate_tracks(user_id, context_type, context_id)
        if not candidates:
            return None
        return random.choice(candidates)
    
    async def _update_session_context(
        self,
        user_id: int,
        track_id: int,
        dominant_mood: str,
        context_type: str,
        context_id: Optional[int]
    ):
        """Actualiza el contexto de la sesión de reproducción"""
        
        # Buscar sesión existente activa
        result = await self.db.execute(
            select(MoodSessionContext)
            .where(MoodSessionContext.user_id == user_id)
            .where(MoodSessionContext.is_active == True)
            .order_by(MoodSessionContext.last_updated.desc())
            .limit(1)
        )
        session = result.scalar_one_or_none()
        
        recent_tracks = session.recent_track_ids if session and session.recent_track_ids else []
        recent_tracks.append(track_id)
        
        # Mantener solo las últimas 10
        recent_tracks = recent_tracks[-10:]
        
        if session:
            # Actualizar existente
            session.current_dominant_mood = dominant_mood
            session.recent_track_ids = recent_tracks
            session.last_updated = datetime.utcnow()
            session.playback_context_type = context_type
            session.context_id = context_id
        else:
            # Crear nueva
            session = MoodSessionContext(
                user_id=user_id,
                current_dominant_mood=dominant_mood,
                recent_track_ids=recent_tracks,
                playback_context_type=context_type,
                context_id=context_id,
                is_active=True
            )
            self.db.add(session)
        
        await self.db.commit()
    
    async def handle_skip(self, user_id: int, skipped_track_id: int):
        """Registra un skip y ajusta el mood dominante"""
        # Buscar sesión activa
        result = await self.db.execute(
            select(MoodSessionContext)
            .where(MoodSessionContext.user_id == user_id)
            .where(MoodSessionContext.is_active == True)
            .order_by(MoodSessionContext.last_updated.desc())
            .limit(1)
        )
        session = result.scalar_one_or_none()
        
        if session and session.recent_track_ids:
            # Remover de recent_tracks si existe
            if skipped_track_id in session.recent_track_ids:
                session.recent_track_ids.remove(skipped_track_id)
                
                # Recalcular mood dominante
                if session.recent_track_ids:
                    new_mood = await self.get_dominant_mood(user_id, session.recent_track_ids)
                    session.current_dominant_mood = new_mood
                    session.last_updated = datetime.utcnow()
                
                await self.db.commit()
