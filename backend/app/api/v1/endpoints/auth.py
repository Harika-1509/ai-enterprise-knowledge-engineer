from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserResponse, UserLogin
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201)
def register(data: UserCreate, db: Session = Depends(get_db)):
    service = AuthService(db)
    user = service.register(data)
    return user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Uses OAuth2PasswordRequestForm (form fields: username, password) because
    that's what FastAPI's /docs Swagger 'Authorize' button expects natively.
    We map 'username' to our email field.
    """
    service = AuthService(db)
    token = service.login(UserLogin(email=form_data.username, password=form_data.password))
    return Token(access_token=token)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user