from fastapi import FastAPI
from api.routes.agent import router as agent_router
from api.routes.auth import router as auth_router

app = FastAPI(title="AI Workspace Automation Agent")

app.include_router(agent_router, prefix="/api")
app.include_router(auth_router, prefix="/auth")