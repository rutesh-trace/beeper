from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from chats.models import MessageStatus


# Schema for sending a new chat message
class ChatMessageCreate(BaseModel):
    conversation_id: int
    sender_id: int
    receiver_id: int
    message: str

    class Config:
        orm_mode = True


# Schema for reading chat messages (response)
class ChatMessageResponse(BaseModel):
    id: int
    conversation_id: int
    sender_id: int
    receiver_id: int
    message: str
    timestamp: datetime
    message_status: MessageStatus
    source: str

    class Config:
        orm_mode = True


# Schema for creating a new chat conversation
class ChatConversationCreate(BaseModel):
    sender_id: int
    receiver_id: int

    class Config:
        orm_mode = True


# Schema for retrieving chat conversations (response)
class ChatConversationResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    last_message: Optional[str]
    last_message_time: datetime

    class Config:
        orm_mode = True
