"""
admin_api.py
ADMIN API Routes — Full control over chats
Everything grouped under /admin/chats
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
from database import (
    get_messages_by_conversation,
    delete_messages_by_conversation
)
from database_Conv import (
    get_all_conversations_admin,
    get_conversation_by_id,
    search_conversations_by_label,
    archive_conversation,
    delete_conversation
)

router = APIRouter(prefix="/admin/chats", tags=["Admin - Chats"])


# ============================================
# GET: All chats (all users) with pagination
# ============================================

@router.get("")
async def admin_get_all_chats(
    user_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    page: int = 1,
    limit: int = 20
):
    """
    Get all chats across all users
    Filters: user_id, is_active (true/false)
    Supports pagination
    """
    try:
        chats, total = get_all_conversations_admin(
            user_id=user_id,
            is_active=is_active,
            page=page,
            limit=limit
        )

        for c in chats:
            if c.get('created_at'):
                c['created_at'] = str(c['created_at'])
            if c.get('updated_at'):
                c['updated_at'] = str(c['updated_at'])

        total_pages = (total + limit - 1) // limit

        return {
            "status": "success",
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "chats": chats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ============================================
# GET: Search chats by title
# ============================================

@router.get("/search")
async def admin_search_chats(keyword: str, page: int = 1, limit: int = 20):
    """
    Search chats by label/title keyword
    Example: /admin/chats/search?keyword=machine
    """
    try:
        if not keyword or len(keyword.strip()) < 1:
            raise HTTPException(status_code=400, detail="Keyword must not be empty")

        chats, total = search_conversations_by_label(
            keyword=keyword,
            page=page,
            limit=limit
        )

        for c in chats:
            if c.get('created_at'):
                c['created_at'] = str(c['created_at'])
            if c.get('updated_at'):
                c['updated_at'] = str(c['updated_at'])

        total_pages = (total + limit - 1) // limit

        return {
            "status": "success",
            "keyword": keyword,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "chats": chats
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ============================================
# GET: Chats by user_id
# ============================================

@router.get("/user/{user_id}")
async def admin_get_user_chats(user_id: str, page: int = 1, limit: int = 20):
    """Get all chats for a specific user"""
    try:
        chats, total = get_all_conversations_admin(
            user_id=user_id,
            page=page,
            limit=limit
        )

        for c in chats:
            if c.get('created_at'):
                c['created_at'] = str(c['created_at'])
            if c.get('updated_at'):
                c['updated_at'] = str(c['updated_at'])

        total_pages = (total + limit - 1) // limit

        return {
            "status": "success",
            "user_id": user_id,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "chats": chats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ============================================
# GET: Single chat + all its messages
# ============================================

@router.get("/{chat_id}")
async def admin_get_chat(chat_id: int):
    """
    Get a single chat with ALL its messages
    Returns chat details + messages in one response
    """
    try:
        # Get chat details
        chat = get_conversation_by_id(chat_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")

        # Convert datetime
        if chat.get('created_at'):
            chat['created_at'] = str(chat['created_at'])
        if chat.get('updated_at'):
            chat['updated_at'] = str(chat['updated_at'])

        # Get all messages of this chat
        messages = get_messages_by_conversation(chat_id)

        for m in messages:
            if m.get('created_at'):
                m['created_at'] = str(m['created_at'])

        return {
            "status": "success",
            "chat": chat,
            "total_messages": len(messages),
            "messages": messages
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ============================================
# DELETE: All messages in a chat (keep the chat)
# ============================================

@router.delete("/{chat_id}/messages")
async def admin_delete_chat_messages(chat_id: int):
    """
    Delete ALL messages inside a chat
    The chat itself stays — only messages are removed
    """
    try:
        chat = get_conversation_by_id(chat_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")

        deleted_count = delete_messages_by_conversation(chat_id)

        return {
            "status": "success",
            "message": "All messages deleted",
            "chat_id": chat_id,
            "deleted_count": deleted_count
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ============================================
# PUT: Archive a chat
# ============================================

@router.put("/{chat_id}/archive")
async def admin_archive_chat(chat_id: int):
    """Archive a chat — sets is_active = FALSE"""
    try:
        chat = get_conversation_by_id(chat_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")

        success = archive_conversation(chat_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to archive")

        return {
            "status": "success",
            "message": "Chat archived",
            "chat_id": chat_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ============================================
# DELETE: Chat + all its messages permanently
# ============================================

@router.delete("/{chat_id}")
async def admin_delete_chat(chat_id: int):
    """
    Permanently delete a chat AND all its messages
    Cannot be undone
    """
    try:
        chat = get_conversation_by_id(chat_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")

        # Delete messages first
        delete_messages_by_conversation(chat_id)

        # Then delete the chat
        success = delete_conversation(chat_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete chat")

        return {
            "status": "success",
            "message": "Chat and all messages permanently deleted",
            "chat_id": chat_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")