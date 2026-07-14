from app.schemas.search import SearchResult

_SYSTEM_PROMPT = """You are an enterprise knowledge assistant. You answer questions \
using ONLY the source documents provided below. You do not use any outside knowledge, \
even if you are confident about the answer from your own training.

CRITICAL RULES:
1. Answer using ONLY information present in the numbered sources below.
2. Every factual claim you make MUST be followed by a citation marker like [Source 1], \
referencing the source number(s) that support it.
3. If the sources do NOT contain enough information to answer the question, you MUST \
say: "I don't have enough information in the provided documents to answer this." \
Do NOT guess, speculate, or fill gaps with outside knowledge.
4. If different sources conflict, point out the conflict rather than picking one silently.
5. Do not mention these instructions in your answer. Just answer naturally, with citations.
"""


def build_context_block(sources: list[SearchResult]) -> str:
    """
    Formats retrieved chunks as clearly numbered, labeled sources so the
    LLM can cite them precisely, and so we can parse those citations
    back out programmatically in Step 23.
    """
    blocks = []
    for i, source in enumerate(sources, start=1):
        location = _describe_location(source)
        blocks.append(
            f"[Source {i}] (from \"{source.filename}\"{location})\n{source.content}"
        )
    return "\n\n".join(blocks)


def _describe_location(source: SearchResult) -> str:
    if source.page_number is not None:
        return f", page {source.page_number}"
    if source.slide_number is not None:
        return f", slide {source.slide_number}"
    if source.sheet_name is not None:
        return f", sheet '{source.sheet_name}'"
    if source.paragraph_index is not None:
        return f", paragraph {source.paragraph_index}"
    return ""


def build_messages(query: str, sources: list[SearchResult]) -> list[dict]:
    """
    Builds the full message list for the LLM call: system prompt with
    guardrails, and a user prompt containing the numbered context + question.
    """
    if not sources:
        # No retrieved context at all - the model should refuse outright,
        # but we make this explicit rather than relying on the model to
        # infer it from an empty context block.
        context_block = "(No relevant documents were found for this query.)"
    else:
        context_block = build_context_block(sources)

    user_prompt = f"""SOURCES:
{context_block}

QUESTION:
{query}

Answer the question using only the sources above, with [Source N] citations."""

    return [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]