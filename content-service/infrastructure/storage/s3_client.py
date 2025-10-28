# infrastructure/storage/s3_client.py
import boto3
from config import settings


def get_s3_client():
    return boto3.client(
        "s3",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )


def upload_bytes_to_s3(
    bucket: str, key: str, data: bytes, content_type: str | None = None
):
    """Sube bytes a S3 sin devolver URL, ya que se usa content_base_path."""
    s3 = get_s3_client()
    extra_args = {"ContentType": content_type} if content_type else {}
    s3.put_object(Bucket=bucket, Key=key, Body=data, **extra_args)
