import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from pydantic import BaseModel, ConfigDict, Field

from .dependency_resolvers import (
    DependencyConfigs,
    DependencyGroup,
    DependencyKey,
    DependencyValue,
    resolve_dependencies,
)
from .file import CopyStatus, FileType, ReplaceConfig, get_file_client
from .utils import OpsSemaphore

logger = logging.getLogger("firestarter")

dependency_file_locks: dict[DependencyKey, asyncio.Lock] = {}
file_locks_lock = asyncio.Lock()


class Command(BaseModel):
    command: str
    not_run_check: Optional[str] = None


class StatusCounter(BaseModel):
    success: int = 0
    fail: int = 0
    skip: int = 0

    def update(self, statuses: list[CopyStatus]) -> None:
        for status in statuses:
            if status == CopyStatus.success:
                self.success += 1
            elif status == CopyStatus.fail:
                self.fail += 1
            elif status == CopyStatus.skip:
                self.skip += 1

    @classmethod
    def aggregate(cls, counters: list["StatusCounter"]) -> "StatusCounter":
        counter = cls()
        for c in counters:
            counter.success += c.success
            counter.fail += c.fail
            counter.skip += c.skip
        return counter

    def __str__(self) -> str:
        return f"[green]Success: {self.success}[/green], [red]Fail: {self.fail}[/red], [yellow]Skip: {self.skip}[/yellow]"


@asynccontextmanager
async def get_dependency_lock(
    dependency_key: DependencyKey,
) -> AsyncGenerator[asyncio.Lock, None]:
    async with file_locks_lock:
        if dependency_key not in dependency_file_locks:
            dependency_file_locks[dependency_key] = asyncio.Lock()

    yield dependency_file_locks[dependency_key]


class ResourceSettings(BaseModel):
    auto_overwrite: bool


class ResourceConfig(BaseModel):
    input_path: str
    dependencies: dict[DependencyKey, list[DependencyValue]] = Field(
        default_factory=dict
    )
    replace_configs: list[ReplaceConfig] = Field(default_factory=list)
    output_path: str
    auto_overwrite: Optional[bool] = None

    def resolve_settings(self, auto_overwrite: bool) -> ResourceSettings:
        return ResourceSettings(
            auto_overwrite=(
                auto_overwrite
                if self.auto_overwrite is None
                else self.auto_overwrite
            )
        )

    def _get_output_path(
        self,
        input_file_path: str,
        input_file_type: FileType,
        output_file_path: str,
        output_file_type: FileType,
    ) -> str:
        if input_file_type == FileType.directory:
            assert output_file_type == FileType.directory
            input_filename = input_file_path.split("/")[-1]
            return os.path.join(output_file_path, input_filename)
        elif input_file_type == FileType.file:
            if output_file_type == FileType.directory:
                input_filename = input_file_path.split("/")[-1]
                return os.path.join(output_file_path, input_filename)
            elif output_file_type == FileType.file:
                return output_file_path
            else:
                raise ValueError(f"Unknown file type: {output_file_type}")
        else:
            raise ValueError(f"Unknown file type: {input_file_type}")

    def _determine_output_file_type(
        self,
        input_file_path: str,
        input_file_type: FileType,
        output_file_path: str,
    ) -> FileType:
        if input_file_type == FileType.directory:
            logger.debug(
                "Input path is a directory, assuming output path is also a directory"
            )
            return FileType.directory

        output_path_end = output_file_path.split("/")[-1]
        output_ends_with_extension = "." in output_path_end
        if output_ends_with_extension:
            logger.debug(
                "Input path is a file and output path ends with extension, assuming output path is a file"
            )
            return FileType.file
        elif output_path_end == input_file_path.split("/")[-1]:
            logger.debug(
                "Output path is the same as input path, assuming output path is a file"
            )
            return FileType.file
        else:
            logger.debug(
                "Output path does not match input path and does not end with extension, assuming output path is a directory"
            )
            return FileType.directory

    async def process_resource(
        self,
        global_auto_overwrite: bool,
        global_variables: dict[str, str],
    ) -> StatusCounter:
        status_counter = StatusCounter()
        file_client = get_file_client(self.input_path)

        try:
            input_file_type = await file_client.validate_file(self.input_path)
        except FileNotFoundError:
            logger.error(f"ERROR: Input path {self.input_path} not found")
            status_counter.fail += 1
            return status_counter

        output_file_type = self._determine_output_file_type(
            self.input_path, input_file_type, self.output_path
        )

        if input_file_type == FileType.directory:
            files = await file_client.get_all_files(self.input_path)
        else:
            files = [self.input_path]

        settings_to_use = self.resolve_settings(
            auto_overwrite=global_auto_overwrite
        )
        replace_configs_to_use = [
            config.resolve(global_variables) for config in self.replace_configs
        ]

        file_to_process: list[tuple[str, str]] = [
            (
                file,
                self._get_output_path(
                    file, input_file_type, self.output_path, output_file_type
                ),
            )
            for file in files
        ]
        process_coros = [
            file_client.copy_file(
                input_file_path,
                output_file_path,
                output_file_type,
                settings_to_use.auto_overwrite,
                replace_configs_to_use,
            )
            for input_file_path, output_file_path in file_to_process
        ]
        copy_statuses = await asyncio.gather(*process_coros)
        status_counter.update(copy_statuses)

        return status_counter


class FireStarterConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    auto_overwrite: bool = False
    global_variables: dict[str, str] = Field(default_factory=dict)
    dependency_configs: DependencyConfigs = Field(
        default_factory=DependencyConfigs
    )
    resource_configs: list[ResourceConfig] = Field(default_factory=list)
    commands: list[Command] = Field(default_factory=list)

    async def process_dependency(
        self, dependency_name: str, dependency_group: DependencyGroup
    ) -> tuple[str, int]:
        file_client = get_file_client(dependency_group.output_file)
        file_type = await file_client.validate_file(
            dependency_group.output_file
        )
        if file_type == FileType.directory:
            raise ValueError(
                "Dependency output path is a directory, must be a file"
            )

        async with OpsSemaphore:
            async with get_dependency_lock(dependency_group.output_file):
                file_str = await file_client.load_file_str(
                    dependency_group.output_file
                )
                new_file_str, dependencies_updated = resolve_dependencies(
                    dependency_group, file_str
                )
                await file_client.save_file_str(
                    dependency_group.output_file, new_file_str
                )

        return dependency_name, dependencies_updated

    def process_commands(self) -> StatusCounter:
        status_counter = StatusCounter()
        for command in self.commands:
            try:
                if command.not_run_check is not None:
                    # run the command, if the check passes, then run otherwise skip
                    if os.system(command.not_run_check) == 0:
                        os.system(command.command)
                        status_counter.success += 1
                    else:
                        status_counter.skip += 1
                else:
                    os.system(command.command)
                    status_counter.success += 1
            except Exception as e:
                logger.error(
                    f"ERROR: Failed to run command: {command.command}, error: {e}"
                )
                status_counter.fail += 1

        return status_counter


async def execute_firestarter(
    config: FireStarterConfig, skip_commands: bool
) -> tuple[StatusCounter, list[tuple[str, int]], StatusCounter]:
    # process all files
    coros = [
        resource_config.process_resource(
            config.auto_overwrite, config.global_variables
        )
        for resource_config in config.resource_configs
    ]
    status_counters = await asyncio.gather(*coros)
    total_status_counter = StatusCounter.aggregate(status_counters)

    # gather dependencies
    dependency_groups: dict[str, DependencyGroup] = {}
    for resource_config in config.resource_configs:
        for (
            dependency_key,
            dependency_values,
        ) in resource_config.dependencies.items():
            if dependency_key not in dependency_groups:
                dependency_groups[dependency_key] = DependencyGroup(
                    output_file=config.dependency_configs[
                        dependency_key
                    ].output_file,
                    type=config.dependency_configs[dependency_key].type,
                    dependency_values=dependency_values,
                )
            else:
                dependency_groups[dependency_key].dependency_values.extend(
                    dependency_values,
                )

    resolver_coros = [
        config.process_dependency(dependency_name, group)
        for dependency_name, group in dependency_groups.items()
    ]
    dependencies_updated = await asyncio.gather(*resolver_coros)

    if skip_commands:
        commands_status_counter = StatusCounter(skip=len(config.commands))
    else:
        commands_status_counter = config.process_commands()

    return (
        total_status_counter,
        dependencies_updated,
        commands_status_counter,
    )
