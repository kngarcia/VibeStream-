from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import get_db
from services.mood_recommendation_service import MoodRecommendationService
from services.mood_detection_service import MoodDetectionService
from database.models import UserMoodSettings, MoodSessionContext
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select

router = APIRouter()


# Schemas
class MoodToggleRequest(BaseModel):
    enabled: bool
    transition_smoothness: Optional[str] = 'medium'


class MoodToggleResponse(BaseModel):
    mood_ai_enabled: bool
    current_mood: Optional[str]
    transition_smoothness: str


class MoodStatusResponse(BaseModel):
    mood_ai_enabled: bool
    current_mood: Optional[str]
    transition_smoothness: str
    recent_moods: Optional[List[str]] = []


class NextTrackRequest(BaseModel):
    context_type: str  # 'playlist', 'liked', 'explore'
    context_id: Optional[int] = None


class NextTrackResponse(BaseModel):
    id: int
    title: str
    artist_name: str
    duration: int
    mood: str
    mood_distance: float


class SkipTrackRequest(BaseModel):
    track_id: int


def get_user_id(request: Request) -> int:
    """Extrae user_id del estado del request (inyectado por auth middleware)"""
    if not hasattr(request.state, "user") or not request.state.user:
        raise HTTPException(status_code=401, detail="No autenticado")
    return request.state.user.get("user_id")


# Endpoints
@router.post("/mood/toggle", response_model=MoodToggleResponse)
async def toggle_mood_ai(
    request_data: MoodToggleRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Activa o desactiva el Modo Mood AI"""
    user_id = get_user_id(request)
    
    # Buscar configuración existente
    result = await db.execute(
        select(UserMoodSettings).where(UserMoodSettings.user_id == user_id)
    )
    settings = result.scalar_one_or_none()
    
    if settings:
        settings.mood_ai_enabled = request_data.enabled
        settings.transition_smoothness = request_data.transition_smoothness
        settings.last_toggle_at = datetime.utcnow()
    else:
        settings = UserMoodSettings(
            user_id=user_id,
            mood_ai_enabled=request_data.enabled,
            transition_smoothness=request_data.transition_smoothness
        )
        db.add(settings)
    
    await db.commit()
    
    # Obtener mood actual si está habilitado
    current_mood = None
    if request_data.enabled:
        mood_service = MoodRecommendationService(db)
        
        # Obtener sesión actual
        session_result = await db.execute(
            select(MoodSessionContext)
            .where(MoodSessionContext.user_id == user_id)
            .where(MoodSessionContext.is_active == True)
            .order_by(MoodSessionContext.last_updated.desc())
            .limit(1)
        )
        session = session_result.scalar_one_or_none()
        
        if session and session.recent_track_ids:
            current_mood = await mood_service.get_dominant_mood(
                user_id, 
                session.recent_track_ids
            )
    
    return MoodToggleResponse(
        mood_ai_enabled=request_data.enabled,
        current_mood=current_mood,
        transition_smoothness=request_data.transition_smoothness
    )


@router.get("/mood/status", response_model=MoodStatusResponse)
async def get_mood_status(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Obtiene el estado actual del Modo Mood AI"""
    user_id = get_user_id(request)
    
    # Configuración
    result = await db.execute(
        select(UserMoodSettings).where(UserMoodSettings.user_id == user_id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        return MoodStatusResponse(
            mood_ai_enabled=False,
            current_mood=None,
            transition_smoothness='medium',
            recent_moods=[]
        )
    
    # Mood actual
    current_mood = None
    recent_moods = []
    
    if settings.mood_ai_enabled:
        mood_service = MoodRecommendationService(db)
        mood_detector = MoodDetectionService(db)
        
        # Sesión actual
        session_result = await db.execute(
            select(MoodSessionContext)
            .where(MoodSessionContext.user_id == user_id)
            .where(MoodSessionContext.is_active == True)
            .order_by(MoodSessionContext.last_updated.desc())
            .limit(1)
        )
        session = session_result.scalar_one_or_none()
        
        if session and session.recent_track_ids:
            current_mood = await mood_service.get_dominant_mood(
                user_id, 
                session.recent_track_ids
            )
            
            # Obtener moods recientes
            for track_id in session.recent_track_ids[-5:]:
                mood = await mood_detector.detect_mood_for_track(track_id)
                recent_moods.append(mood)
    
    return MoodStatusResponse(
        mood_ai_enabled=settings.mood_ai_enabled,
        current_mood=current_mood,
        transition_smoothness=settings.transition_smoothness,
        recent_moods=recent_moods
    )


@router.post("/mood/next-track", response_model=NextTrackResponse)
async def get_next_track_mood_based(
    request_data: NextTrackRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Obtiene la siguiente canción basada en el mood"""
    user_id = get_user_id(request)
    
    mood_service = MoodRecommendationService(db)
    
    track = await mood_service.get_next_track_mood_based(
        user_id=user_id,
        context_type=request_data.context_type,
        context_id=request_data.context_id
    )
    
    if not track:
        raise HTTPException(status_code=404, detail="No se encontraron canciones")
    
    return NextTrackResponse(**track)


@router.get("/mood/current")
async def get_current_mood(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Obtiene el mood actual de la sesión"""
    user_id = get_user_id(request)
    
    result = await db.execute(
        select(MoodSessionContext)
        .where(MoodSessionContext.user_id == user_id)
        .where(MoodSessionContext.is_active == True)
        .order_by(MoodSessionContext.last_updated.desc())
        .limit(1)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        return {"current_mood": None, "recent_tracks": []}
    
    mood_service = MoodRecommendationService(db)
    current_mood = await mood_service.get_dominant_mood(
        user_id, 
        session.recent_track_ids or []
    )
    
    return {
        "current_mood": current_mood,
        "recent_tracks": session.recent_track_ids,
        "context_type": session.playback_context_type
    }


@router.post("/mood/skip")
async def handle_track_skip(
    skip_data: SkipTrackRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Maneja el evento de skip de una canción"""
    user_id = get_user_id(request)
    
    mood_service = MoodRecommendationService(db)
    await mood_service.handle_skip(user_id, skip_data.track_id)
    
    return {"status": "ok", "message": "Skip registrado"}
