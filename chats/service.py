from datetime import datetime, UTC
from gettext import gettext
from typing import Dict, Optional

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
            receiver_id = chat_data.receiver_id

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
                    "last_message": chat_data.message,
                    "last_message_time": datetime.now(UTC)
                }
                new_conversation = conversation_db_interface.create(conversation_data)
                conversation_id = new_conversation.get("id")

            # Prepare message data
            chat_data = chat_data.model_dump()
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
            message_db_interface = DBInterface(ChatMessage)
            message = message_db_interface.read_by_fields(message_filter)

            if not message:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=gettext("message_not_found")
                )

            # Update status
            updated_message = message_db_interface.update(
                str(message_id), {"message_status": message_status}
            )
            return updated_message

        except SQLAlchemyError as err:
            app_logger.error(gettext("error_updating_data_to_db").format("Chat"))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=gettext("error_updating_data_to_db").format("Chat")
            )

    def categorize_message(self, message_text: str) -> Dict[str, Optional[str]]:
        """
        Categorizes a message into image, video, audio, or text.

        Args:
            message_text (str): The message string to be categorized.

        Returns:
            dict: Dictionary with categorized message fields.
        """
        # Default values
        image = None
        video = None
        audio = None
        text_message = None

        # Check if the message is a URL containing media type keywords
        parts = message_text.split("/")
        if "chat_videos" in parts:
            video = message_text
        elif "chat_images" in parts:
            image = message_text
        elif "chat_audio" in parts:
            audio = message_text
        else:
            text_message = message_text

        return {
            "message": text_message,
            "image": image,
            "video": video,
            "audio": audio,
        }

    def get_chat_history(self, sender_id: int, receiver_id: int):
        """
        Fetches chat history between two users, ordered by timestamp.

        Args:
            sender_id (int): The ID of the sender.
            receiver_id (int): The ID of the receiver.

        Returns:
            list[dict]: A list of chat messages in dictionary format.
        """
        try:
            # Find the conversation between sender and receiver
            conversation_filter = [
                ((ChatConversation.sender_id == sender_id) & (ChatConversation.receiver_id == receiver_id)) |
                ((ChatConversation.sender_id == receiver_id) & (ChatConversation.receiver_id == sender_id))
            ]
            conversation_db_interface = DBInterface(ChatConversation)
            conversation = conversation_db_interface.read_by_fields(conversation_filter)
            if not conversation:
                return []  # No conversation found, return empty list

            conversation_id = conversation.id

            # Fetch messages for the conversation
            message_filter = [ChatMessage.conversation_id == conversation_id]
            message_db_interface = DBInterface(ChatMessage)
            messages = message_db_interface.read_all_by_fields(
                filters=message_filter, order_by=ChatMessage.timestamp.asc()
            )

            # Convert messages to a structured format
            chat_history = []
            for msg in messages:
                categorized_data = self.categorize_message(message_text=msg.message)
                chat_history.append({
                    "id": msg.id,
                    "sender_id": msg.sender_id,
                    "receiver_id": msg.receiver_id,
                    **categorized_data,
                    "timestamp": msg.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "message_status": msg.message_status.value,
                })

            return chat_history

        except SQLAlchemyError as e:
            app_logger.error(f"Error fetching chat history: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving chat history."
            )
