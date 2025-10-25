from fastapi import FastAPI
from backend.routes import recipe_agent
from backend.app.db.database import create_db
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

#Create the database
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    create_db()
    yield
    # Shutdown code (optional)

app = FastAPI(lifespan=lifespan)

# Include routers
app.include_router(recipe_agent.router, prefix="/api", tags=["recipes"])

@app.get("/")
def root():
    return {"message": "Welcome to Mise-en-Place AI - Your Recipe Prep Assistant!"}

#Connects to the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#uvicorn backend.app.main:app --reload