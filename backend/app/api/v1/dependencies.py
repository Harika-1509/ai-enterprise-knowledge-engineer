from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.models.user import UserRole

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = credentials.credentials
    user_id = decode_access_token(token)
    if user_id is None:
        raise credentials_exception

    user = UserRepository(db).get_by_id(user_id)
    if user is None:
        raise credentials_exception
    return user




def require_role(*allowed_roles: UserRole):
    """
    Dependency factory. Returns a dependency function that checks whether
    the current user's role is in the allowed set.

    Usage: Depends(require_role(UserRole.ADMIN))
           Depends(require_role(UserRole.ADMIN, UserRole.MEMBER))
    """

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires one of the following roles: "
                f"{', '.join(r.value for r in allowed_roles)}.",
            )
        return current_user

    return role_checker