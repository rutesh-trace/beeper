from datetime import datetime, UTC
from gettext import gettext

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from starlette import status

from app_logging import app_logger
from chats.models import ChatMessage, ChatConversation, MessageStatus
from chats.schemas import ChatMessageCreate
from db_domains.db_interface import DBInterface


class ChatService:
    """Handles chat-related database operations."""

    def store_chat_message(self, chat_data: ChatMessageCreate, source: str, senders_id: int) -> dict:
        """
        Stores a new chat message in the database. Creates a conversation if it doesn't exist.

        Args:
            chat_data (ChatMessageCreate): Chat message payload.
            source (str): Source of the message (e.g., "mobile", "web").\
            senders_id (int): ID of the sender of the message.

        Returns:
            dict: Stored chat message.
        """
        try:
            receiver_id = chat_data.get("receiver_id")

            # Check if a conversation exists between sender & receiver
            conversation_filter = [
                ((ChatConversation.sender_id == senders_id) & (ChatConversation.receiver_id == receiver_id)) |
                ((ChatConversation.sender_id == receiver_id) & (ChatConversation.receiver_id == senders_id))
            ]
            conversation_db_interface = DBInterface(ChatConversation)
            conversation = conversation_db_interface.read_by_fields(conversation_filter)

            if conversation:
                conversation_id = conversation.id  # Use existing conversation
            else:
                # Create a new conversation
                conversation_data = {
                    "sender_id": senders_id,
                    "receiver_id": receiver_id,
                    "last_message": chat_data.get("message"),
                    "last_message_time": datetime.now(UTC)
                }
                new_conversation = conversation_db_interface.create(conversation_data)
                conversation_id = new_conversation.get("id")

            # Prepare message data
            chat_data["sender_id"] = senders_id
            chat_data["conversation_id"] = conversation_id  # Ensure it's linked to a conversation
            chat_data["timestamp"] = datetime.now(UTC)
            chat_data["message_status"] = MessageStatus.SENT
            chat_data["source"] = source

            # Store message in DB
            message_db_interface = DBInterface(ChatMessage)
            new_chat = message_db_interface.create(chat_data)

            # Update conversation with last message
            conversation_db_interface.update(
                _id=conversation_id,
                data={
                    "last_message": chat_data.get("message"),
                    "last_message_time": datetime.now(UTC)
                }
            )

            return new_chat

        except SQLAlchemyError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error inserting chat message into the database."
            )

    def update_message_status(self, message_id: int, message_status: MessageStatus) -> dict:
        """
        Updates the status of a message (Sent, Delivered, Read, etc.).

        Args:
            message_id (int): ID of the message.
            message_status (MessageStatus): New status to be set.

        Returns:
            dict: Updated message details.
        """
        try:
            # Check if message exists
            message_filter = [ChatMessage.id == message_id]
            message = self.db_interface.read_by_fields(message_filter)

            if not message:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=gettext("message_not_found")
                )

            # Update status
            updated_message = self.db_interface.update(
                message_id, {"message_status": message_status}
            )
            return updated_message

        except SQLAlchemyError as err:
            app_logger.error(gettext("error_updating_data_to_db").format("Chat"))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=gettext("error_updating_data_to_db").format("Chat")
            )
