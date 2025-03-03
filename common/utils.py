import os

from PIL import Image
from fastapi import UploadFile

from common.cache_string import gettext

# Define base media directories
PROFILE_IMAGE_DIR = gettext("profile_image_directory")
CHAT_IMAGE_DIR = gettext("chat_image_directory")

# Ensure directories exist
os.makedirs(PROFILE_IMAGE_DIR, exist_ok=True)
os.makedirs(CHAT_IMAGE_DIR, exist_ok=True)


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
