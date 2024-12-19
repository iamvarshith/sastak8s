from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.db.database import Base
import enum

class DeploymentStatus(enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed" # current no idea when to complete it
    FAILED = "failed"

class Deployment(Base):
    __tablename__ = "deployments"

    id = Column(Integer, primary_key=True, index=True)
    cluster_id = Column(Integer, ForeignKey("clusters.id"))
    docker_image = Column(String)
    ram_required = Column(Integer)
    cpu_required = Column(Integer)
    gpu_required = Column(Integer)
    priority = Column(Integer)
    status = Column(Enum(DeploymentStatus))

    cluster = relationship("Cluster", back_populates="deployments")
