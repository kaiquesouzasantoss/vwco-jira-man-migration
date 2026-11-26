import os
from pathlib import Path


def get_bool_env(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "sim"}


def get_int_env(name, default):
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


SCRIPT_VERSION = "2026.07.10-enterprise-hardened"
JIRA_URL = os.getenv("JIRA_URL")
JIRA_USERNAME = os.getenv("JIRA_USERNAME")
JIRA_PASSWORD = os.getenv("JIRA_PASSWORD")
BASE_OUTPUT_FOLDER = Path(os.getenv("JIRA_OUTPUT_FOLDER", r"C:\TEMP_"))
PAGE_SIZE = get_int_env("JIRA_PAGE_SIZE", 50)
API_PAGE_SIZE = get_int_env("JIRA_API_PAGE_SIZE", 10)
VERIFY_SSL = get_bool_env("JIRA_VERIFY_SSL", True)
JIRA_CA_BUNDLE = os.getenv("JIRA_CA_BUNDLE")
CREATE_RAW_JSON = get_bool_env("JIRA_CREATE_RAW_JSON", False)
RUN_SINGLE_ISSUE = get_bool_env("JIRA_RUN_SINGLE_ISSUE", False)
SINGLE_ISSUE_KEY = os.getenv("JIRA_SINGLE_ISSUE_KEY", "ITG-122")
ENABLE_PARALLEL_EXECUTION = get_bool_env("JIRA_ENABLE_PARALLEL", False)
MAX_WORKERS = get_int_env("JIRA_MAX_WORKERS", 5)
SAFE_MAX_WORKERS_LIMIT = get_int_env("JIRA_SAFE_MAX_WORKERS_LIMIT", 5)
MAX_RETRIES = get_int_env("JIRA_MAX_RETRIES", 3)
RETRY_BACKOFF_SECONDS = get_int_env("JIRA_RETRY_BACKOFF_SECONDS", 1)
REQUEST_TIMEOUT_SECONDS = get_int_env("JIRA_REQUEST_TIMEOUT_SECONDS", 60)
RESUME_ENABLED = get_bool_env("JIRA_RESUME_ENABLED", False)
RUN_FOLDER_NAME = os.getenv("JIRA_RUN_FOLDER_NAME", "JIRA-MIGRATION")
USE_TIMESTAMPED_RUN_FOLDER = get_bool_env("JIRA_USE_TIMESTAMPED_RUN_FOLDER", False)
REFRESH_ISSUE_BEFORE_EXPORT = get_bool_env("JIRA_REFRESH_ISSUE_BEFORE_EXPORT", True)
DOWNLOAD_ATTACHMENTS = get_bool_env("JIRA_DOWNLOAD_ATTACHMENTS", True)

FT_KEYS = [
    "FT-4256",
    "FT-4274"
]

ITG_KEYS = [
    "ITG-923",
    "ITG-1217",
    "ITG-1824",
    "ITG-1840",
    "ITG-1863",
    "ITG-1929",
    "ITG-1967",
    "ITG-1979",
    "ITG-1990",
    "ITG-2005",
    "ITG-2012",
    "ITG-2036",
    "ITG-2039",
    "ITG-2057",
    "ITG-2061",
    "ITG-2072",
    "ITG-2075",
    "ITG-2076",
    "ITG-2077",
    "ITG-2079",
    "ITG-2080",
    "ITG-2081",
    "ITG-2082",
    "ITG-2083",
    "ITG-2084",
    "ITG-2085",
    "ITG-2086",
    "ITG-2087",
    "ITG-2088",
    "ITG-2089",
    "ITG-2090",
    "ITG-2091",
    "ITG-2092",
    "ITG-2093",
    "ITG-2094",
    "ITG-2095",
    "ITG-2096",
    "ITG-2097",
    "ITG-2098",
    "ITG-2099",
    "ITG-2100",
    "ITG-2101",
    "ITG-2102",
    "ITG-2103",
]

def build_keys_jql(keys):
    quoted = ", ".join(key.strip() for key in keys if key.strip())
    return f"key in ({quoted}) ORDER BY key ASC"

EXTRACTION_CONFIGS = {
    "ITG": {"label": "ITG", "description": "Extract ITG issues", "jql": "project = ITG ORDER BY key ASC"},
    "FT": {"label": "FT", "description": "Extract FT issues", "jql": "project = FT ORDER BY key ASC"},
    "FTB": {"label": "FTB", "description": "Extract FTB issues", "jql": "project = FTB ORDER BY key ASC "},
    "ML": {"label": "ML", "description": "Extract ML issues", "jql": "project = ML ORDER BY key ASC "},
    "FT_LIST": {"label": "FT (selected items)", "description": "Extract only the FT issues listed in FT_KEYS", "jql": build_keys_jql(FT_KEYS)},
    "ITG_LIST": {"label": "ITG (selected items)", "description": "Extract only the ITG issues listed in ITG_KEYS","jql": build_keys_jql(ITG_KEYS)}
}

def validate_required_settings():
    missing_settings = []

    if not JIRA_USERNAME:
        missing_settings.append("JIRA_USERNAME")
    if not JIRA_PASSWORD:
        missing_settings.append("JIRA_PASSWORD")
    if not JIRA_URL:
        missing_settings.append("JIRA_URL")
    if missing_settings:
        raise ValueError("Missing required environment variables: " + ", ".join(missing_settings))
