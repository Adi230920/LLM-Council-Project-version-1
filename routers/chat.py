import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from database import get_db, Chat, Message, User
from routers.auth import get_current_user
from models.schemas import ConsultRequest, DeliberationTrace
from services.orchestrator import run_deliberation
from services.provider_manager import ProviderManager
import json

logger = logging.getLogger("boule_ai.chat")
router = APIRouter(prefix="/chats", tags=["Chats"])

# Dependency for ProviderManager
async def get_manager() -> ProviderManager:
    manager = ProviderManager()
    try:
        yield manager
    finally:
        await manager.close()

@router.get("", response_model=List[dict])
async def list_chats(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Chat).where(Chat.user_id == current_user.id).order_by(Chat.created_at.desc())
    )
    chats = result.scalars().all()
    return [{"id": c.id, "title": c.title, "created_at": c.created_at} for c in chats]

@router.post("", response_model=dict)
async def create_chat(title: str = "New Conversation", db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_chat = Chat(user_id=current_user.id, title=title)
    db.add(new_chat)
    await db.commit()
    await db.refresh(new_chat)
    return {"id": new_chat.id, "title": new_chat.title}

@router.get("/{chat_id}", response_model=dict)
async def get_chat_history(chat_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Chat).options(selectinload(Chat.messages)).where(Chat.id == chat_id, Chat.user_id == current_user.id)
    )
    chat = result.scalars().first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    messages = []
    for m in chat.messages:
        messages.append({
            "role": m.role,
            "content": m.content,
            "deliberation_trace": m.deliberation_trace,
            "timestamp": m.timestamp
        })
    return {"id": chat.id, "title": chat.title, "messages": messages}

@router.post("/{chat_id}/message", response_model=DeliberationTrace)
async def send_message(
    chat_id: str,
    request: ConsultRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    manager: ProviderManager = Depends(get_manager)
):
    # 1. Verify Chat ownership
    result = await db.execute(select(Chat).where(Chat.id == chat_id, Chat.user_id == current_user.id))
    chat = result.scalars().first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # 2. Save User Message
    user_msg = Message(chat_id=chat_id, role="user", content=request.prompt)
    db.add(user_msg)
    
    # 3. If first message, update chat title
    if chat.title == "New Conversation":
        chat.title = request.prompt[:50] + ("..." if len(request.prompt) > 50 else "")
    
    # 4. Run Deliberation
    try:
        trace = await run_deliberation(request=request, provider_manager=manager)
        
        # 5. Save Assistant Message (Verdict only in content, trace in deliberation_trace)
        assistant_msg = Message(
            chat_id=chat_id,
            role="assistant",
            content=trace.verdict,
            deliberation_trace=trace.dict()
        )
        db.add(assistant_msg)
        
        await db.commit()
        return trace
    except Exception as exc:
        logger.exception("Council deliberation failed: %s", exc)
        await db.rollback()
        raise HTTPException(status_code=502, detail=f"Deliberation failed: {exc}")
