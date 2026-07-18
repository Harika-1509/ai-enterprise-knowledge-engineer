import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class WebhookNotifier:
    """
    Fires outbound webhook notifications to n8n when internal events
    occur. Deliberately fire-and-forget with a short timeout and full
    exception suppression - a failed or slow webhook notification must
    NEVER block or fail the actual ingestion pipeline (Step 16) that
    triggers it. Workflow automation is an ENHANCEMENT on top of core
    functionality, not a dependency of it - same reliability philosophy
    established for query rewriting (Step 20) and LLM calls generally.
    """

    def notify_document_ingested(
        self, document_id: str, filename: str, owner_id: str, chunk_count: int
    ) -> None:
        url = settings.N8N_WEBHOOK_BASE_URL + settings.N8N_DOCUMENT_INGESTED_WEBHOOK_PATH
        payload = {
            "document_id": document_id,
            "filename": filename,
            "owner_id": owner_id,
            "chunk_count": chunk_count,
        }

        try:
            response = httpx.post(url, json=payload, timeout=settings.WEBHOOK_TIMEOUT_SECONDS)
            response.raise_for_status()
            logger.info(f"Webhook notified: document_ingested for '{filename}' -> n8n responded {response.status_code}")
        except Exception as e:
            # Deliberately broad exception handling: connection refused
            # (n8n not running), timeout, 404 (workflow not active in
            # n8n), or any other failure should ALL be swallowed here.
            # The document was successfully ingested regardless of
            # whether anyone was listening for the notification.
            logger.warning(f"Webhook notification failed for '{filename}' (non-critical, ingestion still succeeded): {e}")


webhook_notifier = WebhookNotifier()