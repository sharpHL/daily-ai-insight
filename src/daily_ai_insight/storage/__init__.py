"""Storage management for data persistence.

Supports multiple storage backends:
    - file: Local filesystem (default)
    - kv: Cloudflare KV

Configuration via environment variables:
    STORAGE_BACKEND=file|kv
    STORAGE_PATH=storage
    STORAGE_GIT_SYNC=true
    STORAGE_AUTO_PUSH=false
"""

import os
from typing import Literal, Union
import logging

from .backends.file import FileStorage
from .backends.kv import KVStorage

logger = logging.getLogger(__name__)

StorageType = Literal["file", "kv"]
StorageBackend = Union[FileStorage, KVStorage]


def create_storage(
    backend: StorageType = "file",
    **kwargs
) -> StorageBackend:
    """Factory function to create storage backend.

    Reads configuration from environment variables:
        - STORAGE_BACKEND: Backend type ('file' or 'kv')
        - STORAGE_PATH: Base path for file storage
        - STORAGE_GIT_SYNC: Enable Git auto-commit
        - STORAGE_AUTO_PUSH: Auto-push to remote
        - CF_ACCOUNT_ID: Cloudflare account ID (for KV)
        - CF_KV_NAMESPACE_ID: KV namespace ID
        - CF_API_TOKEN: Cloudflare API token

    Args:
        backend: Storage backend type
        **kwargs: Additional backend-specific parameters

    Returns:
        Storage backend instance

    Raises:
        ValueError: If backend type is unknown
        ImportError: If required dependencies are missing

    Examples:
        # Use default (file storage with Git)
        storage = create_storage()

        # Explicit file storage
        storage = create_storage(backend="file", git_sync=True)

        # Cloudflare KV storage
        storage = create_storage(backend="kv")
    """
    # Read from environment
    backend = os.getenv("STORAGE_BACKEND", backend).lower()

    if backend == "file":
        # File storage configuration
        base_path = kwargs.get("base_path") or os.getenv("STORAGE_PATH", "storage")
        git_sync = kwargs.get("git_sync")
        if git_sync is None:
            git_sync = os.getenv("STORAGE_GIT_SYNC", "true").lower() == "true"

        auto_push = kwargs.get("auto_push")
        if auto_push is None:
            auto_push = os.getenv("STORAGE_AUTO_PUSH", "false").lower() == "true"

        logger.info(
            f"Initializing FileStorage (path={base_path}, git_sync={git_sync}, auto_push={auto_push})"
        )
        return FileStorage(
            base_path=base_path,
            git_sync=git_sync,
            auto_push=auto_push
        )

    elif backend == "kv":
        # Cloudflare KV configuration
        logger.info("Initializing KVStorage (Cloudflare KV)")
        return KVStorage(**kwargs)

    else:
        raise ValueError(
            f"Unknown storage backend: {backend}. "
            f"Supported: 'file', 'kv'"
        )


# Backward compatibility alias
def StorageManager(base_path: str = "storage"):
    """Legacy StorageManager compatibility wrapper.

    Deprecated: Use create_storage() instead.

    Args:
        base_path: Base storage path

    Returns:
        FileStorage instance
    """
    logger.warning(
        "StorageManager() is deprecated. Use create_storage() instead."
    )
    return create_storage(backend="file", base_path=base_path)


__all__ = [
    "create_storage",
    "StorageManager",
    "FileStorage",
    "KVStorage",
    "StorageBackend",
    "StorageType"
]
