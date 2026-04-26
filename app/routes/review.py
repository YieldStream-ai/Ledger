from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.validation.review_queue import (
    ReviewItem,
    get_review_queue,
    clear_review_queue,
    remove_from_review,
)

router = APIRouter(prefix="/review", tags=["review"])


@router.get("/queue", response_model=list[ReviewItem])
async def list_review_queue():
    return get_review_queue()


@router.delete("/queue")
async def clear_queue():
    clear_review_queue()
    return {"status": "cleared"}


@router.delete("/queue/{item_id}")
async def remove_queue_item(item_id: str):
    removed = remove_from_review(item_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"status": "removed"}
