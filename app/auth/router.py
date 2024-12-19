from sqlite3 import IntegrityError

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.auth import models, utils
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pydantic import BaseModel
from fastapi import APIRouter, Depends




router = APIRouter()

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


class Token(BaseModel):
    access_token: str
    token_type: str

import secrets

def generate_unique_invite_code():
    return secrets.token_urlsafe(16)


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = utils.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = utils.create_access_token(
        data={"sub": user.username,
              "organization_id": user.organization_id}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register")
async def register_user(username: str, password: str, invite_code: str, db: Session = Depends(get_db)):
    organization = db.query(models.Organization).filter(models.Organization.invite_code == invite_code).first()
    if not organization:
        raise HTTPException(status_code=400, detail="Invalid invite code")

    existing_user = db.query(models.User).filter(models.User.username == username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_password = utils.get_password_hash(password)
    new_user = models.User(username=username, hashed_password=hashed_password, organization_id=organization.id)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully"}



@router.post("/create_organization/")
def create_organization(name: str, db: Session = Depends(get_db)):
    # Check if the organization name already exists
    existing_org = db.query(models.Organization).filter(models.Organization.name == name).first()
    if existing_org:
        raise HTTPException(status_code=400, detail="Organization with this name already exists")

    # Proceed to create the new organization
    invite_code = generate_unique_invite_code()
    new_org = models.Organization(name=name, invite_code=invite_code)
    db.add(new_org)
    db.commit()
    db.refresh(new_org)
    return {"message": "Organization created successfully", "invite_code": invite_code}


