"""Job orchestration placeholder.

Long-running feature extraction and model training should eventually run as
tracked background jobs instead of blocking API requests.
"""

from __future__ import annotations


def job_service_ready() -> bool:
    return True
