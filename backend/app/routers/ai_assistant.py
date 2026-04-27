"""
AI Assistant router for chatbot interactions with persistent conversations.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.models import to_str_id, USERS
from typing import List
from app.database import get_db
from app.schemas import (
    ChatRequest, ChatResponse, ConversationResponse,
    ConversationListItem, ChatMessageResponse
)
from app.services.auth import get_current_user
from app.ai_assistant.chatbot import RestaurantChatbot
from datetime import datetime
from bson import ObjectId

router = APIRouter(prefix="/ai-assistant", tags=["AI Assistant"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """Process a chat message, persist to conversation, and return AI recommendations."""

    # Resolve or create conversation
    conversation = None
    if request.conversation_id:
        conversation = await db.chat_conversations.find_one({
            "_id": ObjectId(request.conversation_id),
            "user_id": ObjectId(current_user["id"])
        })
        if not conversation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    if not conversation:
        title = request.message[:80] + ("..." if len(request.message) > 80 else "")
        conversation = {
            "user_id": ObjectId(current_user["id"]),
            "title": title,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        result = await db.chat_conversations.insert_one(conversation)
        conversation["_id"] = result.inserted_id

    # Save user message
    user_msg = {
        "conversation_id": conversation["_id"],
        "role": "user",
        "content": request.message,
        "created_at": datetime.utcnow()
    }
    await db.chat_messages.insert_one(user_msg)

    # Build conversation history for context
    db_messages = await db.chat_messages.find(
        {"conversation_id": conversation["_id"]}
    ).sort("created_at", 1).to_list(None)
    history = [{"role": m["role"], "content": m["content"]} for m in db_messages[:-1]]

    # Run the AI pipeline
    chatbot = RestaurantChatbot(db)
    result = await chatbot.process_query(
        user_id=ObjectId(current_user["id"]),
        message=request.message,
        conversation_history=history
    )

    # Save assistant response
    assistant_msg = {
        "conversation_id": conversation["_id"],
        "role": "assistant",
        "content": result["message"],
        "recommendations": [
            {"restaurant": rec["restaurant"], "reason": rec["reason"]}
            for rec in result.get("recommendations", [])
        ] if result.get("recommendations") else None,
        "created_at": datetime.utcnow()
    }
    await db.chat_messages.insert_one(assistant_msg)

    # Update conversation timestamp
    await db.chat_conversations.update_one(
        {"_id": conversation["_id"]},
        {"$set": {"updated_at": datetime.utcnow()}}
    )

    return ChatResponse(
        message=result["message"],
        conversation_id=str(conversation["_id"]),
        recommendations=result.get("recommendations", [])
    )


@router.get("/conversations", response_model=List[ConversationListItem])
async def list_conversations(
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """List all conversations for the current user, most recent first."""
    conversations = await db.chat_conversations.find(
        {"user_id": ObjectId(current_user["id"])}
    ).sort("updated_at", -1).to_list(None)
    return [ConversationListItem.model_validate(to_str_id(c)) for c in conversations]


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """Get a conversation with all its messages."""
    conversation = await db.chat_conversations.find_one({
        "_id": ObjectId(conversation_id),
        "user_id": ObjectId(current_user["id"])
    })
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    messages = await db.chat_messages.find(
        {"conversation_id": ObjectId(conversation_id)}
    ).sort("created_at", 1).to_list(None)
    conversation["messages"] = [to_str_id(m) for m in messages]
    return ConversationResponse.model_validate(to_str_id(conversation))


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """Delete a conversation and all its messages."""
    conversation = await db.chat_conversations.find_one({
        "_id": ObjectId(conversation_id),
        "user_id": ObjectId(current_user["id"])
    })
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    await db.chat_messages.delete_many({"conversation_id": ObjectId(conversation_id)})
    await db.chat_conversations.delete_one({"_id": ObjectId(conversation_id)})