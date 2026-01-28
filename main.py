from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.agent import router as agent_router
from api.routes.auth import router as auth_router
from api.routes.google_auth import router as google_auth_router

app = FastAPI(title="AI Workspace Automation Agent", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent_router, prefix="/api")
app.include_router(auth_router, prefix="/auth")
app.include_router(google_auth_router, prefix="/auth")