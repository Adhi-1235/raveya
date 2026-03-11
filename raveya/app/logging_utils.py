import json
from typing import Any, Dict

from sqlalchemy.orm import Session

from .models import AIRequestLog


def log_ai_interaction(
    db: Session,
    *,
    module_name: str,
    request_payload: Dict[str, Any],
    prompt: str,
    response: str,
) -> AIRequestLog:
    """
    Persists a structured log entry for an AI interaction.
    """
    log = AIRequestLog(
        module_name=module_name,
        request_payload=json.dumps(request_payload, ensure_ascii=False),
        prompt=prompt,
        response=response,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

