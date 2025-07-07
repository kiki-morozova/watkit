# constants for the publish command
ALLOWED_TOP_LEVEL = ["watkit.json", "README.md"]
ALLOWED_SRC_EXT = [".wat"]

# constants for the install command
PKG_DIR = "pkg"
LOCAL_REGISTRY = "registry"
REQUIRED_FIELDS = {"name", "version", "main", "output"}
ALLOWED_OPTIONAL_FIELDS = {"description", "license", "author"}
SEARCH_API_URL = "https://watkit-7omq2a.fly.dev"