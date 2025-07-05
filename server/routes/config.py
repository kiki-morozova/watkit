from fastapi import APIRouter
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

@router.get("/config")
async def get_config():
    """
    Get server configuration values that are safe to expose to the client
    """
    return {
        "s3_bucket_name": os.getenv("S3_BUCKET_NAME"),
        "aws_region": os.getenv("AWS_REGION")
    } 