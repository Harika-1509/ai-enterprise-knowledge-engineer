"""
End-to-end test of the complete critical user journey, through REAL
HTTP requests via FastAPI's TestClient - register, login, upload,
wait for ingestion, ask a question, verify a grounded answer with
citations. This is the single most important test in the entire
suite: if this fails, the product itself is broken for real users,
regardless of what any lower-level test says.
"""

import io
import time
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture(scope="module")
def unique_user():
    suffix = uuid.uuid4().hex[:8]
    return {
        "email": f"e2e_test_{suffix}@example.com",
        "password": "E2ETestPassword123",
        "full_name": "E2E Test User",
    }


def test_full_journey_register_login_upload_ask(unique_user):
    # ---- Step 1: Register ----
    register_response = client.post("/api/v1/auth/register", json=unique_user)
    assert register_response.status_code == 201, register_response.text
    assert "hashed_password" not in register_response.json()

    # ---- Step 2: Login ----
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": unique_user["email"],
            "password": unique_user["password"],
        },
    )
    assert login_response.status_code == 200, login_response.text

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # ---- Step 3: Confirm authenticated identity ----
    me_response = client.get("/api/v1/auth/me", headers=headers)

    assert me_response.status_code == 200
    assert me_response.json()["email"] == unique_user["email"]

    # ---- Step 4: Upload a real document ----
    test_content = (
        b"Company Handbook\n\n"
        b"The remote work policy allows employees to work from home "
        b"up to 3 days per week. Requests must be approved by a manager."
    )

    files = {
        "file": (
            "handbook.txt",
            io.BytesIO(test_content),
            "text/plain",
        )
    }

    upload_response = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        files=files,
    )

    assert upload_response.status_code == 201, upload_response.text

    document_id = upload_response.json()["id"]

    assert upload_response.json()["status"] == "pending"

    # ---- Step 5: Wait for ingestion ----
    max_wait_seconds = 15
    poll_interval = 1

    status = "pending"

    for _ in range(max_wait_seconds):

        docs_response = client.get(
            "/api/v1/documents/",
            headers=headers,
        )

        matching = [
            d
            for d in docs_response.json()
            if d["id"] == document_id
        ]

        if matching:
            status = matching[0]["status"]

        if status == "completed":
            break

        time.sleep(poll_interval)

    assert status == "completed", (
        f"Ingestion did not complete in time, "
        f"final status: {status}"
    )

    # ---- Step 6: Ask question ----

    ask_response = client.post(
        "/api/v1/ask/",
        headers=headers,
        json={
            "query": "How many days per week can employees work from home?",
            "limit": 5,
        },
    )

    assert ask_response.status_code == 200, ask_response.text

    body = ask_response.json()

    assert "3" in body["answer"], (
        f"Expected correct fact, got: {body['answer']}"
    )

    assert len(body["citations"]) > 0, (
        "Expected at least one citation"
    )

    assert body["citations"][0]["filename"] == "handbook.txt"


    # ---- Step 7: Security check ----

    other_user_suffix = uuid.uuid4().hex[:8]

    other_user = {
        "email": f"e2e_other_{other_user_suffix}@example.com",
        "password": "OtherPassword123",
        "full_name": "Other E2E User",
    }

    client.post(
        "/api/v1/auth/register",
        json=other_user,
    )

    other_login = client.post(
        "/api/v1/auth/login",
        data={
            "username": other_user["email"],
            "password": other_user["password"],
        },
    )

    other_headers = {
        "Authorization": (
            f"Bearer {other_login.json()['access_token']}"
        )
    }


    other_ask_response = client.post(
        "/api/v1/ask/",
        headers=other_headers,
        json={
            "query": "How many days per week can employees work from home?",
            "limit": 5,
        },
    )

    assert other_ask_response.status_code == 200

    other_body = other_ask_response.json()

    assert len(other_body["citations"]) == 0, (
        "SECURITY REGRESSION: second user received "
        "citations from first user's private document"
    )


    # ---- Cleanup ----

    client.delete(
        f"/api/v1/documents/{document_id}",
        headers=headers,
    )