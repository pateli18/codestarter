import asyncio
import json
from typing import Annotated

import typer
from rich import print

from .executor import FireStarterConfig, execute_firestarter
from .file import get_file_client

app = typer.Typer(no_args_is_help=True)


@app.command()
def run(
    file: Annotated[
        str, typer.Option(help="path to firestarter.json file")
    ] = "./firestarter.json",
    skip_commands: Annotated[
        bool, typer.Option(help="don't run commands")
    ] = False,
):
    file_client = get_file_client(file)
    file_str = asyncio.run(file_client.load_file_str(file))
    file_config_raw = json.loads(file_str)
    file_config = FireStarterConfig(**file_config_raw)
    print(":fire: firestarter starting :fire:")
    copy_status_counter, dependencies_updated, command_status_counter = (
        asyncio.run(
            execute_firestarter(file_config, skip_commands=skip_commands)
        )
    )
    dependencies_updated = ", ".join(
        f"[green]{dependency_name}: {dependencies_updated}[/green]"
        for dependency_name, dependencies_updated in dependencies_updated
        if dependencies_updated > 0
    )

    print(f"Copy Status: {copy_status_counter}")
    if dependencies_updated:
        print(f"Dependencies Updated: {dependencies_updated}")
    print(f"Command Status: {command_status_counter}")
    print(":fire: firestarter finished :fire:")


if __name__ == "__main__":
    app()
