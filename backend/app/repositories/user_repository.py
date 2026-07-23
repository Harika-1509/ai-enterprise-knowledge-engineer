from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    """Handles all direct database access for User. No business logic here."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email).first()

    def get_by_id(self, user_id: str) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def create(self, email: str, hashed_password: str, full_name: str) -> User:
        user = User(email=email, hashed_password=hashed_password, full_name=full_name)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_by_google_id(self, google_id: str) -> User | None:
        return (
            self.db.query(User)
            .filter(User.google_id == google_id)
            .first()
        )


    def create_from_google(
        self,
        email: str,
        full_name: str,
        google_id: str,
        avatar_url: str | None
    ) -> User:

        user = User(
            email=email,
            full_name=full_name,
            google_id=google_id,
            avatar_url=avatar_url,
            hashed_password=None,
            is_active=True,
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user


    def link_google_to_existing(
        self,
        user: User,
        google_id: str,
        avatar_url: str | None
    ) -> User:

        user.google_id = google_id
        user.avatar_url = avatar_url

        self.db.commit()
        self.db.refresh(user)

        return user