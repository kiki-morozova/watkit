# constants for the publish command
ALLOWED_TOP_LEVEL = ["watkit.json", "README.md"]
ALLOWED_SRC_EXT = [".wat"]

# constants for the install command
PKG_DIR = "pkg"
LOCAL_REGISTRY = "registry"
REQUIRED_FIELDS = {"name", "version", "main", "output"}
ALLOWED_OPTIONAL_FIELDS = {"description", "license", "author"}
SEARCH_API_URL = "https://watkit.dev"

GITHUB_DEVICE_CODE_URL = "https://github.com/login/device/code"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_API = "https://api.github.com/user"
SERVER_URL = "https://watkit.dev"