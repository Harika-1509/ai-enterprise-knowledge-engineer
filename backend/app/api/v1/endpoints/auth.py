print("LOADED AUTH.PY")
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import logging

from app.api.v1.dependencies import get_current_user
from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserResponse, UserLogin
from app.services.auth_service import AuthService
from app.services.oauth_service import oauth, oauth_service


router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/register", response_model=UserResponse, status_code=201)
def register(
    data: UserCreate,
    db: Session = Depends(get_db)
):
    service = AuthService(db)
    user = service.register(data)
    return user



@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Email/password login.
    """

    service = AuthService(db)

    token = service.login(
        UserLogin(
            email=form_data.username,
            password=form_data.password
        )
    )

    return Token(access_token=token)



@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: User = Depends(get_current_user)
):
    return current_user



# ==============================
# Google OAuth Login
# ==============================

@router.get("/google/login")
async def google_login(request: Request):

    redirect_uri = settings.GOOGLE_REDIRECT_URI

    return await oauth.google.authorize_redirect(
        request,
        redirect_uri
    )



@router.get("/google/callback")
async def google_callback(
    request: Request,
    db: Session = Depends(get_db)
):

    try:

        token = await oauth.google.authorize_access_token(
            request
        )

        userinfo = token.get("userinfo")


        if not userinfo:
            raise HTTPException(
                status_code=400,
                detail="Could not fetch Google user info"
            )


        access_token = oauth_service.handle_google_callback(
            db,
            userinfo
        )


        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/auth/callback?token={access_token}"
        )


    except Exception as e:

        logger.exception(
            f"Google OAuth failed: {e}"
        )

        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error=oauth_failed"
        )