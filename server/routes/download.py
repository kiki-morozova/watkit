from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import httpx
import os

router = APIRouter()

@router.get("/download/{filename}")
async def download_file(filename: str):
    """
    Download a file from S3 with proper download headers
    """
    # Validate filename to prevent directory traversal
    if not filename or '/' in filename or '..' in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    # Get S3 bucket name from environment
    bucket_name = os.environ["S3_BUCKET_NAME"]
    if not bucket_name:
        raise HTTPException(status_code=500, detail="S3 bucket not configured")
    
    # Construct S3 website URL
    s3_url = f"https://{bucket_name}.s3-website-us-east-1.amazonaws.com/{filename}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(s3_url)
            
            if response.status_code != 200:
                raise HTTPException(status_code=404, detail="File not found")
            
            # Create streaming response with proper download headers
            return StreamingResponse(
                iter([response.content]),
                media_type="application/octet-stream",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "Content-Length": str(len(response.content)),
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET",
                    "Access-Control-Allow-Headers": "*"
                }
            )
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch file: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") 