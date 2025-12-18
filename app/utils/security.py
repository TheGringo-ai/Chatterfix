import bleach
import logging
import os
import asyncio
from typing import Optional

# Conditional import for google.cloud.secretmanager
try:
    from google.cloud import secretmanager

    SECRET_MANAGER_AVAILABLE = True
except ImportError:
    SECRET_MANAGER_AVAILABLE = False
    logging.warning(
        "google-cloud-secret-manager not installed. Cannot fetch secrets from Secret Manager."
    )


logger = logging.getLogger(__name__)


def sanitize_html_input(text: str) -> str:
    """
    Sanitizes HTML input to prevent XSS attacks.
    Removes potentially dangerous tags and attributes.
    """
    if not isinstance(text, str):
        return text  # Return as is if not a string

    # Define allowed tags and attributes for general content
    # This list should be carefully curated based on application needs
    allowed_tags = [
        "a",
        "abbr",
        "acronym",
        "b",
        "blockquote",
        "code",
        "em",
        "i",
        "li",
        "ol",
        "p",
        "strong",
        "ul",
    ]
    allowed_attributes = {
        "a": ["href", "title"],
        "abbr": ["title"],
        "acronym": ["title"],
    }

    try:
        cleaned_text = bleach.clean(
            text,
            tags=allowed_tags,
            attributes=allowed_attributes,
            strip=True,  # Strip disallowed tags and their content
        )
        return cleaned_text
    except Exception as e:
        logger.error(f"Error sanitizing HTML input: {e}")
        return text  # Return original text on error, or an empty string


def escape_sql_input(text: str) -> str:
    """
    Escapes single quotes in a string to help prevent SQL injection in cases
    where parameterized queries cannot be used (should be rare).

    WARNING: This is NOT a substitute for parameterized queries.
    Always prefer using an ORM or database driver that supports parameterized queries.
    """
    if not isinstance(text, str):
        return text  # Return as is if not a string

    return text.replace("'", "''")


def _get_secret_sync_from_manager(
    secret_id: str, project_id: Optional[str] = None
) -> Optional[str]:
    """Synchronously fetches a secret from Google Secret Manager."""
    if not SECRET_MANAGER_AVAILABLE:
        return None

    try:
        client = secretmanager.SecretManagerServiceClient()
        if project_id is None:
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            logger.warning(
                f"GOOGLE_CLOUD_PROJECT environment variable not set, cannot fetch secret '{secret_id}' from Secret Manager."
            )
            return None

        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.error(f"Failed to fetch secret '{secret_id}' from Secret Manager: {e}")
        return None


async def get_secret(secret_id: str, project_id: Optional[str] = None) -> Optional[str]:
    """
    Fetches a secret. Prioritizes environment variables, then Google Secret Manager.
    """
    # 1. Try fetching from environment variables (Cloud Run injected secrets)
    env_value = os.getenv(
        secret_id.upper()
    )  # Assuming ENV var name matches secret_id in uppercase
    if env_value:
        return env_value

    # 2. Try fetching from Google Secret Manager
    if SECRET_MANAGER_AVAILABLE:
        # Use asyncio.to_thread for synchronous Secret Manager client in async context
        return await asyncio.to_thread(
            _get_secret_sync_from_manager, secret_id, project_id
        )

    logger.warning(
        f"Secret '{secret_id}' not found in environment or Secret Manager (or client not available)."
    )
    return None


def get_secret_sync(secret_id: str, project_id: Optional[str] = None) -> Optional[str]:
    """
    Synchronous version of get_secret.
    Fetches a secret. Prioritizes environment variables, then Google Secret Manager.
    """
    # 1. Try fetching from environment variables
    env_value = os.getenv(secret_id.upper())
    if env_value:
        return env_value

    # 2. Try fetching from Google Secret Manager (synchronously)
    if SECRET_MANAGER_AVAILABLE:
        return _get_secret_sync_from_manager(secret_id, project_id)

    logger.warning(
        f"Secret '{secret_id}' not found in environment or Secret Manager (or client not available)."
    )
    return None
