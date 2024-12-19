from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.deployments import models
from app.clusters.models import Cluster
from app.auth.utils import oauth2_scheme
from pydantic import BaseModel
from app.scheduler.scheduler import schedule_deployment

router = APIRouter()

class DeploymentCreate(BaseModel):
    cluster_id: int
    docker_image: str
    ram_required: int
    cpu_required: int
    gpu_required: int
    priority: int

@router.post("/create")
async def create_deployment(deployment: DeploymentCreate, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    cluster = db.query(Cluster).filter(Cluster.id == deployment.cluster_id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")

    new_deployment = models.Deployment(
        cluster_id=deployment.cluster_id,
        docker_image=deployment.docker_image,
        ram_required=deployment.ram_required,
        cpu_required=deployment.cpu_required,
        gpu_required=deployment.gpu_required,
        priority=deployment.priority,
        status=models.DeploymentStatus.QUEUED
    )
    db.add(new_deployment)
    db.commit()
    db.refresh(new_deployment)

    # Trigger the scheduling algorithm
    await schedule_deployment(db, new_deployment.id)

    return {"message": "Deployment created and queued", "deployment_id": new_deployment.id}

@router.get("/list")
async def list_deployments(cluster_id: int, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    deployments = db.query(models.Deployment).filter(models.Deployment.cluster_id == cluster_id).all()
    return deployments
