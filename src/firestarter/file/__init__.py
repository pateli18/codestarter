from .file_utils import (
    CopyStatus,
    FileClient,
    FileClientType,
    FileType,
    ReplaceConfig,
)


def _determine_file_client_from_path(path: str) -> FileClientType:
    return FileClientType.local


def get_file_client(path: str) -> FileClient:
    file_client_type = _determine_file_client_from_path(path)
    if file_client_type == FileClientType.local:
        from .local import LocalFileClient

        return LocalFileClient()
    else:
        raise ValueError(f"Invalid file client type: {file_client_type}")


__all__ = [
    "FileClient",
    "FileClientType",
    "FileType",
    "ReplaceConfig",
    "get_file_client",
    "CopyStatus",
]
