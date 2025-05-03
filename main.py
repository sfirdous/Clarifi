import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path

from backend.database import database, metadata, engine
from backend.routes import stats ,upload,auth


# Lifespan function handles startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()       # On startup
    metadata.create_all(engine)    # Create tables if not exist
    yield
    await database.disconnect()    # On shutdown
    
    
# Initialize FastAPI with lifespan
app = FastAPI(lifespan=lifespan)


app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(stats.router)



# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
      
# Uvicorn entry point
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000) 