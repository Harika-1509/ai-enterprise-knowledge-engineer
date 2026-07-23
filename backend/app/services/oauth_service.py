import logging

from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token
from app.repositories.user_repository import UserRepository


logger = logging.getLogger(__name__)


oauth = OAuth()

oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile"
    },
)


class OAuthService:

    def handle_google_callback(
        self,
        db: Session,
        userinfo: dict
    ) -> str:

        google_id = userinfo["sub"]
        email = userinfo["email"]

        full_name = userinfo.get(
            "name",
            email.split("@")[0]
        )

        avatar_url = userinfo.get("picture")


        repo = UserRepository(db)


        # 1. Existing Google user
        user = repo.get_by_google_id(google_id)


        if user:
            logger.info(
                f"Google login: existing user {email}"
            )


        else:
            # 2. Existing email/password user
            existing_user = repo.get_by_email(email)


            if existing_user:

                logger.info(
                    f"Linking Google account {email}"
                )

                user = repo.link_google_to_existing(
                    existing_user,
                    google_id,
                    avatar_url
                )


            else:
                # 3. New Google signup

                logger.info(
                    f"Creating Google user {email}"
                )

                user = repo.create_from_google(
                    email,
                    full_name,
                    google_id,
                    avatar_url
                )


        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive"
            )


        # Same JWT as normal login
        return create_access_token(
            subject=str(user.id)
        )


oauth_service = OAuthService()