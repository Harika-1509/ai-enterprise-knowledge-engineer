"""
Shared pytest fixtures. Integration tests use a DEDICATED test Qdrant
collection (never the real 'documents' collection) to avoid corrupting
real development data, and clean up after themselves.
"""

import uuid

import pytest
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, SparseVectorParams

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.core.security import hash_password

TEST_COLLECTION_NAME = "documents_test"


@pytest.fixture(scope="function")
def test_db_session():
    """
    Provides a DB session for a test, with automatic rollback after -
    changes made during the test never persist to the real database.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture(scope="function")
def test_user(test_db_session):
    """Creates a throwaway test user, cleaned up after the test."""
    unique_email = f"test_{uuid.uuid4().hex[:8]}@integration.test"
    user = User(
        email=unique_email,
        hashed_password=hash_password("TestPassword123"),
        full_name="Integration Test User",
        role=UserRole.MEMBER,
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)

    yield user

    test_db_session.delete(user)
    test_db_session.commit()


@pytest.fixture(scope="function")
def test_qdrant_collection():
    """
    Creates a DEDICATED test collection (never touches the real
    'documents' collection Step 15 created), yields the client, then
    deletes the test collection entirely after the test - full cleanup,
    no leftover test data accumulating between runs.
    """
    client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)

    client.create_collection(
        collection_name=TEST_COLLECTION_NAME,
        vectors_config={"dense": VectorParams(size=settings.EMBEDDING_DIMENSION, distance=Distance.COSINE)},
        sparse_vectors_config={"sparse": SparseVectorParams()},
    )

    yield client

    client.delete_collection(TEST_COLLECTION_NAME)