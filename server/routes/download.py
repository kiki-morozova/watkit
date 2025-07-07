from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from helpers.s3 import s3, BUCKET
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
    
    try:
        # Get the object from S3 directly using boto3
        response = s3.get_object(Bucket=BUCKET, Key=filename)
        
        # Get the file content and metadata
        content = response['Body'].read()
        content_type = response.get('ContentType', 'application/octet-stream')
        content_length = response.get('ContentLength', len(content))
        
        # Create streaming response with proper download headers
        return StreamingResponse(
            iter([content]),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(content_length),
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET",
                "Access-Control-Allow-Headers": "*"
            }
        )
        
    except s3.exceptions.NoSuchKey:
        raise HTTPException(status_code=404, detail="File not found")
    except s3.exceptions.ClientError as e:
        raise HTTPException(status_code=500, detail=f"S3 error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") 