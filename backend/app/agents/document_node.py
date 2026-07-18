import logging

from app.agents.state import AgentState
from app.core.database import SessionLocal
from app.repositories.document_repository import DocumentRepository
from app.repositories.user_repository import UserRepository
from app.schemas.answer import AskResponse, Citation, Confidence, ConfidenceLevel
from app.services.llm.llm_factory import LLMProviderFactory
from app.services.vectorstore.qdrant_service import qdrant_service

logger = logging.getLogger(__name__)

_MAP_SUMMARY_PROMPT = """Summarize the following excerpt from a larger document \
into 3-5 concise sentences, preserving all specific facts, figures, and terms \
(numbers, dates, names, amounts). This summary will later be combined with \
summaries of other parts of the same document."""

_REDUCE_SUMMARY_PROMPT = """You are combining several partial summaries of \
different sections of ONE document into a single, coherent, well-organized \
final summary. Preserve all specific facts and figures from the partial \
summaries. Do not add any information not present in them. Organize logically \
with brief section-like structure where it aids clarity."""

_BATCH_SIZE = 10  # chunks per map-reduce batch - a conservative size that
# comfortably fits within any of our LLM providers' context windows even
# for chunks near our MAX_CONTEXT_TOKENS ceiling (Step 21)


def _summarize_batch(chunks_text: str) -> str:
    provider = LLMProviderFactory.get_provider(task="fast")
    return provider.generate(
        messages=[
            {"role": "system", "content": _MAP_SUMMARY_PROMPT},
            {"role": "user", "content": chunks_text},
        ],
        temperature=0.1,
        max_tokens=300,
    )


def _reduce_summaries(batch_summaries: list[str], filename: str) -> str:
    provider = LLMProviderFactory.get_provider(task="quality")
    combined = "\n\n".join(f"Section summary {i+1}: {s}" for i, s in enumerate(batch_summaries))
    return provider.generate(
        messages=[
            {"role": "system", "content": _REDUCE_SUMMARY_PROMPT},
            {
                "role": "user",
                "content": f"DOCUMENT: {filename}\n\n{combined}",
            },
        ],
        temperature=0.1,
        max_tokens=800,
    )


def _summarize_document(document_id: str, filename: str) -> str:
    """
    Map-reduce summarization: retrieves ALL chunks for a document
    (Qdrant filter+scroll, not search), summarizes in batches (map),
    then combines batch summaries into one final summary (reduce).
    Skips the reduce step entirely if only one batch was needed.
    """
    chunks = qdrant_service.get_all_chunks_for_document(document_id)

    if not chunks:
        return "This document has no extractable content to summarize."

    batches = [chunks[i:i + _BATCH_SIZE] for i in range(0, len(chunks), _BATCH_SIZE)]
    logger.info(f"Summarizing '{filename}': {len(chunks)} chunks in {len(batches)} batch(es)")

    batch_summaries = []
    for batch in batches:
        batch_text = "\n\n".join(c.get("content", "") for c in batch)
        try:
            batch_summaries.append(_summarize_batch(batch_text))
        except Exception as e:
            logger.exception(f"Batch summarization failed for '{filename}': {e}")
            batch_summaries.append("[A section of this document could not be summarized.]")

    if len(batch_summaries) == 1:
        # Single batch - no reduce step needed, avoids a wasted LLM call
        # (same "skip unnecessary synthesis" principle as Step 29's planner)
        return batch_summaries[0]

    try:
        return _reduce_summaries(batch_summaries, filename)
    except Exception as e:
        logger.exception(f"Reduce step failed for '{filename}', concatenating batch summaries: {e}")
        return "\n\n".join(batch_summaries)


def document_node(state: AgentState) -> AgentState:
    """
    Handles document-level operations: full-document summarization
    (map-reduce over ALL of a document's chunks, no similarity search)
    and document listing (a direct Postgres query, no retrieval or LLM
    call at all). Deliberately uses the RIGHT tool per operation rather
    than routing everything through the retrieval/generation pipeline
    used by every prior agent.
    """
    db = SessionLocal()
    try:
        user = UserRepository(db).get_by_id(str(state["user_id"]))
        if not user:
            return {**state, "error": "User not found."}

        doc_repo = DocumentRepository(db)
        documents = doc_repo.list_by_owner(user.id)

        # Simple heuristic: does the query name a specific document (by
        # filename substring match)? A more sophisticated implementation
        # could use an LLM call to extract a target filename, but for
        # this scale a direct substring match against the user's own
        # document list is simple, fast, and has zero LLM cost/risk of
        # misinterpretation for this narrow task.
        query_lower = state["query"].lower()
        target_doc = next(
            (d for d in documents if d.filename.lower() in query_lower or
             query_lower in d.filename.lower()),
            None,
        )

        if target_doc:
            summary_text = _summarize_document(str(target_doc.id), target_doc.filename)
            result = AskResponse(
                query=state["query"],
                answer=summary_text,
                citations=[],  # whole-document summary - no per-claim
                # attribution needed, since it's ALL from this one known,
                # already-identified document (unlike QA/Research, which
                # mix content from potentially multiple sources)
                sources=[],
                confidence=Confidence(
                    level=ConfidenceLevel.HIGH,
                    retrieval_score=1.0,  # not applicable in the usual
                    # sense - the "retrieval" here is deterministic
                    # (all chunks of a known document), not similarity-based
                    self_verified=None,  # not applicable - map-reduce
                    # summarization isn't verified against retrieval the
                    # same way QA answers are; noted honestly as a
                    # different confidence semantics for this operation
                    reasoning=f"Full-document summary of '{target_doc.filename}' "
                    f"via map-reduce over all its content.",
                ),
            )
        else:
            # No specific document identified - list what's available
            doc_list = "\n".join(f"- {d.filename} ({d.status.value})" for d in documents)
            answer_text = (
                f"You have {len(documents)} document(s):\n{doc_list}"
                if documents
                else "You don't have any documents uploaded yet."
            )
            result = AskResponse(
                query=state["query"],
                answer=answer_text,
                citations=[],
                sources=[],
                confidence=Confidence(
                    level=ConfidenceLevel.HIGH,
                    retrieval_score=1.0,
                    self_verified=None,
                    reasoning="Direct document listing from database records - no retrieval or generation involved.",
                ),
            )

        return {**state, "result": result}

    except Exception as e:
        logger.exception(f"document_node failed for query='{state.get('query')}': {e}")
        return {**state, "error": str(e)}
    finally:
        db.close()