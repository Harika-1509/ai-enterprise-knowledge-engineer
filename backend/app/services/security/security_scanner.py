import logging
import re

logger = logging.getLogger(__name__)

# Known prompt-injection signatures commonly seen in indirect injection
# attempts embedded in documents. Deliberately pattern-based (not
# LLM-based) - fast, deterministic, and not itself vulnerable to being
# "argued out of" flagging something, unlike an LLM judge would be.
# This is explicitly a FIRST LINE of defense, not a complete solution -
# sophisticated injection attempts can evade simple pattern matching,
# and this should be understood as one layer in a defense-in-depth
# strategy, not the only one.
_INJECTION_PATTERNS = [
    re.compile(r"ignore (all |the )?(previous|prior|above) instructions", re.IGNORECASE),
    re.compile(r"disregard (all |the )?(previous|prior|above)", re.IGNORECASE),
    re.compile(r"you are now (a |an )?(?!.*enterprise knowledge assistant)", re.IGNORECASE),
    re.compile(r"system\s*:\s*", re.IGNORECASE),  # attempts to fake a system message
    re.compile(r"reveal (all |your )?(system prompt|instructions|api key)", re.IGNORECASE),
    re.compile(r"print (all|every) (user|password|api key|secret)", re.IGNORECASE),
]

# Lightweight PII-pattern detection - intentionally simple regex, not a
# full PII-detection library (e.g. Microsoft Presidio) - flagged as a
# reasonable starting point for this project's scope, with a note that
# a dedicated PII-detection library would be the production-grade upgrade.
_PII_PATTERNS = {
    "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "phone_like": re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "ssn_like": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
}


class SecurityScanner:
    """
    Screens retrieved chunk content for two distinct concerns:
    1. Prompt injection signatures - chunks matching these are EXCLUDED
       from the prompt entirely (hard block - no legitimate document
       content needs to say "ignore previous instructions" to an LLM).
    2. PII-like patterns - chunks matching these are FLAGGED but NOT
       blocked (soft signal - many legitimate documents contain emails/
       phone numbers, e.g. a company directory or an offer letter's
       contact info; outright blocking would be too aggressive).
    """

    def scan_chunk(self, content: str) -> dict:
        injection_matches = [p.pattern for p in _INJECTION_PATTERNS if p.search(content)]
        pii_matches = [name for name, p in _PII_PATTERNS.items() if p.search(content)]

        return {
            "has_injection_risk": len(injection_matches) > 0,
            "injection_patterns_matched": injection_matches,
            "has_pii_risk": len(pii_matches) > 0,
            "pii_types_matched": pii_matches,
        }

    def scan_chunks(self, chunks: list) -> tuple[list, list[dict]]:
        """
        Scans a list of chunk-like objects (must have a `.content`
        attribute - works with SearchResult from Step 17). Returns
        (safe_chunks, security_flags) where safe_chunks has any
        injection-flagged chunks REMOVED, and security_flags contains
        details on everything flagged (injection AND PII) for logging/
        surfacing to the caller.
        """
        safe_chunks = []
        flags = []

        for chunk in chunks:
            scan_result = self.scan_chunk(chunk.content)

            if scan_result["has_injection_risk"]:
                logger.warning(
                    f"Excluded chunk from document_id={getattr(chunk, 'document_id', '?')} "
                    f"due to injection pattern match: {scan_result['injection_patterns_matched']}"
                )
                flags.append({"document_id": str(getattr(chunk, "document_id", "")), **scan_result})
                continue  # hard block - do not include in safe_chunks

            if scan_result["has_pii_risk"]:
                logger.info(
                    f"PII-like pattern flagged (not blocked) in document_id="
                    f"{getattr(chunk, 'document_id', '?')}: {scan_result['pii_types_matched']}"
                )
                flags.append({"document_id": str(getattr(chunk, "document_id", "")), **scan_result})

            safe_chunks.append(chunk)

        return safe_chunks, flags


security_scanner = SecurityScanner()