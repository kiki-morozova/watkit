from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import os
import json

REGISTRY_DIR = "registry"
router = APIRouter()

@router.get("/package/{name}/{version}/manifest")
async def get_manifest(name: str, version: str):
    path = os.path.join(REGISTRY_DIR, name, version, "watkit.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Manifest not found")
    try:
        with open(path) as f:
            data = json.load(f)
        return JSONResponse(data)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to read manifest")


@router.get("/package/{name}/{version}/archive")
async def get_archive(name: str, version: str):
    archive_name = f"{name}.watpkg"
    archive_path = os.path.join(REGISTRY_DIR, name, version, archive_name)
    if not os.path.exists(archive_path):
        raise HTTPException(status_code=404, detail="Package archive not found")
    return FileResponse(archive_path, media_type="application/gzip", filename=archive_name)
