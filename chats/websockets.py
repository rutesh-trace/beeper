import socketio

# Create a global Socket.IO server instance
sio = socketio.AsyncServer(cors_allowed_origins='*', async_mode='asgi')

connected_users = {}  # Store connected users
user_details = {}


@sio.on("connect")
async def connect(sid, env):
    connected_users[sid] = env
    print(f"✅ New Client Connected: {sid}")
    await sio.emit("send_msg", "Hello from Server", room=sid)  # Send only to the connected client


@sio.on("disconnect")
async def disconnect(sid):
    print(f"❌ Client Disconnected: {sid}")
    for user_id, user_sid in connected_users.items():
        if user_sid == sid:
            del connected_users[user_id]
            break


@sio.on("register_user")
async def register_user(sid, data):
    print("Register users ===> ", data)
    print("connected_users users ===> ", user_details)

    user_id = data.get("user_id")
    if user_id:
        user_details[user_id] = sid
        print(f"✅ User {user_id} registered with session ID {sid}")


@sio.on("msg")
async def receive_message(sid, msg):
    print(f"📩 Message from {sid}: {msg}")
    await sio.emit("send_msg", msg)


@sio.on("msg")
async def send_message_to_client(sid, data):
    sender_id = data.get("senderID")
    target_id = data.get("user_id")

    message = data.get("message", "Default message from server")

    # Find recipient's socket ID
    target_sid = user_details.get(target_id)

    if target_sid:
        await sio.emit("message", {"sender_id": sender_id, "message": message}, to=target_id)
        await sio.emit("receive_msg", message, to=target_sid)  # Send to that client
        print(f"📩 Server sent message to {target_id} ({target_sid}): {message}")
    else:
        print(f"⚠️ User {target_id} not found.")


# Export `sio` instance
socket_app = socketio.ASGIApp(sio)
