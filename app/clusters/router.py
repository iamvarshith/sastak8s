from fastapi import APIRouter, Depends, HTTPException
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.clusters import models
from app.auth.utils import oauth2_scheme
from pydantic import BaseModel

router = APIRouter()

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

class ClusterCreate(BaseModel):
    name: str
    total_ram: int
    total_cpu: int
    total_gpu: int


def retrive_organization_id(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        organization_id = payload.get("organization_id")
        return organization_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
@router.post("/create")
async def create_cluster(cluster: ClusterCreate, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    # get the user's organization from the token
    org = retrive_organization_id(token)
    organization_id = int(org) if org else 1

    new_cluster = models.Cluster(
        name=cluster.name,
        organization_id=organization_id,
        total_ram=cluster.total_ram,
        total_cpu=cluster.total_cpu,
        total_gpu=cluster.total_gpu,
        available_ram=cluster.total_ram,
        available_cpu=cluster.total_cpu,
        available_gpu=cluster.total_gpu
    )
    db.add(new_cluster)
    db.commit()
    db.refresh(new_cluster)

    return {"message": "Cluster created successfully", "cluster_id": new_cluster.id , "organization_id": organization_id}

@router.get("/list")
async def list_clusters(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    org = retrive_organization_id(token)
    organization_id = int(org) if org else 1
    clusters = db.query(models.Cluster).filter(models.Cluster.organization_id == organization_id).all()
    return clusters
