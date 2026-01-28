from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.agent import router as agent_router
from api.routes.auth import router as auth_router
from config import settings

app = FastAPI(title="AI Workspace Automation Agent", version="0.1.0")

origins = [origin.strip() for origin in settings.FRONTEND_ORIGINS.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent_router, prefix="/api")
app.include_router(auth_router, prefix="/auth")


@app.get("/health")
def health_check():
    return {"status": "ok"}
