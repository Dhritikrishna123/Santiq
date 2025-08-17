"""Audit logging and tracking for ETL operations."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class AuditEvent(BaseModel):
    """Represents a single audit event."""

    id: str
    timestamp: datetime
    event_type: str  # pipeline_start, plugin_execute, pipeline_complete, etc.
    pipeline_id: str
    stage: Optional[str] = None
    plugin_name: Optional[str] = None
    plugin_type: Optional[str] = None
    data: Dict[str, Any] = {}
    success: bool = True
    error_message: Optional[str] = None


class AuditLogger:
    """Handles audit logging for ETL operations."""

    def __init__(self, log_file: Optional[str] = None) -> None:
        self.log_file = Path(log_file) if log_file else self._get_default_log_file()
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # Ensure log file exists (but don't initialize with content)
        if not self.log_file.exists():
            self.log_file.touch()

    def _get_default_log_file(self) -> Path:
        """Get default audit log file location."""
        import os

        if os.name == "nt":  # Windows
            log_dir = os.getenv("APPDATA", os.path.expanduser("~"))
        else:  # Unix-like
            log_dir = os.getenv("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))

        return Path(log_dir) / "santiq" / "audit.jsonl"

    def log_event(
        self,
        event_type: str,
        pipeline_id: str,
        stage: Optional[str] = None,
        plugin_name: Optional[str] = None,
        plugin_type: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> str:
        """Log an audit event."""
        event = AuditEvent(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            event_type=event_type,
            pipeline_id=pipeline_id,
            stage=stage,
            plugin_name=plugin_name,
            plugin_type=plugin_type,
            data=data or {},
            success=success,
            error_message=error_message,
        )

        # Append to JSONL file
        with open(self.log_file, "a") as f:
            f.write(event.model_dump_json() + "\n")

        return event.id

    def get_pipeline_events(self, pipeline_id: str) -> List[AuditEvent]:
        """Get all events for a specific pipeline."""
        events: List[AuditEvent] = []

        if not self.log_file.exists():
            return events

        with open(self.log_file) as f:
            for line in f:
                try:
                    event_data = json.loads(line.strip())
                    event = AuditEvent(**event_data)
                    if event.pipeline_id == pipeline_id:
                        events.append(event)
                except (json.JSONDecodeError, Exception):
                    continue

        return sorted(events, key=lambda e: e.timestamp)

    def get_recent_events(self, limit: int = 100) -> List[AuditEvent]:
        """Get the most recent audit events."""
        events: List[AuditEvent] = []

        if not self.log_file.exists():
            return events

        with open(self.log_file) as f:
            for line in f:
                try:
                    event_data = json.loads(line.strip())
                    events.append(AuditEvent(**event_data))
                except (json.JSONDecodeError, Exception):
                    continue

        return sorted(events, key=lambda e: e.timestamp, reverse=True)[:limit]
