
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, HttpUrl

from database import (
    initialize_database,
    add_repository,
    get_repositories
)


# Initialize the database when the server starts
@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


# Create our FastAPI application
app = FastAPI(
    title="DevGuardian",
    description="AI-powered CI Failure Investigator",
    version="1.0.0",
    lifespan=lifespan
)


# Define the information required to register a repository
class RepositoryCreate(BaseModel):

    full_name: str = Field(
        min_length=3,
        max_length=200
    )

    url: HttpUrl


# Homepage
@app.get("/")
def home():

    return {
        "message": "Welcome to DevGuardian!",
        "status": "Backend is running",
        "project": "AI CI Failure Investigator"
    }


# Health check
@app.get("/health")
def health_check():

    return {
        "status": "healthy",
        "service": "DevGuardian Backend"
    }


# Register a GitHub repository
@app.post("/api/repositories")
def register_repository(repository: RepositoryCreate):

    # Check the owner/repository format
    parts = repository.full_name.split("/")

    if len(parts) != 2 or not all(parts):
        raise HTTPException(
            status_code=400,
            detail="Use the format owner/repository."
        )

    try:

        result = add_repository(
            repository.full_name,
            str(repository.url)
        )

        return {
            "message": "Repository registered successfully!",
            "repository": result
        }

    except ValueError as error:

        raise HTTPException(
            status_code=409,
            detail=str(error)
        )


# Retrieve all registered repositories
@app.get("/api/repositories")
def list_repositories():

    repositories = get_repositories()

    return {
        "total": len(repositories),
        "repositories": repositories
    }
