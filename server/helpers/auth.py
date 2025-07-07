import os
import httpx
from jose import jwt, JWTError
from dotenv import load_dotenv
from fastapi import HTTPException, Request
from datetime import datetime, timedelta

load_dotenv()

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
JWT_SECRET = os.getenv("JWT_SECRET", "change-this-secret")
JWT_ALGORITHM = "HS256"

REDIRECT_URI = os.getenv("REDIRECT_URI", "http://watkit-7omq2a.fly.dev/auth/callback")

def get_github_oauth_url(state: str = "") -> str:
    return (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=read:user"
        f"&state={state}"
        f"&prompt=consent"
    )

async def exchange_code_for_token(code: str, redirect_uri: str) -> str:
    url = "https://github.com/login/oauth/access_token"
    headers = {"Accept": "application/json"}
    data = {
        "client_id": GITHUB_CLIENT_ID,
        "client_secret": GITHUB_CLIENT_SECRET,
        "code": code,
        "redirect_uri": redirect_uri,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers, data=data)
        resp.raise_for_status()
        token_data = resp.json()
        return token_data.get("access_token")

async def fetch_github_username(access_token: str) -> str:
    """
    Fetch the username from the GitHub API using the access token.
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        resp = await client.get("https://api.github.com/user", headers=headers)
        resp.raise_for_status()
        return resp.json().get("login")

def fetch_github_username_from_cookie(request: Request) -> str:
    """
    Fetch the username from the JWT token in the cookie.
    """
    token = request.cookies.get("watkit_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def create_jwt(username: str) -> str:
    """
    Create a JWT token for the given username with an expiry of 1 hour.
    """
    JWT_EXPIRY_SECONDS = 3600  # 1 hour
    payload = {
        "sub": username,
        "exp": datetime.utcnow() + timedelta(seconds=JWT_EXPIRY_SECONDS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def decode_jwt(token: str) -> str:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload["username"]
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

def get_username_from_request(request: Request) -> str:
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing auth token")
    token = auth.removeprefix("Bearer ").strip()
    return decode_jwt(token)
