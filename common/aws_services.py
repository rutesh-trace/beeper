import mimetypes

import aioboto3
import os

from common.cache_string import gettext
from config import app_config


class AWSClient:
    """Handles AWS authentication and S3 client creation."""

    def __init__(self):
        self.AWS_ACCESS_KEY = app_config.AWS_ACCESS_KEY
        self.AWS_SECRET_KEY = app_config.AWS_SECRET_KEY
        self.AWS_REGION = app_config.AWS_REGION
        self.S3_BUCKET_NAME = app_config.AWS_BUCKET_NAME
        self.CLOUDFRONT_DOMAIN = "https://d3954p6kspdm1i.cloudfront.net"

    async def get_s3_client(self):
        """Returns an async S3 client session."""
        session = aioboto3.Session()
        return session.client(
            "s3",
            aws_access_key_id=self.AWS_ACCESS_KEY,
            aws_secret_access_key=self.AWS_SECRET_KEY,
            region_name=self.AWS_REGION,
        )

    async def upload_to_s3(self, file_name: str, binary_data: bytes, file_type: str) -> dict:
        """Uploads a video to S3 and returns both the S3 Object URL and CloudFront CDN URL."""
        async with await self.get_s3_client() as s3_client:
            if file_type == "video":
                s3_key = f"{gettext('chat_video_directory')}/{file_name}"
            elif file_type == "image":
                s3_key = f"{gettext('chat_image_directory')}/{file_name}"
            elif file_type == "audio":
                s3_key = f"{gettext('chat_audio_directory')}/{file_name}"


            # Detect the content type dynamically
            content_type, _ = mimetypes.guess_type(file_name)
            content_type = content_type if content_type else "application/octet-stream"

            await s3_client.put_object(
                Bucket=self.S3_BUCKET_NAME,
                Key=s3_key,
                Body=binary_data,
                ContentType=content_type
            )

            # Generate both URLs
            s3_object_url = f"https://{self.S3_BUCKET_NAME}.s3.{self.AWS_REGION}.amazonaws.com/{s3_key}"
            cdn_url = f"{self.CLOUDFRONT_DOMAIN}/{s3_key}"
            print(f"S3 Object URL: {s3_object_url}")
            print(f"Cloudfront CDN URL: {cdn_url}")
            return {
                "s3_object_url": s3_object_url,
                "cdn_url": cdn_url
            }

    async def generate_presigned_url(self, file_name: str, expiration=3600) -> str:
        """Generates a temporary S3 pre-signed URL (expires in 1 hour)."""
        async with await self.get_s3_client() as s3_client:
            presigned_url = await s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.S3_BUCKET_NAME, "Key": f"videos/{file_name}"},
                ExpiresIn=expiration,
            )
            return presigned_url
