from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.routes import auth
from backend.app.db.database import create_db_and_tables

app = FastAPI(
    title="ClearLedger API",
    description="Manual transaction logging for Zimbabwean merchants",
    version="0.1.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)


@app.on_event("startup")
def on_startup():
    """Create database tables on startup"""
    create_db_and_tables()


@app.get("/")
def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "ClearLedger API is running"}
