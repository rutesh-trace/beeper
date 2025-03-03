import io
import json
import base64
from datetime import datetime
from fastapi import UploadFile, APIRouter
from chats.service import ChatService
from common.utils import save_uploaded_image
from chats.websockets import connection_manager  # Import existing connection manager
from main import sio

connected_users = {}  # Store user_id -> socket session ID


@sio.on("register_user")
async def register_user(sid, data):
    user_id = data.get("user_id")
    if user_id:
        connected_users[user_id] = sid  # Use sid instead of request.sid
        print(f"✅ User {user_id} registered with session ID {sid}")
    else:
        print("❌ Error: No user_id provided in registration!")


@sio.on("message")  # ✅ Listen to correct event
async def handle_message(sid, data):
    """Handles incoming chat messages."""
    breakpoint()
    user_id = data.get("sender_id")
    receiver_id = data.get("receiver_id")
    source = data.get("source", "web")
    base64_image = data.get("image")  # ✅ Match frontend field
    text_message = data.get("message")

    print(f"📩 Message received: {text_message} from {user_id} to {receiver_id}")

    message_content = text_message  # Default to text

    if base64_image:
        try:
            # ✅ Decode base64 image properly
            image_data = base64.b64decode(base64_image.split(",")[1])
            filename = f"{user_id}_{receiver_id}_{int(datetime.now().timestamp())}.jpg"
            image_file = io.BytesIO(image_data)
            upload_file = UploadFile(filename=filename, file=image_file)

            # ✅ Save the image and generate a URL
            image_path, _ = save_uploaded_image(upload_file, "chat")
            image_url = f"http://localhost:8080/{image_path}"
            message_content = image_url

        except Exception as e:
            await connection_manager.sio.emit("error", {"error": f"Failed to process image: {str(e)}"}, room=sid)
            return

    # ✅ Store message in database
    chat_service = ChatService()
    stored_message = chat_service.store_chat_message({
        "receiver_id": receiver_id,
        "message": message_content
    }, source, user_id)

    # ✅ Prepare message payload
    message_payload = {
        "sender_id": stored_message["sender_id"],
        "message": stored_message["message"],
        "timestamp": str(stored_message["timestamp"]),
        "source": stored_message["source"]
    }

    # ✅ Send message to receiver if online
    if receiver_id in connection_manager.active_connections:
        await connection_manager.send_message(sid, message_payload)

    # ✅ Also send message back to sender
    await connection_manager.sio.emit("receive_message", message_payload, room=sid)
