"""ChangeDetectionEngine, WebhookReceiver, PollingChangeDetector, and EntityDiffer."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable
import time
import json

from infrastructure.logging.logger import StructuredLogger


@dataclass
class ChangeEvent:
    """Represents a detected change event in an external entity."""
    event_id: str
    service_name: str
    entity_type: str
    entity_id: str
    change_type: str  # 'created', 'updated', 'deleted'
    payload: Dict[str, Any] = field(default_factory=dict)
    diff: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class EntityDiffer:
    """Computes field-level diffs between entity states."""

    @staticmethod
    def compute_diff(old_state: Dict[str, Any], new_state: Dict[str, Any]) -> Dict[str, Any]:
        """Compare old and new entity states to return modified fields."""
        diff = {}
        all_keys = set(old_state.keys()).union(set(new_state.keys()))
        for key in all_keys:
            v_old = old_state.get(key)
            v_new = new_state.get(key)
            if v_old != v_new:
                diff[key] = {"old": v_old, "new": v_new}
        return diff


class WebhookReceiver:
    """Ingests and validates incoming third-party webhooks."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("WebhookReceiver")

    def parse_webhook(self, service_name: str, payload: Dict[str, Any], headers: Dict[str, str]) -> ChangeEvent:
        """Parse raw webhook request into standardized ChangeEvent."""
        self._logger.info(f"Received webhook for service '{service_name}'")
        entity_id = payload.get("id") or payload.get("entity_id") or "unknown_id"
        entity_type = payload.get("entity_type") or payload.get("object") or "resource"
        action = payload.get("action") or payload.get("event") or "updated"

        event_id = f"evt_wh_{service_name}_{int(time.time())}"
        return ChangeEvent(
            event_id=event_id,
            service_name=service_name,
            entity_type=entity_type,
            entity_id=str(entity_id),
            change_type=action,
            payload=payload,
        )


class PollingChangeDetector:
    """Detects changes by polling external connector endpoints and comparing state."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("PollingChangeDetector")
        self._entity_snapshots: Dict[str, Dict[str, Any]] = {}

    def _snapshot_key(self, service: str, entity_type: str, entity_id: str) -> str:
        return f"{service.lower()}:{entity_type.lower()}:{entity_id}"

    def detect_changes(
        self,
        service_name: str,
        entity_type: str,
        current_entities: List[Dict[str, Any]],
        id_field: str = "id",
    ) -> List[ChangeEvent]:
        """Compare current entity list with cached snapshot to emit ChangeEvents."""
        detected_events: List[ChangeEvent] = []
        current_seen = set()

        for entity in current_entities:
            entity_id = str(entity.get(id_field, ""))
            if not entity_id:
                continue
            current_seen.add(entity_id)
            key = self._snapshot_key(service_name, entity_type, entity_id)

            if key not in self._entity_snapshots:
                # Entity created
                self._entity_snapshots[key] = entity
                detected_events.append(
                    ChangeEvent(
                        event_id=f"evt_poll_{service_name}_{int(time.time())}",
                        service_name=service_name,
                        entity_type=entity_type,
                        entity_id=entity_id,
                        change_type="created",
                        payload=entity,
                    )
                )
            else:
                # Compare for updates
                old_state = self._entity_snapshots[key]
                diff = EntityDiffer.compute_diff(old_state, entity)
                if diff:
                    self._entity_snapshots[key] = entity
                    detected_events.append(
                        ChangeEvent(
                            event_id=f"evt_poll_{service_name}_{int(time.time())}",
                            service_name=service_name,
                            entity_type=entity_type,
                            entity_id=entity_id,
                            change_type="updated",
                            payload=entity,
                            diff=diff,
                        )
                    )

        return detected_events


class ChangeDetectionEngine:
    """Master engine unifying webhooks, polling, entity diffing, and event dispatching."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("ChangeDetectionEngine")
        self.webhook_receiver = WebhookReceiver()
        self.polling_detector = PollingChangeDetector()
        self._subscribers: List[Callable[[ChangeEvent], None]] = []

    def subscribe(self, callback: Callable[[ChangeEvent], None]) -> None:
        """Register change event subscriber callback."""
        self._subscribers.append(callback)

    def dispatch_event(self, event: ChangeEvent) -> None:
        """Dispatch event to all registered subscribers."""
        self._logger.info(f"Dispatching ChangeEvent: [{event.service_name}:{event.entity_type}] action={event.change_type}")
        for sub in self._subscribers:
            try:
                sub(event)
            except Exception as e:
                self._logger.error(f"Error in change event subscriber: {e}")
