"""
Supabase Storage Integration Service.

Handles persistent file storage in Supabase Storage buckets (e.g. 'qa-reports').
Ensures Render ephemeral filesystem does not cause permanent data loss.
"""
import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("sih26170.supabase_storage")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
DEFAULT_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "qa-reports")

_supabase_client = None


def get_supabase_client():
    """Initializes and caches the Supabase client if credentials are configured."""
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY or SUPABASE_SERVICE_ROLE_KEY.startswith("your_"):
        logger.info("Supabase Storage credentials not configured; local streaming mode active.")
        return None

    try:
        from supabase import create_client, Client
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        logger.info("Supabase client successfully initialized for storage: %s", SUPABASE_URL)
        return _supabase_client
    except Exception as e:
        logger.warning("Failed to initialize Supabase client: %s", e)
        return None


def upload_pdf_to_storage(
    pdf_bytes: bytes,
    file_path: str,
    bucket: str = DEFAULT_BUCKET,
    content_type: str = "application/pdf"
) -> Optional[str]:
    """
    Uploads a PDF byte buffer to Supabase Storage bucket and returns the public or signed URL.
    Returns None if Supabase Storage is not configured.
    """
    client = get_supabase_client()
    if client is None:
        return None

    try:
        # Check / create bucket if needed (service role)
        # Upload binary file
        response = client.storage.from_(bucket).upload(
            path=file_path,
            file=pdf_bytes,
            file_options={"content-type": content_type, "upsert": "true"}
        )
        
        # Get public URL
        public_url = client.storage.from_(bucket).get_public_url(file_path)
        logger.info("Successfully uploaded PDF to Supabase Storage: %s", public_url)
        return public_url
    except Exception as e:
        logger.error("Error uploading to Supabase Storage (%s/%s): %s", bucket, file_path, e)
        return None
