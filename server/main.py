from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from routes.publish import router as publish_router
from routes.auth import router as auth_router
from routes.serve import router as serve_router
from routes.search import router as search_router
from routes.config import router as config_router
from routes.download import router as download_router

app = FastAPI()

# Mount static files
app.mount("/web", StaticFiles(directory="web"), name="web")

# Register routes
app.include_router(publish_router, prefix="")
app.include_router(auth_router, prefix="")
app.include_router(serve_router, prefix="")
app.include_router(search_router, prefix="")
app.include_router(config_router, prefix="")
app.include_router(download_router, prefix="")

# Serve the main page at root
@app.get("/")
async def read_index():
    return FileResponse("web/index.html")

# Serve the package page
@app.get("/package")
async def read_package():
    return FileResponse("web/package.html")

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Watkit API",
        version="1.0.0",
        description="Watkit Registry Server (uses GitHub OAuth cookies)",
        routes=app.routes,
    )
    openapi_schema["openapi"] = "3.0.3"

    # Optionally describe the cookie-based JWT auth (docs-only)
    openapi_schema["components"]["securitySchemes"] = {
        "cookieAuth": {
            "type": "apiKey",
            "in": "cookie",
            "name": "watkit_token"
        }
    }

    for path in openapi_schema["paths"].values():
        for method in path.values():
            method.setdefault("security", [{"cookieAuth": []}])

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
