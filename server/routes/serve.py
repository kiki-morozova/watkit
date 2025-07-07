from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import os
import threading
from helpers.s3 import increment_package_download_count, get_package_download_count, s3_list_objects, s3_read_text, s3_write_text, s3_exists
from helpers.validation import validate_package_name, validate_version

router = APIRouter()

# Global download counter with thread safety and S3 persistence
TOTAL_DOWNLOADS_COUNTER = 0
download_lock = threading.Lock()
BUCKET = os.environ["S3_BUCKET_NAME"]

def load_total_downloads():
    """Load total downloads count from S3"""
    global TOTAL_DOWNLOADS_COUNTER
    try:
        if s3_exists("total_downloads.txt"):
            count_text = s3_read_text("total_downloads.txt")
            TOTAL_DOWNLOADS_COUNTER = int(count_text.strip())
        else:
            TOTAL_DOWNLOADS_COUNTER = 0
    except Exception as e:
        print(f"Error loading total downloads: {e}")
        TOTAL_DOWNLOADS_COUNTER = 0

def increment_download_counter():
    global TOTAL_DOWNLOADS_COUNTER
    with download_lock:
        TOTAL_DOWNLOADS_COUNTER += 1
        # Save to S3
        try:
            s3_write_text("total_downloads.txt", str(TOTAL_DOWNLOADS_COUNTER))
        except Exception as e:
            print(f"Error saving total downloads: {e}")
        return TOTAL_DOWNLOADS_COUNTER

def get_download_counter():
    global TOTAL_DOWNLOADS_COUNTER
    with download_lock:
        return TOTAL_DOWNLOADS_COUNTER

# Load the total downloads count when the module is imported
load_total_downloads()

@router.get("/package/{name}/{version}/manifest")
async def get_manifest(name: str, version: str):
    validate_package_name(name)
    validate_version(version)
    
    try:
        # Use S3 helper to read the manifest directly from S3
        manifest_key = f"{name}/{version}/watkit.json"
        if not s3_exists(manifest_key):
            raise HTTPException(status_code=404, detail="Manifest not found")
        
        manifest_content = s3_read_text(manifest_key)
        import json
        data = json.loads(manifest_content)
        return JSONResponse(data)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error reading manifest for {name}v{version}: {e}")
        raise HTTPException(status_code=500, detail="Failed to read manifest")


@router.get("/package/{name}/{version}/archive")
async def get_archive(name: str, version: str):
    validate_package_name(name)
    validate_version(version)
    
    archive_name = f"{name}.watpkg"
    archive_path = os.path.join(BUCKET, name, version, archive_name)
    if not os.path.exists(archive_path):
        raise HTTPException(status_code=404, detail="Package archive not found")
    
    # Track download for this specific package version
    download_count = increment_package_download_count(name, version)
    # Also increment global counter
    total_downloads = increment_download_counter()
    print(f"Download tracked: {name}v{version} (package downloads: {download_count}, total: {total_downloads})")
    
    return FileResponse(archive_path, media_type="application/gzip", filename=archive_name)

@router.post("/track-download")
async def track_download(name: str, version: str):
    """
    Track a package download (called by CLI install command)
    """
    validate_package_name(name)
    validate_version(version)
    
    download_count = increment_package_download_count(name, version)
    # Also increment global counter
    total_downloads = increment_download_counter()
    print(f"Download tracked via API: {name}v{version} (package downloads: {download_count}, total: {total_downloads})")
    return JSONResponse({"success": True, "download_count": download_count})

@router.get("/downloads")
async def get_download_count():
    """
    Get the total number of downloads across all packages
    """
    return JSONResponse({"total_downloads": get_download_counter()})

@router.get("/authors")
async def get_authors_count():
    """
    Get the number of authors by counting lines in AUTHORS.txt
    """
    try:
        if s3_exists("AUTHORS.txt"):
            authors_text = s3_read_text("AUTHORS.txt")
            # Count non-empty lines
            lines = [line.strip() for line in authors_text.split('\n') if line.strip()]
            return JSONResponse({"total_authors": len(lines)})
        else:
            return JSONResponse({"total_authors": 0})
    except Exception as e:
        print(f"Error reading AUTHORS.txt: {e}")
        return JSONResponse({"total_authors": 0})

@router.get("/packages")
async def get_packages_count():
    """
    Get the number of packages by counting entries in search_index.json
    """
    try:
        if s3_exists("search_index.json"):
            import json
            index_text = s3_read_text("search_index.json")
            index_data = json.loads(index_text)
            return JSONResponse({"total_packages": len(index_data)})
        else:
            return JSONResponse({"total_packages": 0})
    except Exception as e:
        print(f"Error reading search_index.json: {e}")
        return JSONResponse({"total_packages": 0})

@router.get("/package/{name}/{version}/downloads")
async def get_package_download_count_endpoint(name: str, version: str):
    """
    Get the download count for a specific package version
    """
    validate_package_name(name)
    validate_version(version)
    
    count = get_package_download_count(name, version)
    return JSONResponse({"downloads": count})
