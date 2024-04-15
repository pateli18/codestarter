import logging
import os

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

    async def get_all_files(self, directory: str) -> list[str]:
        all_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                all_files.append(os.path.join(root, file))
        return all_files

    async def file_exists(self, path: str) -> bool:
        return os.path.exists(path)

    async def directory_exists(self, path: str) -> bool:
        return os.path.isdir(os.path.dirname(path))
