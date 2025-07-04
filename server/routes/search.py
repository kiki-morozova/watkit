from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
import boto3
import json
import os
from difflib import get_close_matches

router = APIRouter()

BUCKET = os.environ.get("S3_BUCKET_NAME", "watkit-registry")
INDEX_KEY = "search_index.json"

s3 = boto3.client("s3")

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
import boto3
import json
import os
from difflib import SequenceMatcher

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

    return JSONResponse({"results": top_results})
