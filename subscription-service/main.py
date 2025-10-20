from fastapi import FastAPI
from handlers.subscription_handler import router as subscription_router
from middleware.auth_middleware import AuthMiddleware
import uvicorn

app = FastAPI(title="Subscription Service", version="0.1")

# Middleware global
app.add_middleware(AuthMiddleware)

# Router de suscripciones
app.include_router(subscription_router, prefix="/subscriptions", tags=["Subscriptions"])


# Health check
@app.get("/health")
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8007, reload=True)
