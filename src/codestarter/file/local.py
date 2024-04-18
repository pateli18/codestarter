import logging
import os
from fnmatch import fnmatch

import aiofiles

from .utils import FileClient, FileType

logger = logging.getLogger(__name__)


class LocalFileClient(FileClient):
    async def load_file_str(self, path: str) -> str:
        async with aiofiles.open(path, "r") as f:
            file_str = await f.read()

        return file_str

    async def save_file_str(self, path: str, contents: str) -> None:
        # create directory if it doesn't exist
        os.makedirs(os.path.dirname(path), exist_ok=True)
        async with aiofiles.open(path, "w") as f:
            await f.write(contents)

    async def validate_file(self, path: str) -> FileType:
        if os.path.isfile(path):
            return FileType.file
        elif os.path.isdir(path):
            return FileType.directory
        else:
            raise FileNotFoundError(f"No file or directory found at {path}")

    async def get_all_files(
        self,
        directory: str,
        include_patterns: list[str],
        exclude_patterns: list[str],
    ) -> list[str]:
        all_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                full_path = os.path.join(root, file)
                if any(
                    fnmatch(full_path, pattern) for pattern in exclude_patterns
                ):
                    continue
                if len(include_patterns) > 0 and not any(
                    fnmatch(full_path, pattern) for pattern in include_patterns
                ):
                    continue
                all_files.append(full_path)
        return all_files

    async def file_exists(self, path: str) -> bool:
        return os.path.exists(path)

    async def directory_exists(self, path: str) -> bool:
        return os.path.isdir(os.path.dirname(path))
