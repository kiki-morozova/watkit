from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from urllib.parse import unquote
from pydantic import BaseModel
from helpers.auth import (
    get_github_oauth_url,
    exchange_code_for_token,
    fetch_github_username,
    create_jwt,
)
from helpers.validation import validate_alphanumeric_hyphen_underscore, validate_github_code, validate_github_token
import os
import httpx

router = APIRouter()
GITHUB_REDIRECT_URI = os.getenv("REDIRECT_URI", "https://watkit-7omq2a.fly.dev/auth/callback")

@router.get("/auth/login")
async def login(state: str = ""):
    if state:
        validate_alphanumeric_hyphen_underscore(state, "state")
    url = get_github_oauth_url(state=state)
    return RedirectResponse(url)

@router.get("/auth/callback")
async def callback(code: str, state: str):
    validate_github_code(code)
    if state:
        validate_alphanumeric_hyphen_underscore(state, "state")
    
    access_token = await exchange_code_for_token(code, redirect_uri=GITHUB_REDIRECT_URI)
    username = await fetch_github_username(access_token)
    jwt_token = create_jwt(username)

    decoded_state = unquote(state)
    if decoded_state.startswith("https://watkit-7omq2a.fly.dev"):
        # CLI login
        redirect_url = f"{decoded_state}?token={jwt_token}"
        return RedirectResponse(redirect_url)

    # Web login
    response = RedirectResponse(url="/auth/success")
    response.set_cookie(
        key="watkit_token",
        value=jwt_token,
        max_age=3600,
        httponly=True,
        secure=True,
        samesite="Lax"
    )
    return response

@router.get("/auth/success")
async def success():
    return HTMLResponse("""
    <script>
        alert("Login successful! You can now publish.");
        window.location.href = "/";
    </script>
    """)

@router.get("/auth/logout")
async def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("watkit_token")
    return response

class GitHubTokenIn(BaseModel):
    access_token: str

@router.post("/auth/github-token")
async def github_token_to_jwt(data: GitHubTokenIn):
    validate_github_token(data.access_token)
    
    try:
        username = await fetch_github_username(data.access_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid GitHub token")

    jwt_token = create_jwt(username)
    return {"token": jwt_token}

@router.post("/auth/exchange")
async def exchange_token(request: Request):
    data = await request.json()
    github_token = data.get("access_token")
    if not github_token:
        raise HTTPException(status_code=400, detail="Missing access token")

    validate_github_token(github_token)

    try:
        username = await fetch_github_username(github_token)
    except httpx.HTTPError:
        raise HTTPException(status_code=401, detail="Invalid GitHub token")

    jwt_token = create_jwt(username)
    return JSONResponse({"watkit_token": jwt_token})
