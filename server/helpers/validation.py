import re
from typing import Optional
from fastapi import HTTPException


def validate_alphanumeric_hyphen_underscore(value: str, field_name: str) -> None:
    """Validate that string only contains alphanumeric characters, hyphens, and underscores."""
    if not re.match(r'^[a-zA-Z0-9_-]+$', value):
        raise HTTPException(
            status_code=400, 
            detail=f"{field_name} must only contain alphanumeric characters, hyphens (-), and underscores (_)"
        )


def validate_alphanumeric_dots(value: str, field_name: str) -> None:
    """Validate that string only contains alphanumeric characters and dots."""
    if not re.match(r'^[a-zA-Z0-9.]+$', value):
        raise HTTPException(
            status_code=400, 
            detail=f"{field_name} must only contain alphanumeric characters and dots"
        )


def validate_alphanumeric_hyphen_underscore_dots(value: str, field_name: str) -> None:
    """Validate that string only contains alphanumeric characters, hyphens, underscores, and dots."""
    if not re.match(r'^[a-zA-Z0-9_.-]+$', value):
        raise HTTPException(
            status_code=400, 
            detail=f"{field_name} must only contain alphanumeric characters, hyphens (-), underscores (_), and dots"
        )


def validate_length(value: str, field_name: str, max_length: int) -> None:
    """Validate that string doesn't exceed maximum length."""
    if len(value) > max_length:
        raise HTTPException(
            status_code=400, 
            detail=f"{field_name} must be less than {max_length} characters"
        )


def validate_github_code(value: str) -> None:
    """Validate GitHub OAuth code format."""
    if not re.match(r'^[a-zA-Z0-9_-]+$', value):
        raise HTTPException(
            status_code=400, 
            detail="Invalid GitHub authorization code format"
        )


def validate_github_token(value: str) -> None:
    """Validate GitHub token format."""
    if not re.match(r'^[a-zA-Z0-9_-]+$', value):
        raise HTTPException(
            status_code=400, 
            detail="Invalid GitHub token format"
        )


def validate_package_name(name: str) -> None:
    """Validate package name with comprehensive checks."""
    validate_alphanumeric_hyphen_underscore(name, "package name")
    validate_length(name, "package name", 30)
    
    if name == "downloads":
        raise HTTPException(status_code=400, detail="downloads is a reserved package name")


def validate_version(version: str) -> None:
    """Validate version string."""
    validate_alphanumeric_dots(version, "version")
    validate_length(version, "version", 20)


def validate_username(username: str) -> None:
    """Validate GitHub username."""
    validate_alphanumeric_hyphen_underscore(username, "username")
    validate_length(username, "username", 39) 