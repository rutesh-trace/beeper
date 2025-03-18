import os
from contextlib import asynccontextmanager
import socketio
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

import db_domains.db as db
from authentication.routers import router as auth_router
from chats.websockets import socket_app
from common.cache_string import refresh
from config import app_config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event manager for startup and shutdown tasks."""
    db.init_db()
    print("Initializing database...")
    yield
    print("Shutting down...")


app = FastAPI(
    title="Beeper",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

MEDIA_DIR = os.path.abspath("media")
print(f"Serving media from: {MEDIA_DIR}")
app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")
app.mount("/", socket_app)

# ✅ Include All Routers
app.include_router(auth_router)

if __name__ == "__main__":
    load_dotenv()
    refresh()
    uvicorn.run(
        "main:app",
        host=app_config.HOST_URL,
        port=app_config.HOST_PORT,
        log_level="info",
        reload=True
    )
