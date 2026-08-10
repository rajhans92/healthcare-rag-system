"""
AWS S3 service.

Handles S3 operations for medical document files.
"""

import logging

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)


class S3Service:
    """
    Service responsible for AWS S3 operations.
    """

    def __init__(self) -> None:
        self.bucket_name = settings.AWS_S3_BUCKET_NAME

        self.client = boto3.client(
            "s3",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

    # ==========================================================
    # Generate Upload URL
    # ==========================================================

    def generate_upload_url(
        self,
        file_key: str,
        mime_type: str,
        expires_in: int = 900,
    ) -> str:
        """
        Generate a presigned URL for uploading a file to S3.

        Default expiration: 15 minutes.
        """

        try:
            url = self.client.generate_presigned_url(
                ClientMethod="put_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": file_key,
                    "ContentType": mime_type,
                },
                ExpiresIn=expires_in,
            )

            return url

        except (
            ClientError,
            BotoCoreError,
        ) as exc:

            logger.exception(
                "Failed to generate S3 upload URL."
            )

            raise RuntimeError(
                "Unable to generate S3 upload URL."
            ) from exc

    # ==========================================================
    # Check Object Exists
    # ==========================================================

    def object_exists(
        self,
        file_key: str,
    ) -> bool:
        """
        Check whether an object exists in S3.
        """

        try:
            self.client.head_object(
                Bucket=self.bucket_name,
                Key=file_key,
            )

            return True

        except ClientError as exc:

            error_code = exc.response.get(
                "Error",
                {},
            ).get(
                "Code"
            )

            if error_code in (
                "404",
                "NoSuchKey",
                "NotFound",
            ):
                return False

            logger.exception(
                "Failed to check S3 object."
            )

            raise RuntimeError(
                "Unable to verify S3 object."
            ) from exc

    # ==========================================================
    # Generate Download URL
    # ==========================================================

    def generate_download_url(
        self,
        file_key: str,
        expires_in: int = 900,
    ) -> str:
        """
        Generate a presigned URL for downloading
        a private S3 object.
        """

        try:
            url = self.client.generate_presigned_url(
                ClientMethod="get_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": file_key,
                },
                ExpiresIn=expires_in,
            )

            return url

        except (
            ClientError,
            BotoCoreError,
        ) as exc:

            logger.exception(
                "Failed to generate S3 download URL."
            )

            raise RuntimeError(
                "Unable to generate S3 download URL."
            ) from exc

    # ==========================================================
    # Delete Object
    # ==========================================================

    def delete_object(
        self,
        file_key: str,
    ) -> None:
        """
        Delete an object from S3.
        """

        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=file_key,
            )

        except (
            ClientError,
            BotoCoreError,
        ) as exc:

            logger.exception(
                "Failed to delete S3 object."
            )

            raise RuntimeError(
                "Unable to delete S3 object."
            ) from exc