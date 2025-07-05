from fastapi import APIRouter, Request, Form, HTTPException
import os

from helpers.auth import fetch_github_username_from_cookie
from helpers.validation import validate_package_name, validate_username

router = APIRouter()
REGISTRY_DIR = "registry"

@router.post("/package/{name}/transfer")
async def transfer_package_ownership(
    request: Request,
    name: str,
    new_owner: str = Form(...)
):
    validate_package_name(name)
    validate_username(new_owner)
    
    username = fetch_github_username_from_cookie(request)
    package_root = os.path.join(REGISTRY_DIR, name)
    owner_file = os.path.join(package_root, "OWNER")

    if not os.path.exists(package_root):
        raise HTTPException(status_code=404, detail="Package not found")

    if os.path.exists(owner_file):
        with open(owner_file) as f:
            current_owner = f.read().strip()
        if current_owner != username:
            raise HTTPException(status_code=403, detail="You are not the current package owner")
    else:
        # Infer ownership from earliest version
        versions = sorted(os.listdir(package_root))
        if not versions:
            raise HTTPException(status_code=400, detail="No versions exist to infer ownership")
        first_manifest = os.path.join(package_root, versions[0], "watkit.json")
        if not os.path.exists(first_manifest):
            raise HTTPException(status_code=500, detail="Missing manifest in earliest version")
        with open(first_manifest) as f:
            original = f.read()
        if username not in original:
            raise HTTPException(status_code=403, detail="You are not the package owner")

    # Write new owner
    os.makedirs(package_root, exist_ok=True)
    with open(owner_file, "w") as f:
        f.write(new_owner.strip())

    return {"status": "ok", "package": name, "new_owner": new_owner}
