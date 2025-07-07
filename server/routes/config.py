from fastapi import APIRouter
import os

router = APIRouter()

@router.get("/config")
async def get_config():
    """
    Get server configuration values that are safe to expose to the client
    """
    return {
        "s3_bucket_name": os.environ["S3_BUCKET_NAME"],
        "aws_region": os.environ["AWS_REGION"]
    } 