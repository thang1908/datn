"""Conversation result retrieval routes."""

import logging
import re
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from src.db import delete_conversation, get_conversation, list_conversations, update_conversation

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/conversations", tags=["conversations"])


# ── Schema ────────────────────────────────────────────────────────────────────

class ConversationUpdate(BaseModel):
    """Các trường được phép cập nhật thủ công."""

    CaseType: Optional[str] = None
    Resolved: Optional[str] = None
    IsNegative: Optional[str] = None
    Summary: Optional[str] = None
    NegativeReasonCode: Optional[list[str]] = None
    NegativeReasonDescription: Optional[list[str]] = None

    @field_validator("NegativeReasonCode", "NegativeReasonDescription", mode="before")
    @classmethod
    def normalize_list_field(cls, value):
        """Accept textarea strings from the UI but store Mongo values as lists."""
        if value is None or isinstance(value, list):
            return value
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return []
            return [part.strip() for part in re.split(r"[\n,;]+", text) if part.strip()]
        return value


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("")
async def list_conversation_results(
    limit: int = 20,
    skip: int = 0,
) -> dict:
    """
    List recent conversation results.

    Parameters:
    - limit: Number of results to return (default: 20)
    - skip: Number of results to skip (default: 0)
    """
    results = await list_conversations(limit=limit, skip=skip)
    return {
        "total": len(results),
        "limit": limit,
        "skip": skip,
        "results": results,
    }


@router.get("/{message_id}")
async def get_conversation_result(message_id: str) -> dict:
    """Retrieve a stored pipeline result from MongoDB by message_id."""
    result = await get_conversation(message_id)
    if not result:
        raise HTTPException(
            status_code=404, detail=f"Conversation {message_id} not found"
        )
    return result


@router.patch("/{message_id}")
async def update_conversation_result(
    message_id: str,
    body: ConversationUpdate,
) -> dict:
    """
    Cập nhật thủ công một số trường của conversation.

    Chỉ các trường sau được phép sửa:
    ``CaseType``, ``Resolved``, ``IsNegative``, ``Summary``,
    ``NegativeReasonCode``, ``NegativeReasonDescription``.
    """
    # Bỏ None — chỉ giữ trường người dùng thực sự muốn cập nhật
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=422, detail="Không có trường nào được cung cấp để cập nhật.")

    try:
        updated = await update_conversation(message_id, updates)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if not updated:
        raise HTTPException(
            status_code=404, detail=f"Conversation {message_id} not found"
        )
    return updated


@router.delete("/{message_id}")
async def delete_conversation_result(message_id: str) -> dict:
    """Xóa một conversation khỏi MongoDB theo message_id."""
    deleted = await delete_conversation(message_id)
    if not deleted:
        raise HTTPException(
            status_code=404, detail=f"Conversation {message_id} not found"
        )
    return {"success": True, "deleted_id": message_id}
