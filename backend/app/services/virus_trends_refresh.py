"""Run one virus-trends fetch + merge to disk (used by CLI job and optional admin HTTP trigger)."""

from __future__ import annotations

import logging

from app.services.virus_trends_fetch import fetch_virus_trends, fetch_result_to_payload_dict
from app.services.virus_trends_storage import merge_and_save_after_fetch

log = logging.getLogger(__name__)


def run_virus_trends_refresh() -> tuple[int, str]:
    """
    Returns (exit_code, message). On fetch failure, does not overwrite existing JSON.
    """
    result = fetch_virus_trends()
    if not result.ok:
        log.error("virus-trends refresh failed: %s", result.error)
        return 1, f"fetch_failed: {result.error}"

    body = fetch_result_to_payload_dict(result)
    merged = merge_and_save_after_fetch(body)
    checked = merged.get("checked_at", "")
    log.info("virus-trends refresh OK (checked_at=%s)", checked)
    return 0, f"ok checked_at={checked}"
