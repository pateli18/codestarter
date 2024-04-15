# FireStarter

FireStarter is a tool for assembling a repo using copy / paste. Inspired by the installation of components with [shadcn/ui](https://ui.shadcn.com/), FireStarter allows you to bring in easily bring in code and alter it without having to worry about assembling internal packages.

## Quickstart

### Installation

```bash
pip install firestarter[cli,local,pythondep]
```

- `cli`: Install the CLI
- `local`: Install the local file system extension
- `pythondep`: Install the python dependency extension

### Create a Config

### Run

## Extensions

### File

FireStarter provides a file extension that allows you to read and store your files in the storage provider of your choice. Currently only `local` is supported. You can add other file config types by:

1. Adding a item to the [FlieClientType](./src/firestarter/file/utils.py#L126) class.
1. Adding a new class that inherits from [FileClient](./src/firestarter/file/utils.py#L45). See [local.py](./src/firestarter/file/local.py) for an example.
1. Updating `_determine_file_client_from_path` and `get_file_client` in [\_\_init\_\_.py](./src/firestarter/file/__init__.py).

### Dependency Resolvers

FireStarter provides a dependency resolver extension that allows you to update dependencies in the dependency file of your choice. Currently only `requirements_resolver` (for python requirements.txt files) is supported. You can add other dependency resolvers by:

1. Adding a item to the [DependencyType](./src/firestarter/dependency_resolvers/utils.py#L9) class.
1. Adding a new file with a `resolver` function that has the following signature `def resolver(new_dependencies: list[str], dependency_file: str) -> tuple[str, int]:`. See [requirements_resolver.py](./src/firestarter/dependency_resolvers/requirements_resolver.py#L22) for an example.
1. Updating `resolve_dependencies` in [\_\_init\_\_.py](./src/firestarter/dependency_resolvers/__init__.py).
