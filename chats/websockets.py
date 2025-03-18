import socketio
from fastapi import HTTPException
import asyncio

from app_logging import get_logger
from chats.schemas import ChatMessageCreate
from chats.service import ChatService
from common.utils import save_base64_image, save_base64_video, save_base64_audio, is_webm, convert_webm_to_mp3
from config import app_config
import asyncio

logger = get_logger()

# Create a global Socket.IO server instance
sio = socketio.AsyncServer(cors_allowed_origins='*', async_mode='asgi', max_http_buffer_size=1_000_000_000)

connected_users = {}  # Store connected users
user_details = {}  # Store user IDs and their socket session IDs


@sio.on("connect")
async def connect(sid, env):
    """Handles new client connections."""
    connected_users[sid] = env
    await sio.emit("send_msg", "Hello from Server", room=sid)


@sio.on("disconnect")
async def disconnect(sid):
    """Handles client disconnections and removes user mapping."""
    user_id_to_remove = None
    for user_id, user_sid in user_details.items():
        if user_sid == sid:
            user_id_to_remove = user_id
            break
    if user_id_to_remove:
        del user_details[user_id_to_remove]


@sio.on("register_user")
async def register_user(sid, data):
    """Registers a user ID with a socket session ID."""
    user_id = data.get("user_id")
    if user_id:
        user_details[user_id] = sid


async def store_and_send_message(sender_id, receiver_id, message, message_type):
    """
    Generic function to store a message in the database and send it to the recipient if online.
    """
    chat_data = ChatMessageCreate(
        receiver_id=receiver_id,
        message=message,
        sender_id=sender_id
    )
    chat_service = ChatService()

    try:
        chat_service.store_chat_message(
            chat_data=chat_data,
            source="app",
            senders_id=sender_id
        )

        # Send message to recipient if they are online
        target_sid = user_details.get(receiver_id)
        if target_sid:
            payload = {"senderID": sender_id, "message": None}  # Default structure

            if message_type == "text":
                payload["message"] = message
            elif message_type in ["image", "video", "audio"]:
                payload["message"] = None
                payload[message_type] = message  # Dynamically add the correct key
            await sio.emit("receive_msg", payload, to=target_sid)


    except HTTPException as e:
        print(e)
    except Exception as e:
        print(e)


async def handle_text_message(sender_id, receiver_id, message_text):
    """
        Processes and stores a text message.

        This function:
        - Validates input parameters.
        - Stores the message and sends it to the receiver.
        - Emits errors via Socket.IO if an issue occurs.

        Parameters:
        - sender_id (int/str): The ID of the message sender.
        - receiver_id (int/str): The ID of the message recipient.
        - message_text (str): The text content of the message.

        Emits:
        - "error" (dict): Sends an error message if processing fails.
    """

    if not sender_id or not receiver_id:
        error_msg = "Missing required fields: 'sender_id' or 'receiver_id'."
        logger.warning(error_msg)
        await sio.emit("error", {"error": error_msg})
        return

    if not message_text.strip():
        error_msg = "Message text is empty."
        logger.warning(error_msg)
        await sio.emit("error", {"error": error_msg})
        return

    try:
        # Store and send the text message
        await store_and_send_message(sender_id, receiver_id, message_text, "text")
        logger.info(f"Text message sent from {sender_id} to {receiver_id}: {message_text}")

    except Exception as e:
        error_msg = f"Unexpected error in handle_text_message: {str(e)}"
        logger.critical(error_msg, exc_info=True)
        await sio.emit("error", {"error": error_msg})


async def handle_image_message(sender_id, receiver_id, base64_image, file_name):
    """
        Processes and stores an image message.

        This function:
        - Validates input parameters.
        - Saves the base64-encoded image to a storage system.
        - Stores the message and sends it to the receiver.
        - Emits errors via Socket.IO if an issue occurs.

        Parameters:
        - sender_id (int/str): The ID of the message sender.
        - receiver_id (int/str): The ID of the message recipient.
        - base64_image (str): Base64-encoded image data.
        - file_name (str): Name of the image file.

        Emits:
        - "error" (dict): Sends an error message if processing fails.
    """

    if not sender_id or not receiver_id:
        error_msg = "Missing required fields: 'sender_id' or 'receiver_id'."
        logger.warning(error_msg)
        await sio.emit("error", {"error": error_msg})
        return

    if not base64_image:
        error_msg = "Image data is missing."
        logger.warning(error_msg)
        await sio.emit("error", {"error": error_msg})
        return

    try:
        # Attempt to save the image file
        image_urls = await save_base64_image({
            "image": base64_image,
            "file_name": file_name,
            "senderID": sender_id,
            "receiverID": receiver_id
        })

        cdn_url = image_urls.get("cdn_url")
        if not cdn_url:
            raise ValueError("CDN URL not returned from save_base64_image")

        # Store message and send to recipient
        await store_and_send_message(sender_id, receiver_id, cdn_url, "image")

        logger.info(f"Image message processed successfully from {sender_id} to {receiver_id}")

    except ValueError as ve:
        error_msg = f"Invalid image data: {str(ve)}"
        logger.error(error_msg)
        await sio.emit("error", {"error": error_msg})

    except Exception as e:
        error_msg = f"Unexpected error in handle_image_message: {str(e)}"
        logger.critical(error_msg, exc_info=True)
        await sio.emit("error", {"error": error_msg})


async def handle_video_message(sender_id, receiver_id, base64_video, file_name):
    """
        Processes and stores a video message.

        This function:
        - Validates input parameters.
        - Saves the base64-encoded video to a storage system.
        - Stores the message and sends it to the receiver.
        - Emits errors via Socket.IO if an issue occurs.

        Parameters:
        - sender_id (int/str): The ID of the message sender.
        - receiver_id (int/str): The ID of the message recipient.
        - base64_video (str): Base64-encoded video data.
        - file_name (str): Name of the video file.

        Emits:
        - "error" (dict): Sends an error message if processing fails.
    """

    if not sender_id or not receiver_id:
        error_msg = "Missing required fields: 'sender_id' or 'receiver_id'."
        logger.warning(error_msg)
        await sio.emit("error", {"error": error_msg})
        return

    if not base64_video:
        error_msg = "Video data is missing."
        logger.warning(error_msg)
        await sio.emit("error", {"error": error_msg})
        return

    try:
        # Attempt to save the video file
        video_urls = await save_base64_video({
            "video": base64_video,
            "file_name": file_name,
            "senderID": sender_id,
            "receiverID": receiver_id
        })

        cdn_url = video_urls.get("cdn_url")
        if not cdn_url:
            raise ValueError("CDN URL not returned from save_base64_video")

        # Store message and send to recipient
        await store_and_send_message(sender_id, receiver_id, cdn_url, "video")

        logger.info(f"Video message processed successfully from {sender_id} to {receiver_id}")

    except ValueError as ve:
        error_msg = f"Invalid video data: {str(ve)}"
        logger.error(error_msg)
        await sio.emit("error", {"error": error_msg})

    except Exception as e:
        error_msg = f"Unexpected error in handle_video_message: {str(e)}"
        logger.critical(error_msg, exc_info=True)
        await sio.emit("error", {"error": error_msg})


async def handle_audio_message(sender_id, receiver_id, base64_audio, file_name):
    """
        Processes and stores an audio message.

        This function:
        - Validates input parameters.
        - Saves the base64-encoded audio file to a storage system.
        - Stores the message and sends it to the receiver.
        - Emits errors via Socket.IO if an issue occurs.

        Parameters:
        - sender_id (int/str): The ID of the message sender.
        - receiver_id (int/str): The ID of the message recipient.
        - base64_audio (str): Base64-encoded audio data.
        - file_name (str): Name of the audio file.

        Emits:
        - "error" (dict): Sends an error message if processing fails.
    """

    if not sender_id or not receiver_id:
        error_msg = "Missing required fields: 'sender_id' or 'receiver_id'."
        logger.warning(error_msg)
        await sio.emit("error", {"error": error_msg})
        return

    if not base64_audio:
        error_msg = "Audio data is missing."
        logger.warning(error_msg)
        await sio.emit("error", {"error": error_msg})
        return

    try:
        # Attempt to save the audio file
        audio_urls = await save_base64_audio({
            "audio": base64_audio,
            "file_name": file_name,
            "senderID": sender_id,
            "receiverID": receiver_id
        })

        cdn_url = audio_urls.get("cdn_url")
        if not cdn_url:
            raise ValueError("CDN URL not returned from save_base64_audio")

        # Store message and send to recipient
        await store_and_send_message(sender_id=sender_id, receiver_id=receiver_id,
                                     message=cdn_url, message_type="audio")

        logger.info(f"Audio message processed successfully from {sender_id} to {receiver_id}")

    except ValueError as ve:
        error_msg = f"Invalid audio data: {str(ve)}"
        logger.error(error_msg)
        await sio.emit("error", {"error": error_msg})

    except Exception as e:
        error_msg = f"Unexpected error in handle_audio_message: {str(e)}"
        logger.critical(error_msg, exc_info=True)
        await sio.emit("error", {"error": error_msg})


@sio.on("msg")
async def send_message_to_client(sid, data):
    """
    Processes and handles text, image, video, and audio messages received from a client.

    This function:
    - Validates required fields (`senderID`, `user_id`).
    - Handles text messages asynchronously.
    - Processes file messages (image, video, audio).
    - Converts WebM audio files to MP3 before processing.
    - Executes all tasks concurrently for improved performance.
    - Sends error responses to the client via Socket.IO if issues occur.

    Expected Input:
    - `senderID` (int/str): The message sender's ID.
    - `user_id` (int/str): The message recipient's ID.
    - `message` (str, optional): Text message content.
    - `file_name` (str, optional): File name.
    - `file_type` (str, optional): File type ('image', 'video', 'audio').
    - `binary_data` (bytes, optional): File content.

    Emits:
    - "error" (dict): Sends an error response if processing fails.

    Error Handling:
    - Sends relevant errors to the client via Socket.IO.
    - Logs errors for debugging.
    """

    try:
        sender_id = data.get("senderID")
        receiver_id = data.get("user_id")
        message_text = data.get("message", "").strip()
        file_name = data.get("file_name")
        file_type = data.get("file_type")
        files_binary_data = data.get("binary_data")

        # Validate sender and receiver IDs
        if not sender_id or not receiver_id:
            error_msg = "Missing required fields: 'senderID' or 'user_id'."
            logger.warning(error_msg)
            await sio.emit("error", {"error": error_msg}, to=sid)
            return

        tasks = []

        # Handle text message asynchronously
        if message_text:
            try:
                tasks.append(handle_text_message(sender_id, receiver_id, message_text))
                logger.info(f"Processing text message from {sender_id} to {receiver_id}")
            except Exception as e:
                error_msg = f"Failed to process text message: {str(e)}"
                logger.error(error_msg, exc_info=True)
                await sio.emit("error", {"error": error_msg}, to=sid)

        # Dictionary-based dispatch for file processing
        file_handlers = {
            "image": handle_image_message,
            "video": handle_video_message,
            "audio": handle_audio_message
        }

        # Process file message (if applicable)
        if file_type in file_handlers and files_binary_data:
            try:
                logger.info(f"Processing {file_type} message from {sender_id} to {receiver_id}")

                # Special case: Convert WebM to MP3 for audio messages
                if file_type == "audio" and is_webm(files_binary_data):
                    split_file_name = file_name.rsplit(".", 1)[0]
                    new_file_name = f"{split_file_name}.mp3"
                    audio_data = await convert_webm_to_mp3(files_binary_data)
                else:
                    new_file_name, audio_data = file_name, files_binary_data

                tasks.append(file_handlers[file_type](sender_id, receiver_id, audio_data, new_file_name))
            except Exception as e:
                error_msg = f"Failed to process {file_type} message: {str(e)}"
                logger.error(error_msg, exc_info=True)
                await sio.emit("error", {"error": error_msg}, to=sid)

        # Execute all tasks concurrently
        if tasks:
            await asyncio.gather(*tasks)

    except Exception as e:
        error_msg = f"Unexpected error in send_message_to_client: {str(e)}"
        logger.critical(error_msg, exc_info=True)
        await sio.emit("error", {"error": error_msg}, to=sid)


@sio.on("fetch_chat_history")
async def fetch_chat_history(sid, data):
    """
        Fetches and sends the chat history between a sender and receiver.

        This function retrieves all messages exchanged between `user_id` (sender)
        and `receiver_id` (recipient) and emits the result back to the requesting client.

        Expected Input (from client):
        - `user_id` (int/str): The sender's unique identifier.
        - `receiver_id` (int/str): The recipient's unique identifier.

        Emits:
        - "chat_history": A list of chat messages if successful.
        - "error": An error message if fetching fails.

        Error Handling:
        - If required parameters are missing, an appropriate error is emitted.
        - Any unexpected exception is caught and logged to avoid crashing the server.
    """

    sender_id = data.get("user_id")
    receiver_id = data.get("receiver_id")

    # Validate required parameters
    if not sender_id or not receiver_id:
        error_message = "Missing required parameters: 'user_id' or 'receiver_id'."
        logger.error(error_message)
        await sio.emit("error", {"error": error_message}, to=sid)
        return

    try:
        # Fetch chat history
        chat_service = ChatService()
        chat_history = chat_service.get_chat_history(sender_id, receiver_id)

        # Send the chat history back to the client
        await sio.emit("chat_history", chat_history, to=sid)
        logger.info(f"Chat history fetched successfully for sender {sender_id} and receiver {receiver_id}")

    except Exception as e:
        error_message = f"Unexpected error fetching chat history: {e}"
        logger.exception(error_message)  # Logs full traceback for debugging
        await sio.emit("error", {"error": "An unexpected error occurred. Please try again later."}, to=sid)


# Export `sio` instance
socket_app = socketio.ASGIApp(sio)
