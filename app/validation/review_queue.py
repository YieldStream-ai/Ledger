from __future__ import annotations

import threading
from datetime import datetime, timezone

from pydantic import BaseModel


class ReviewItem(BaseModel):
    id: str
    timestamp: str
    file_name: str
    bank_detected: str | None = None
    discrepancy: float
    expected_ending: float
    actual_ending: float
    parsed_data_snapshot: dict


_lock = threading.Lock()
_queue: list[ReviewItem] = []
MAX_QUEUE_SIZE = 500


def add_to_review(item: ReviewItem) -> None:
    with _lock:
        if len(_queue) >= MAX_QUEUE_SIZE:
            _queue.pop(0)
        _queue.append(item)


def get_review_queue() -> list[ReviewItem]:
    with _lock:
        return list(_queue)


def clear_review_queue() -> None:
    with _lock:
        _queue.clear()


def remove_from_review(item_id: str) -> bool:
    with _lock:
        for i, item in enumerate(_queue):
            if item.id == item_id:
                _queue.pop(i)
                return True
        return False
