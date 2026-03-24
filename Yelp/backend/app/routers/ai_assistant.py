"""
AI Assistant router for chatbot interactions with persistent conversations.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import User, ChatConversation, ChatMessage
from app.schemas import (
    ChatRequest, ChatResponse, ConversationResponse,
    ConversationListItem, ChatMessageResponse
)
from app.services.auth import get_current_user
from app.ai_assistant.chatbot import RestaurantChatbot

router = APIRouter(prefix="/ai-assistant", tags=["AI Assistant"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process a chat message, persist to conversation, and return AI recommendations."""
    
    # Resolve or create conversation
    conversation = None
    if request.conversation_id:
        conversation = db.query(ChatConversation).filter(
            ChatConversation.id == request.conversation_id,
            ChatConversation.user_id == current_user.id
        ).first()
        if not conversation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    
    if not conversation:
        # Create new conversation with first message as title
        title = request.message[:80] + ("..." if len(request.message) > 80 else "")
        conversation = ChatConversation(user_id=current_user.id, title=title)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    
    # Save user message
    user_msg = ChatMessage(
        conversation_id=conversation.id,
        role='user',
        content=request.message
    )
    db.add(user_msg)
    db.commit()
    
    # Build conversation history from DB for context
    db_messages = db.query(ChatMessage).filter(
        ChatMessage.conversation_id == conversation.id
    ).order_by(ChatMessage.created_at).all()
    
    history = [{"role": m.role, "content": m.content} for m in db_messages[:-1]]  # exclude the message we just added
    
    # Run the AI pipeline
    chatbot = RestaurantChatbot(db)
    result = await chatbot.process_query(
        user_id=current_user.id,
        message=request.message,
        conversation_history=history
    )
    
    # Save assistant response
    assistant_msg = ChatMessage(
        conversation_id=conversation.id,
        role='assistant',
        content=result["message"],
        recommendations=[
            {"restaurant": rec["restaurant"], "reason": rec["reason"]}
            for rec in result.get("recommendations", [])
        ] if result.get("recommendations") else None
    )
    db.add(assistant_msg)
    
    # Update conversation timestamp
    from sqlalchemy.sql import func
    conversation.updated_at = func.current_timestamp()
    db.commit()
    
    return ChatResponse(
        message=result["message"],
        conversation_id=conversation.id,
        recommendations=result.get("recommendations", [])
    )


@router.get("/conversations", response_model=List[ConversationListItem])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all conversations for the current user, most recent first."""
    conversations = db.query(ChatConversation).filter(
        ChatConversation.user_id == current_user.id
    ).order_by(ChatConversation.updated_at.desc()).all()
    
    return [ConversationListItem.model_validate(c) for c in conversations]


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a conversation with all its messages."""
    conversation = db.query(ChatConversation).filter(
        ChatConversation.id == conversation_id,
        ChatConversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    
    return ConversationResponse.model_validate(conversation)


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a conversation and all its messages."""
    conversation = db.query(ChatConversation).filter(
        ChatConversation.id == conversation_id,
        ChatConversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    
    db.delete(conversation)
    db.commit()
