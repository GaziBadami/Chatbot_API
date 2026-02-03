"""
api.py
FRONTEND API Routes — Sidebar chat management
All routes under /conversations
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import get_messages_by_conversation, delete_messages_by_conversation
from database_Conv import (
    get_all_conversations,
    get_conversation_by_id,
    create_conversation,
    switch_conversation,
    update_conversation_label,
    archive_conversation,
    delete_conversation
)

router = APIRouter(prefix="/conversations", tags=["Frontend - Conversations"])


# ============================================
# REQUEST MODELS
# ============================================

class CreateConversationRequest(BaseModel):
    user_id: str
    label: Optional[str] = "New Chat"

class RenameConversationRequest(BaseModel):
    label: str

class SwitchConversationRequest(BaseModel):
    user_id: str


# ============================================
# GET: List all chats (sidebar)
# ============================================

@router.get("/{user_id}")
async def list_conversations(user_id: str, limit: int = 50):
    """
    Get all conversations for a user
    Frontend uses this to populate the sidebar
    Returns: label, last message preview, message count, is_active
    """
    try:
        conversations = get_all_conversations(user_id, limit)

        # Convert datetime objects to strings for JSON
        for c in conversations:
            if c.get('created_at'):
                c['created_at'] = str(c['created_at'])
            if c.get('updated_at'):
                c['updated_at'] = str(c['updated_at'])

        return {
            "status": "success",
            "user_id": user_id,
            "total": len(conversations),
            "conversations": conversations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ============================================
# POST: Create new chat
# ============================================

@router.post("/create")
async def create_new_conversation(request: CreateConversationRequest):
    """
    Create a new chat
    Deactivates the current active chat automatically
    """
    try:
        new_conv = create_conversation(
            user_id=request.user_id,
            label=request.label
        )

        if not new_conv:
            raise HTTPException(status_code=500, detail="Failed to create conversation")

        # Convert datetime
        if new_conv.get('created_at'):
            new_conv['created_at'] = str(new_conv['created_at'])
        if new_conv.get('updated_at'):
            new_conv['updated_at'] = str(new_conv['updated_at'])

        return {
            "status": "success",
            "message": "New chat created",
            "conversation": new_conv
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ============================================
# GET: Load messages of a specific chat
# ============================================

@router.get("/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: int, limit: int = 100):
    """
    Load all messages when user clicks a chat in sidebar
    Returns messages in chronological order (oldest first)
    """
    try:
        # Verify conversation exists
        conversation = get_conversation_by_id(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Chat not found")

        messages = get_messages_by_conversation(conversation_id, limit)

        # Convert datetime objects
        for m in messages:
            if m.get('created_at'):
                m['created_at'] = str(m['created_at'])

        return {
            "status": "success",
            "conversation_id": conversation_id,
            "total_messages": len(messages),
            "messages": messages
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ============================================
# PUT: Rename a chat
# ============================================

@router.put("/{conversation_id}/label")
async def rename_conversation(conversation_id: int, request: RenameConversationRequest):
    """
    Rename a chat from sidebar (user edits the title)
    """
    try:
        conversation = get_conversation_by_id(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Chat not found")

        success = update_conversation_label(conversation_id, request.label)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to rename")

        return {
            "status": "success",
            "message": "Chat renamed",
            "conversation_id": conversation_id,
            "new_label": request.label
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ============================================
# PUT: Switch to a different chat (sidebar click)
# ============================================

@router.put("/{conversation_id}/switch")
async def switch_chat(conversation_id: int, request: SwitchConversationRequest):
    """
    User clicks an old chat in sidebar
    → Sets that chat as active
    → Next messages will go into this chat
    """
    try:
        conversation = get_conversation_by_id(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Chat not found")

        # Verify this conversation belongs to the user
        if conversation['user_id'] != request.user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        success = switch_conversation(request.user_id, conversation_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to switch chat")

        return {
            "status": "success",
            "message": "Switched to chat",
            "conversation_id": conversation_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ============================================
# PUT: Archive a chat
# ============================================

@router.put("/{conversation_id}/archive")
async def archive_chat(conversation_id: int):
    """
    Archive/close a chat
    Chat stays in sidebar but marked as inactive
    """
    try:
        conversation = get_conversation_by_id(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Chat not found")

        success = archive_conversation(conversation_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to archive")

        return {
            "status": "success",
            "message": "Chat archived",
            "conversation_id": conversation_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ============================================
# DELETE: Delete a chat + all its messages
# ============================================

@router.delete("/{conversation_id}")
async def delete_chat(conversation_id: int):
    """
    Delete a chat and ALL its messages permanently
    Cannot be undone
    """
    try:
        conversation = get_conversation_by_id(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Chat not found")

        # Delete all messages first
        delete_messages_by_conversation(conversation_id)

        # Then delete the conversation
        success = delete_conversation(conversation_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete chat")

        return {
            "status": "success",
            "message": "Chat and all messages deleted",
            "conversation_id": conversation_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")