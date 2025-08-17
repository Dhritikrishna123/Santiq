"""Audit logging and tracking for ETL operations."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class AuditEvent(BaseModel):
    """Represents a single audit event in the ETL pipeline.

    This model captures all relevant information about an event that occurs
    during pipeline execution, including timing, context, and outcome.

    Attributes:
        id: Unique identifier for the event
        timestamp: When the event occurred
        event_type: Type of event (pipeline_start, plugin_execute, pipeline_complete, etc.)
        pipeline_id: ID of the pipeline this event belongs to
        stage: Pipeline stage where the event occurred (extract, profile, transform, load)
        plugin_name: Name of the plugin involved in the event
        plugin_type: Type of plugin (extractor, profiler, transformer, loader)
        data: Additional event-specific data
        success: Whether the event was successful
        error_message: Error message if the event failed
    """

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
    """Handles audit logging for ETL operations.

    This class provides comprehensive logging capabilities for tracking
    all events that occur during ETL pipeline execution. It maintains
    a persistent log file in JSONL format for easy parsing and analysis.

    The logger automatically creates log directories and files as needed,
    and provides methods for querying historical events.
    """

    def __init__(self, log_file: Optional[str] = None) -> None:
        """Initialize the audit logger.

        Args:
            log_file: Optional path to the log file. If not provided,
                     uses the default location in the user's data directory.
        """
        self.log_file = Path(log_file) if log_file else self._get_default_log_file()
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # Ensure log file exists (but don't initialize with content)
        if not self.log_file.exists():
            self.log_file.touch()

    def _get_default_log_file(self) -> Path:
        """Get default audit log file location.

        Returns:
            Path to the default audit log file location based on the operating system.
            On Windows, uses APPDATA environment variable or user home directory.
            On Unix-like systems, uses XDG_DATA_HOME or ~/.local/share.
        """
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
        """Log an audit event to the persistent log file.

        Args:
            event_type: Type of event (e.g., 'pipeline_start', 'plugin_execute', 'pipeline_complete')
            pipeline_id: Unique identifier for the pipeline
            stage: Pipeline stage where the event occurred (extract, profile, transform, load)
            plugin_name: Name of the plugin involved in the event
            plugin_type: Type of plugin (extractor, profiler, transformer, loader)
            data: Additional event-specific data as a dictionary
            success: Whether the event was successful
            error_message: Error message if the event failed

        Returns:
            Unique identifier for the logged event

        Raises:
            IOError: If the log file cannot be written to
        """
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
        """Get all events for a specific pipeline.

        Args:
            pipeline_id: Unique identifier for the pipeline

        Returns:
            List of audit events for the specified pipeline, sorted by timestamp
        """
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
        """Get the most recent audit events.

        Args:
            limit: Maximum number of events to return (default: 100)

        Returns:
            List of the most recent audit events, sorted by timestamp (newest first)
        """
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
