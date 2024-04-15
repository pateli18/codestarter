import logging
import re
from abc import abstractmethod
from enum import Enum

from pydantic import BaseModel

from ..utils import OpsSemaphore

logger = logging.getLogger("firestarter")


class CopyStatus(str, Enum):
    success = "success"
    fail = "fail"
    skip = "skip"


class ReplaceConfig(BaseModel):
    original_value: str
    new_value: str
    match_casing: bool = False

    def resolve(self, global_variables: dict[str, str]) -> "ReplaceConfig":
        return ReplaceConfig(
            original_value=(
                global_variables.get(self.original_value, self.original_value)
                if self.original_value.startswith("$")
                else self.original_value
            ),
            new_value=(
                global_variables.get(self.new_value, self.new_value)
                if self.new_value.startswith("$")
                else self.new_value
            ),
            match_casing=self.match_casing,
        )


class FileType(str, Enum):
    file = "file"
    directory = "directory"


class FileClient:
    @abstractmethod
    async def load_file_str(self, path: str) -> str:
        raise NotImplementedError()

    @abstractmethod
    async def save_file_str(self, path: str, contents: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def validate_file(self, path: str) -> FileType:
        raise NotImplementedError()

    @abstractmethod
    async def get_all_files(self, directory: str) -> list[str]:
        raise NotImplementedError()

    async def copy_file(
        self,
        input_file_path: str,
        output_file_path: str,
        output_file_type: FileType,
        allow_overwrite: bool,
        replace_configs: list[ReplaceConfig],
    ) -> CopyStatus:
        async with OpsSemaphore:
            try:
                exists = (
                    await self.file_exists(output_file_path)
                    if output_file_type == FileType.file
                    else await self.directory_exists(output_file_path)
                )
                if not exists or allow_overwrite:
                    file_str = await self.load_file_str(input_file_path)
                    for replace_config in replace_configs:
                        file_str = self.replace_value(file_str, replace_config)
                    await self.save_file_str(output_file_path, file_str)
                    return CopyStatus.success
                else:
                    return CopyStatus.skip
            except Exception as e:
                logger.error(
                    f"ERROR: Failed to copy {input_file_path} to {output_file_path}: {e}"
                )
                return CopyStatus.fail

    @abstractmethod
    async def file_exists(self, path: str) -> bool:
        raise NotImplementedError()

    @abstractmethod
    async def directory_exists(self, path: str) -> bool:
        raise NotImplementedError()

    def replace_value(self, doc: str, replace_config: ReplaceConfig) -> str:
        if replace_config.match_casing:

            def replace(match):
                current = match.group()
                if current.xislower():
                    return replace_config.new_value.lower()
                elif current.isupper():
                    return replace_config.new_value.upper()
                elif current.istitle():
                    return replace_config.new_value.title()
                else:
                    return replace_config.new_value

            replaced_doc = re.sub(
                re.escape(replace_config.original_value),
                replace,
                doc,
                flags=re.IGNORECASE if replace_config.match_casing else 0,
            )
        else:
            replaced_doc = doc.replace(
                replace_config.original_value, replace_config.new_value
            )
        return replaced_doc


class FileClientType(str, Enum):
    local = "local"
