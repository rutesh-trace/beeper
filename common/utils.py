import io
import time
import os
from datetime import datetime
import asyncio
import aiofiles
from PIL import Image
from fastapi import UploadFile
import base64
import ffmpeg

from common.aws_services import AWSClient
from common.cache_string import gettext

# Define base media directories
PROFILE_IMAGE_DIR = gettext("profile_image_directory")
CHAT_IMAGE_DIR = gettext("chat_image_directory")

# Ensure directories exist
os.makedirs(PROFILE_IMAGE_DIR, exist_ok=True)

aws_client = AWSClient()


def save_uploaded_image(image_file: UploadFile, image_type: str = "profile") -> tuple[str, str | None]:
    """
    Saves an uploaded image and returns the file path.

    - If `image_type == "profile"`, it resizes the image and stores a thumbnail.
    - If `image_type == "chat"`, it saves only the original image.

    Returns:
        - original_path (str): Path to the original image.
        - thumbnail_path (str | None): Path to the thumbnail (only for profile images).
    """
    try:
        # Read and verify the image
        image = Image.open(image_file.file)
        image.verify()

        # Reset file pointer after verification
        image_file.file.seek(0)
        image = Image.open(image_file.file)

        # Extract file extension and name
        file_ext = image_file.filename.split(".")[-1].lower()
        file_name = ".".join(image_file.filename.split(".")[:-1])

        # Choose directory based on `image_type`
        if image_type == "profile":
            save_dir = PROFILE_IMAGE_DIR
            thumbnail_required = True
        elif image_type == "chat":
            save_dir = CHAT_IMAGE_DIR
            thumbnail_required = False
        else:
            raise ValueError("Invalid image_type. Must be 'profile' or 'chat'.")

        # Define file paths
        original_path = os.path.join(save_dir, f"{file_name}.{file_ext}")
        thumbnail_path = os.path.join(save_dir, f"{file_name}_thumbnail.{file_ext}") if thumbnail_required else None

        # Save the original image
        image.save(original_path, format=image.format)

        # Create and save thumbnail only for profile images
        if thumbnail_required:
            thumbnail = image.copy()
            thumbnail.thumbnail((500, 500))  # Resize to max 500x500px
            thumbnail.save(thumbnail_path, format=image.format)

        return original_path, thumbnail_path  # Return paths for DB storage

    except Exception as e:
        raise ValueError(f"Invalid image file: {str(e)}")


async def save_base64_image(message_data: dict) -> dict:
    """
    Decodes a Base64 image string and saves it using the provided file name.

    Args:
        message_data (dict[str, str | None]): Base64 image data.

    Returns:
        str: Path to the saved image file.
    """
    try:
        sender_id = message_data.get("senderID")
        receiver_id = message_data.get("receiverID")
        image_binary_data = message_data.get("image")
        file_name = message_data.get("file_name")

        if not all([sender_id, receiver_id, image_binary_data, file_name]):
            raise ValueError("Missing required message data fields")

        # Generate unique file name
        file_ext = file_name.split(".")[-1].lower()
        split_file_name = file_name.split(".")[0].lower().replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{split_file_name}_Sender{sender_id}_Receiver{receiver_id}_{timestamp}.{file_ext}"

        # Start upload timer
        start_time = time.time()
        print(f"Start Time: {start_time:.2f} seconds")

        # Upload asynchronously to S3
        image_url = await aws_client.upload_to_s3(file_name=safe_filename, binary_data=image_binary_data,
                                                  file_type="image")

        print(f"Image uploaded to S3 in {time.time() - start_time:.2f} seconds: {image_url}")
        return image_url

    except Exception as e:
        raise ValueError(f"Invalid Base64 image: {str(e)}")


async def save_base64_video(message_data: dict) -> dict:
    """Saves Base64 video directly to S3 and returns URL."""
    try:
        sender_id = message_data.get("senderID")
        receiver_id = message_data.get("receiverID")
        video_base64_str = message_data.get("video")
        file_name = message_data.get("file_name")

        if not all([sender_id, receiver_id, video_base64_str, file_name]):
            raise ValueError("Missing required message data fields")

        # Generate unique file name
        file_ext = file_name.split(".")[-1].lower()
        split_file_name = file_name.split(".")[0].lower().replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{split_file_name}_Sender{sender_id}_Receiver{receiver_id}_{timestamp}.{file_ext}"

        # Start upload timer
        start_time = time.time()
        print(f"Start Time: {start_time:.2f} seconds")

        # Upload asynchronously to S3
        video_url = await aws_client.upload_to_s3(file_name=safe_filename, binary_data=video_base64_str,
                                                  file_type="video")

        print(f"Video uploaded to S3 in {time.time() - start_time:.2f} seconds: {video_url}")
        return video_url

    except Exception as e:
        raise ValueError(f"Error uploading video to S3: {str(e)}")


async def save_base64_audio(message_data: dict) -> dict:
    """Saves Base64 audio directly to S3 and returns URL."""
    try:
        sender_id = message_data.get("senderID")
        receiver_id = message_data.get("receiverID")
        audio_base64_str = message_data.get("audio")
        file_name = message_data.get("file_name")

        if not all([sender_id, receiver_id, audio_base64_str, file_name]):
            raise ValueError("Missing required message data fields")

        # Generate unique file name
        file_ext = file_name.split(".")[-1].lower()
        split_file_name = file_name.split(".")[0].lower().replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{split_file_name}_Sender{sender_id}_Receiver{receiver_id}_{timestamp}.{file_ext}"

        # Start upload timer
        start_time = time.time()
        print(f"Start Time: {start_time:.2f} seconds")

        # Upload asynchronously to S3
        audio_url = await aws_client.upload_to_s3(
            file_name=safe_filename,
            binary_data=audio_base64_str,
            file_type="audio"
        )

        print(f"Audio uploaded to S3 in {time.time() - start_time:.2f} seconds: {audio_url}")
        return audio_url

    except Exception as e:
        raise ValueError(f"Error uploading audio to S3: {str(e)}")


def is_webm(binary_data):
    """Check if the binary data represents a WebM file by checking the magic bytes."""
    return binary_data.startswith(b'\x1A\x45\xDF\xA3')  # WebM file signature


async def convert_webm_to_mp3(input_binary):
    """Convert WebM audio binary data to MP3 in memory (without writing files)."""
    if not is_webm(input_binary):
        raise ValueError("Provided binary data is not a valid WebM file.")

    # Use an input stream
    input_stream = io.BytesIO(input_binary)

    # Run ffmpeg with input and output as byte streams
    try:
        out, _ = (
            ffmpeg
            .input('pipe:0')  # Read from stdin (WebM binary)
            .output('pipe:1', format='mp3', audio_bitrate='192k', acodec='libmp3lame')  # MP3 output
            .run(input=input_stream.read(), capture_stdout=True, capture_stderr=True)
        )
        return out
    except ffmpeg.Error as e:
        print("FFmpeg error:", e.stderr.decode())
        return None
