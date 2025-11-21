from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from config import settings
import jwt


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware para autenticación JWT"""

    async def dispatch(self, request: Request, call_next):
        # Rutas públicas que no requieren autenticación
        public_paths = ["/health", "/docs", "/openapi.json", "/redoc"]
        
        if request.url.path in public_paths:
            return await call_next(request)

        # Obtener token del header Authorization
        auth_header = request.headers.get("Authorization")
        
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Token de autenticación no proporcionado"}
            )

        token = auth_header.split(" ")[1]

        try:
            # Verificar y decodificar el token
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm]
            )
            
            # Agregar información del usuario al request
            request.state.user = {
                "user_id": payload.get("user_id"),
                "email": payload.get("email"),
                "role": payload.get("role", "user")
            }

        except jwt.ExpiredSignatureError:
            return JSONResponse(
                status_code=401,
                content={"detail": "Token expirado"}
            )
        except jwt.InvalidTokenError:
            return JSONResponse(
                status_code=401,
                content={"detail": "Token inválido"}
            )

        return await call_next(request)
