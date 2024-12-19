import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth.models import Organization
from app.clusters.models import Cluster
from app.deployments.models import Deployment, DeploymentStatus
from app.db.database import get_db, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set up a test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Override the dependency
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="module")
def test_db():
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Drop tables
    Base.metadata.drop_all(bind=engine)


def test_create_organization(test_db):
    response = client.post("/auth/create-organization/", json={"name": "Test Org"})
    assert response.status_code == 200
    assert "invite_code" in response.json()


def test_create_duplicate_organization(test_db):
    client.post("/auth/create-organization/", json={"name": "Duplicate Org"})
    response = client.post("/auth/create-organization/", json={"name": "Duplicate Org"})
    assert response.status_code == 400
    assert "Organization with this name already exists" in response.json()["detail"]


def test_create_cluster(test_db):
    # First, create an organization
    org_response = client.post("/auth/create-organization/", json={"name": "Org for Cluster"})
    org_id = org_response.json()["id"]

    cluster_data = {
        "name": "Test Cluster",
        "organization_id": org_id,
        "total_ram": 1024,
        "total_cpu": 4,
        "total_gpu": 2
    }
    response = client.post("/clusters/create", json=cluster_data)
    assert response.status_code == 200
    assert "cluster_id" in response.json()


def test_create_deployment(test_db):
    # Create an organization and a cluster first
    org_response = client.post("/auth/create-organization/", json={"name": "Org for Deployment"})
    org_id = org_response.json()["id"]

    cluster_data = {
        "name": "Cluster for Deployment",
        "organization_id": org_id,
        "total_ram": 1024,
        "total_cpu": 4,
        "total_gpu": 2
    }
    cluster_response = client.post("/clusters/create", json=cluster_data)
    cluster_id = cluster_response.json()["cluster_id"]

    deployment_data = {
        "cluster_id": cluster_id,
        "docker_image": "test_image:latest",
        "ram_required": 512,
        "cpu_required": 2,
        "gpu_required": 1,
        "priority": 1
    }
    response = client.post("/deployments/create", json=deployment_data)
    assert response.status_code == 200
    assert "deployment_id" in response.json()


def test_process_deployment(test_db):
    # This test will need to mock the RabbitMQ connection
    # For simplicity, we'll just test the database operations
    db = next(override_get_db())
    org = Organization(name="Org for Processing")
    db.add(org)
    db.commit()

    cluster = Cluster(name="Cluster for Processing", organization_id=org.id,
                      total_ram=1024, total_cpu=4, total_gpu=2,
                      available_ram=1024, available_cpu=4, available_gpu=2)
    db.add(cluster)
    db.commit()

    deployment = Deployment(cluster_id=cluster.id, docker_image="test:latest",
                            ram_required=512, cpu_required=2, gpu_required=1,
                            priority=1, status=DeploymentStatus.QUEUED)
    db.add(deployment)
    db.commit()

    from app.scheduler.scheduler import process_deployment
    process_deployment(db, deployment.id)

    updated_deployment = db.query(Deployment).filter(Deployment.id == deployment.id).first()
    assert updated_deployment.status == DeploymentStatus.RUNNING

    updated_cluster = db.query(Cluster).filter(Cluster.id == cluster.id).first()
    assert updated_cluster.available_ram == 512
    assert updated_cluster.available_cpu == 2
    assert updated_cluster.available_gpu == 1


def test_insufficient_resources(test_db):
    db = next(override_get_db())
    org = Organization(name="Org for Insufficient Resources")
    db.add(org)
    db.commit()

    cluster = Cluster(name="Cluster for Insufficient", organization_id=org.id,
                      total_ram=512, total_cpu=2, total_gpu=1,
                      available_ram=512, available_cpu=2, available_gpu=1)
    db.add(cluster)
    db.commit()

    deployment = Deployment(cluster_id=cluster.id, docker_image="test:latest",
                            ram_required=1024, cpu_required=4, gpu_required=2,
                            priority=1, status=DeploymentStatus.QUEUED)
    db.add(deployment)
    db.commit()

    from app.scheduler.scheduler import process_deployment
    process_deployment(db, deployment.id)

    updated_deployment = db.query(Deployment).filter(Deployment.id == deployment.id).first()
    assert updated_deployment.status == DeploymentStatus.QUEUED

    updated_cluster = db.query(Cluster).filter(Cluster.id == cluster.id).first()
    assert updated_cluster.available_ram == 512
    assert updated_cluster.available_cpu == 2
    assert updated_cluster.available_gpu == 1
