# src/services/s3_storage.py
import os
import asyncio
import aioboto3
from typing import Optional

AWS_S3_BUCKET = os.getenv("S3_BUCKET")
AWS_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("S3_SECRET_KEY")
AWS_REGION = os.getenv("S3_REGION", "us-east-1")
S3_PROFILE_PREFIX = os.getenv("S3_PROFILE_PREFIX", "profile_pics/")

async def upload_bytes(key: str, data: bytes, content_type: str = "image/jpeg") -> Optional[str]:
    """
    Upload bytes to S3 and return public URL (or S3 path).
    """
    session = aioboto3.Session()
    async with session.client('s3',
                              region_name=AWS_REGION,
                              aws_secret_access_key=AWS_SECRET_KEY,
                              aws_access_key_id=AWS_ACCESS_KEY) as s3:
        await s3.put_object(Bucket=AWS_S3_BUCKET, Key=key, Body=data, ContentType=content_type)
        # if bucket is public or using pre-signed URLs; here we return key
        return f"s3://{AWS_S3_BUCKET}/{key}"

async def upload_file_from_path(local_path: str, filename: str) -> Optional[str]:
    key = S3_PROFILE_PREFIX + filename
    session = aioboto3.Session()
    async with session.client('s3',
                              region_name=AWS_REGION,
                              aws_secret_access_key=AWS_SECRET_KEY,
                              aws_access_key_id=AWS_ACCESS_KEY) as s3:
        with open(local_path, "rb") as fh:
            await s3.put_object(Bucket=AWS_S3_BUCKET, Key=key, Body=fh)
        return f"s3://{AWS_S3_BUCKET}/{key}"