import os
import boto3
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)
BUCKET = os.getenv("S3_BUCKET_NAME")

def s3_upload(file_path: str, key: str):
    s3.upload_file(file_path, BUCKET, key)

def s3_exists(key: str) -> bool:
    try:
        s3.head_object(Bucket=BUCKET, Key=key)
        return True
    except s3.exceptions.ClientError:
        return False

def s3_read_text(key: str) -> str:
    obj = s3.get_object(Bucket=BUCKET, Key=key)
    return obj["Body"].read().decode("utf-8")

def s3_write_text(key: str, content: str):
    s3.put_object(Bucket=BUCKET, Key=key, Body=content.encode("utf-8"))

def s3_list_objects(prefix: str) -> list[str]:
    paginator = s3.get_paginator("list_objects_v2")
    keys = []

    for page in paginator.paginate(Bucket=BUCKET, Prefix=prefix):
        for obj in page.get("Contents", []):
            keys.append(obj["Key"])

    return keys

def get_package_download_count(package_name: str, version: str) -> int:
    """
    Get the download count for a specific package version from S3
    """
    key = f"downloads/{package_name}/{version}/count.txt"
    try:
        if s3_exists(key):
            count_text = s3_read_text(key)
            return int(count_text.strip())
        else:
            return 0
    except Exception:
        return 0

def increment_package_download_count(package_name: str, version: str) -> int:
    """
    Increment the download count for a specific package version in S3
    Returns the new count
    """
    current_count = get_package_download_count(package_name, version)
    new_count = current_count + 1
    
    key = f"downloads/{package_name}/{version}/count.txt"
    try:
        s3_write_text(key, str(new_count))
        return new_count
    except Exception:
        # If we can't write to S3, return the current count
        return current_count

def get_package_total_downloads(package_name: str) -> int:
    """
    Get the total download count across all versions of a package
    """
    prefix = f"downloads/{package_name}/"
    try:
        keys = s3_list_objects(prefix)
        total = 0
        for key in keys:
            if key.endswith("/count.txt"):
                count_text = s3_read_text(key)
                total += int(count_text.strip())
        return total
    except Exception:
        return 0
