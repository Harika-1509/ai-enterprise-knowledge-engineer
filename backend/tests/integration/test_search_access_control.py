"""
Integration test for Step 17's core security guarantee: users must
NEVER see each other's documents in search results, regardless of
query content. This is arguably the single most important property
to have an automated regression test for in the whole project.
"""

import uuid

from qdrant_client.http.models import PointStruct, Filter, FieldCondition, MatchValue

from app.services.embedding.embedding_service import embedding_service


def test_search_never_returns_another_users_documents(test_qdrant_collection):
    user_a_id = str(uuid.uuid4())
    user_b_id = str(uuid.uuid4())

    shared_content = "The confidential stipend amount is 50000 per month."
    vector = embedding_service.embed_documents([shared_content])[0]

    # Insert IDENTICAL content owned by two different users - the
    # strongest possible test of owner_id filtering, since if the
    # filter were broken, this exact content would leak across users.
    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector={"dense": vector},
            payload={"document_id": "doc-a", "owner_id": user_a_id, "content": shared_content},
        ),
        PointStruct(
            id=str(uuid.uuid4()),
            vector={"dense": vector},
            payload={"document_id": "doc-b", "owner_id": user_b_id, "content": shared_content},
        ),
    ]
    test_qdrant_collection.upsert(collection_name="documents_test", points=points)

    query_vector = embedding_service.embed_query("What is the stipend?")

    # Search AS user_a - must only ever see user_a's point, never user_b's,
    # even though the content is byte-for-byte identical.
    results = test_qdrant_collection.query_points(
        collection_name="documents_test",
        query=query_vector,
        using="dense",
        limit=10,
        query_filter=Filter(
            must=[FieldCondition(key="owner_id", match=MatchValue(value=user_a_id))]
        ),
    )

    returned_owner_ids = {p.payload["owner_id"] for p in results.points}

    assert returned_owner_ids == {user_a_id}, (
        f"SECURITY REGRESSION: search returned documents owned by other users. "
        f"Expected only {user_a_id}, got {returned_owner_ids}"
    )