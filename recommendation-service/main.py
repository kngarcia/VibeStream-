from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from handlers.mood_handler import router as mood_router
from middleware.auth_middleware import AuthMiddleware
from config import settings
from database.connection import init_db
from contextlib import asynccontextmanager
import uvicorn
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle: inicializar BD al arrancar"""
    logger.info("🚀 Iniciando Recommendation Service...")
    try:
        await init_db()
        logger.info("✅ Base de datos inicializada")
    except Exception as e:
        logger.error(f"❌ Error inicializando BD: {e}")
    
    yield
    
    logger.info("🛑 Deteniendo Recommendation Service...")


app = FastAPI(
    title="Recommendation Service - Mood AI",
    version="1.0.0",
    description="Servicio de recomendación de música basado en mood/estado de ánimo",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth Middleware
app.add_middleware(AuthMiddleware)

# Routers
app.include_router(mood_router, prefix="/recommendations", tags=["Mood AI"])


# Health check
@app.get("/health")
def health_check():
    return {
        "status": "ok", 
        "service": "recommendation-service",
        "version": "1.0.0",
        "features": ["mood_detection", "mood_recommendation"]
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=settings.port, reload=True)
