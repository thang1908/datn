"""MongoDB client and CRUD utilities."""

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorClient

from src.core.config import settings

logger = logging.getLogger(__name__)

_db_client: Optional[AsyncIOMotorClient] = None


async def get_db():
    """Get MongoDB database client."""
    global _db_client
    if _db_client is None:
        try:
            _db_client = AsyncIOMotorClient(
                settings.mongodb_uri,
                serverSelectionTimeoutMS=settings.mongodb_timeout_ms,
            )
            # Test connection
            await _db_client.admin.command("ping")
            logger.info("MongoDB connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    return _db_client[settings.mongodb_db_name]


async def close_db() -> None:
    """Close MongoDB connection."""
    global _db_client
    if _db_client is not None:
        await _db_client.aclose()
        _db_client = None
        logger.info("MongoDB connection closed")


async def save_conversation(
    message_id: str,
    crm_output: dict[str, Any],
    call_id: Optional[str] = None,
    direction: Optional[int] = None,
) -> dict[str, Any]:
    """Save pipeline result to MongoDB.

    The output fields are stored flat at the document top level.
    Internal fields ``_id``, ``call_id``, ``direction``, ``created_at``,
    ``updated_at`` are added alongside the PascalCase result fields.
    """
    db = await get_db()
    document = {
        "_id": message_id,
        "call_id": call_id,
        "direction": direction,
        **crm_output,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    await db[settings.mongodb_collection_calls].replace_one(
        {"_id": message_id}, document, upsert=True
    )
    logger.debug(f"Saved conversation {message_id} to MongoDB")
    return document


async def get_conversation(message_id: str) -> Optional[dict[str, Any]]:
    """Retrieve a pipeline result from MongoDB by message_id."""
    db = await get_db()
    doc = await db[settings.mongodb_collection_calls].find_one({"_id": message_id})
    if doc:
        logger.debug(f"Retrieved conversation {message_id} from MongoDB")
    else:
        logger.debug(f"Conversation {message_id} not found in MongoDB")
    return doc


async def list_conversations(
    limit: int = 20,
    skip: int = 0,
) -> list[dict[str, Any]]:
    """List recent pipeline results from MongoDB."""
    db = await get_db()

    docs = (
        await db[settings.mongodb_collection_calls]
        .find()
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
        .to_list(limit)
    )
    logger.debug(f"Retrieved {len(docs)} conversations from MongoDB")
    return docs


async def delete_conversation(message_id: str) -> bool:
    """Delete a conversation from MongoDB by message_id.

    Returns True if deleted, False if not found.
    """
    db = await get_db()
    result = await db[settings.mongodb_collection_calls].delete_one({"_id": message_id})
    deleted = result.deleted_count > 0
    if deleted:
        logger.info(f"Deleted conversation {message_id}")
    else:
        logger.debug(f"Conversation {message_id} not found for deletion")
    return deleted


_ALLOWED_UPDATE_FIELDS = {
    "CaseType",
    "Resolved",
    "IsNegative",
    "Summary",
    "NegativeReasonCode",
    "NegativeReasonDescription",
}


async def update_conversation(
    message_id: str,
    updates: dict[str, Any],
) -> Optional[dict[str, Any]]:
    """Partially update allowed fields of a conversation.

    Only fields in ``_ALLOWED_UPDATE_FIELDS`` are accepted.
    Returns the updated document, or None if not found.
    """
    safe = {k: v for k, v in updates.items() if k in _ALLOWED_UPDATE_FIELDS}
    if not safe:
        raise ValueError(f"No valid fields to update. Allowed: {_ALLOWED_UPDATE_FIELDS}")

    safe["updated_at"] = datetime.now(timezone.utc)

    db = await get_db()
    doc = await db[settings.mongodb_collection_calls].find_one_and_update(
        {"_id": message_id},
        {"$set": safe},
        return_document=True,
    )
    if doc:
        logger.info(f"Updated conversation {message_id}: {list(safe.keys())}")
    else:
        logger.debug(f"Conversation {message_id} not found for update")
    return doc

