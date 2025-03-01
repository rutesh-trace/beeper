import os

from PIL import Image
from fastapi import UploadFile

from common.cache_string import gettext

MEDIA_DIR = gettext("profile_image_directory")
os.makedirs(MEDIA_DIR, exist_ok=True)  # Ensure directory exists


def save_uploaded_image(profile_image: UploadFile) -> tuple[str, str]:
    """
    Saves the uploaded image using Pillow (PIL) after validation.
    Stores both the original and a resized thumbnail version.

    Returns:
        original_path (str): Path to the original image
        thumbnail_path (str): Path to the thumbnail image
    """

    try:
        # Read the image file into memory
        image = Image.open(profile_image.file)

        # Ensure it's a valid image (Pillow will raise an error if it's not)
        image.verify()

        # Reset file pointer after verification
        profile_image.file.seek(0)

        # Open the image again (since .verify() doesn't allow modifications)
        image = Image.open(profile_image.file)

        # Get original file extension
        file_ext = profile_image.filename.split(".")[-1].lower()  # Preserve original format
        file_name = ".".join(profile_image.filename.split(".")[:-1])  # Filename without extension

        # Define paths for original and thumbnail images
        original_path = os.path.join(MEDIA_DIR, f"{file_name}.{file_ext}")
        thumbnail_path = os.path.join(MEDIA_DIR, f"{file_name}_thumbnail.{file_ext}")

        # Save the original image
        image.save(original_path, format=image.format)  # Keep original format

        # Create and save thumbnail
        thumbnail = image.copy()
        thumbnail.thumbnail((500, 500))  # Resize to max 500x500px
        thumbnail.save(thumbnail_path, format=image.format)  # Keep original format

        return original_path, thumbnail_path  # Return file paths for DB storage

    except Exception as e:
        raise ValueError(f"Invalid image file: {str(e)}")  # Handle invalid images
