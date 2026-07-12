from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_current_user, require_role
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserResponse

router = APIRouter()


@router.get("/users", response_model=list[UserResponse])
def list_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    """Admin-only: list every user in the system."""
    return db.query(User).all()


@router.patch("/users/{user_id}/deactivate", response_model=UserResponse)
def deactivate_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    """Admin-only: deactivate a user account."""
    from fastapi import HTTPException, status

    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    target.is_active = False
    db.commit()
    db.refresh(target)
    return target