# Enum for message status
import enum

from sqlalchemy import Column, ForeignKey, Integer, DateTime, String, func, UniqueConstraint, Enum

from db_domains import CreateUpdateTime


class MessageStatus(str, enum.Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class ChatConversation(CreateUpdateTime):
    __tablename__ = "chat_conversations"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"))  # One of the users
    receiver_id = Column(Integer, ForeignKey("users.id"))  # Other user in the chat
    last_message = Column(String, nullable=True)  # Store preview of last message
    last_message_time = Column(DateTime, default=func.now(), onupdate=func.now())  # Updates when a new message arrives

    # Ensure a unique conversation exists between two users
    __table_args__ = (UniqueConstraint('sender_id', 'receiver_id', name='unique_chat_users'),)


class ChatMessage(CreateUpdateTime):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("chat_conversations.id"))  # Links message to conversation
    sender_id = Column(Integer, ForeignKey("users.id"))
    receiver_id = Column(Integer, ForeignKey("users.id"))
    message = Column(String, nullable=False)  # Message content
    timestamp = Column(DateTime, default=func.now())  # Time when message was sent
    message_status = Column(Enum(MessageStatus), default=MessageStatus.SENT)  # Message delivery status
    source = Column(String)
