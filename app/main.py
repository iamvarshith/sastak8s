import asyncio
from fastapi import FastAPI
from app.auth.router import router as auth_router
from app.clusters.router import router as cluster_router
from app.deployments.router import router as deployment_router
from app.db.database import engine
from app.auth import models as auth_models
from app.clusters import models as cluster_models
from app.deployments import models as deployment_models

from app.scheduler.scheduler import run_deployment_processor

app = FastAPI()

# Create tables in the database at startup (if they don't exist)
auth_models.Base.metadata.create_all(bind=engine)
cluster_models.Base.metadata.create_all(bind=engine)
deployment_models.Base.metadata.create_all(bind=engine)

# Include routers for different modules
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(cluster_router, prefix="/clusters", tags=["clusters"])
app.include_router(deployment_router, prefix="/deployments", tags=["deployments"])

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(run_deployment_processor())

@app.get("/")
async def root():
    return {"message": "Welcome to the Cluster Management API"}
