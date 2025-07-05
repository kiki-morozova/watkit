from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
import boto3
import json
import os
from difflib import SequenceMatcher
from helpers.s3 import get_package_total_downloads

router = APIRouter()

BUCKET = os.environ.get("S3_BUCKET_NAME", "watkit-registry")
INDEX_KEY = "search_index.json"

s3 = boto3.client("s3")

def similarity(a: str, b: str) -> float:
    """
    Calculate the similarity between two strings using the SequenceMatcher algorithm.
    """
    return SequenceMatcher(None, a, b).ratio()

@router.get("/search")
async def search_packages(q: str = Query(...), by: str = Query("name")):
    """
    Search for packages in the remote s3 registry.
    """
    try:
        obj = s3.get_object(Bucket=BUCKET, Key=INDEX_KEY)
        index_data = json.loads(obj["Body"].read())
    except Exception:
        return JSONResponse({"error": "Failed to load search index"}, status_code=500)

    q_lower = q.lower()
    scored_matches = []

    for entry in index_data:
        target = entry.get(by, "").lower()
        score = similarity(q_lower, target)

        # Consider anything with score >= 0.5
        if score >= 0.5 or q_lower in target:
            scored_matches.append((score, entry))

    # Sort by score descending and limit to top 15
    scored_matches.sort(key=lambda x: x[0], reverse=True)
    top_results = [entry for _, entry in scored_matches[:15]]

    # Add download counts to each package
    for package in top_results:
        package_name = package.get("name", "")
        if package_name:
            package["downloads"] = get_package_total_downloads(package_name)
        else:
            package["downloads"] = 0

    return JSONResponse({"results": top_results})

@router.get("/random")
async def get_random_packages(count: int = Query(3, ge=1, le=10)):
    """
    Get random packages from the registry.
    """
    try:
        obj = s3.get_object(Bucket=BUCKET, Key=INDEX_KEY)
        index_data = json.loads(obj["Body"].read())
    except Exception:
        return JSONResponse({"error": "Failed to load search index"}, status_code=500)

    if not index_data:
        return JSONResponse({"results": []})

    # Shuffle and take the requested number of packages
    import random
    random.shuffle(index_data)
    random_packages = index_data[:count]

    # Add download counts to each package
    for package in random_packages:
        package_name = package.get("name", "")
        if package_name:
            package["downloads"] = get_package_total_downloads(package_name)
        else:
            package["downloads"] = 0

    return JSONResponse({"results": random_packages})
