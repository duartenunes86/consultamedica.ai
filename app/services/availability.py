import json
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import os
_data_dir = Path(os.environ.get("DATA_DIR", "./data"))
DATA_FILE = _data_dir / "availability.json"
_lock = threading.Lock()


def _load() -> list[dict]:
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE) as f:
        return json.load(f).get("slots", [])


def _save(slots: list[dict]) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump({"slots": slots}, f, indent=2, ensure_ascii=False)


def _to_utc(dt_str: str) -> datetime:
    dt = datetime.fromisoformat(dt_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def get_available_slots() -> list[dict]:
    """Returns free slots that are at least 24h in the future, sorted by datetime."""
    with _lock:
        slots = _load()
    cutoff = datetime.now(timezone.utc) + timedelta(hours=24)
    available = [
        s for s in slots
        if not s.get("booked") and _to_utc(s["datetime"]) >= cutoff
    ]
    return sorted(available, key=lambda s: s["datetime"])


def get_all_slots() -> list[dict]:
    """Returns all slots (free and booked), sorted by datetime."""
    with _lock:
        slots = _load()
    return sorted(slots, key=lambda s: s["datetime"])


def add_slots(datetimes: list[str]) -> list[dict]:
    """Add new availability slots. Returns the created slots."""
    new_slots = []
    with _lock:
        slots = _load()
        for dt_str in datetimes:
            # Validate parseable
            _to_utc(dt_str)
            slot = {"id": uuid.uuid4().hex[:12], "datetime": dt_str, "booked": False}
            slots.append(slot)
            new_slots.append(slot)
        _save(slots)
    return new_slots


def book_slot(slot_id: str) -> dict:
    """
    Mark a slot as booked.
    Raises ValueError if already booked, not found, or < 24h in the future.
    """
    with _lock:
        slots = _load()
        for s in slots:
            if s["id"] == slot_id:
                if s.get("booked"):
                    raise ValueError("Este horário já foi reservado por outro paciente.")
                cutoff = datetime.now(timezone.utc) + timedelta(hours=24)
                if _to_utc(s["datetime"]) < cutoff:
                    raise ValueError("Este horário já não está disponível (menos de 24h de antecedência).")
                s["booked"] = True
                _save(slots)
                return s
        raise ValueError("Horário não encontrado.")


def delete_slot(slot_id: str) -> None:
    """Remove a slot (admin use)."""
    with _lock:
        slots = _load()
        slots = [s for s in slots if s["id"] != slot_id]
        _save(slots)
