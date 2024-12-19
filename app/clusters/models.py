from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class Cluster(Base):
    __tablename__ = "clusters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    total_ram = Column(Integer)
    total_cpu = Column(Integer)
    total_gpu = Column(Integer)
    available_ram = Column(Integer)
    available_cpu = Column(Integer)
    available_gpu = Column(Integer)

    organization = relationship("Organization", back_populates="clusters")
    deployments = relationship("Deployment", back_populates="cluster")
