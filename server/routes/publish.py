from fastapi import APIRouter, File, Form, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse
import os
import shutil
import tempfile
import tarfile
import json
import uuid
import re

from helpers.auth import fetch_github_username_from_cookie
from helpers.file_validation_helpers import safe_extract_tar
from helpers.validation import validate_package_name, validate_version
from helpers.s3 import (
    s3_upload,
    s3_exists,
    s3_read_text,
    s3_write_text,
    s3_list_objects
)

router = APIRouter()
BUCKET = os.getenv("S3_BUCKET_NAME")

@router.post("/publish")
async def publish_package(
    request: Request,
    name: str = Form(...),
    version: str = Form(...),
    watpkg_file: UploadFile = File(...)
):
    validate_package_name(name)
    validate_version(version)

    if not watpkg_file.filename.endswith(".watpkg"):
        raise HTTPException(status_code=400, detail="only .watpkg files are allowed")

    username = fetch_github_username_from_cookie(request)
    
    authors_key = "AUTHORS.txt"
    try:
        if s3_exists(authors_key):
            authors_content = s3_read_text(authors_key)
            authors_list = [author.strip() for author in authors_content.split('\n') if author.strip()]
        else:
            authors_list = []
        
        if username not in authors_list:
            authors_list.append(username)
            authors_list.sort()
            s3_write_text(authors_key, '\n'.join(authors_list))
    except Exception as e:
        print(f"Warning: Failed to update AUTHORS.txt: {e}")
    
    package_prefix = f"{name}/"
    version_prefix = f"{package_prefix}{version}/"

    if s3_exists(f"{version_prefix}watkit.json"):
        raise HTTPException(status_code=409, detail="This version already exists")

    owner_key = f"{package_prefix}OWNER"
    if s3_exists(owner_key):
        owner = s3_read_text(owner_key).strip()
    else:
        owner = None
        objects = s3_list_objects(package_prefix)
        for obj_key in objects:
            if obj_key.endswith("watkit.json") and obj_key != owner_key:
                content = s3_read_text(obj_key)
                try:
                    data = json.loads(content)
                    if "author" in data:
                        owner = data["author"]
                        break
                except Exception:
                    continue
        if not owner:
            owner = username
        s3_write_text(owner_key, owner)

    if owner != username:
        raise HTTPException(status_code=403, detail="Only the package owner can publish new versions.")

    with tempfile.TemporaryDirectory() as tmpdir:
        pkg_path = os.path.join(tmpdir, watpkg_file.filename)
        with open(pkg_path, "wb") as f:
            f.write(await watpkg_file.read())

        try:
            with tarfile.open(pkg_path, "r:gz") as tar:
                safe_extract_tar(tar, tmpdir)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid archive: {e}")

        manifest_path = os.path.join(tmpdir, "watkit.json")
        if not os.path.exists(manifest_path):
            raise HTTPException(status_code=400, detail="Missing watkit.json")

        try:
            with open(manifest_path) as f:
                manifest = json.load(f)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid watkit.json")

        manifest["author"] = username
        temp_manifest_path = os.path.join(tmpdir, f"watkit.json.{uuid.uuid4().hex}.tmp")
        with open(temp_manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        s3_upload(pkg_path, f"{version_prefix}{watpkg_file.filename}")
        s3_upload(temp_manifest_path, f"{version_prefix}watkit.json")

        s3_write_text(f"downloads/{name}/{version}/count.txt", "0")

        s3_write_text(f"{package_prefix}LATEST", version)

        index_key = "search_index.json"
        try:
            if s3_exists(index_key):
                index_data = json.loads(s3_read_text(index_key))
            else:
                index_data = []
        except Exception:
            index_data = []

        found = False
        for entry in index_data:
            if entry["name"] == name:
                found = True
                if version not in entry["versions"]:
                    entry["versions"].append(version)
                    entry["versions"].sort()
                entry["latest"] = version
                entry["author"] = username
                break

        if not found:
            index_data.append({
                "name": name,
                "author": username,
                "latest": version,
                "versions": [version]
            })

        try:
            s3_write_text(index_key, json.dumps(index_data, indent=2))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update search index: {e}")

    return JSONResponse({
        "status": "ok",
        "package": name,
        "version": version,
        "author": username
    })
