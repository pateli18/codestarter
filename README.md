# CodeStarter

CodeStarter is a tool for assembling a repo using copy/paste. Inspired by the installation of components with [shadcn/ui](https://ui.shadcn.com/), CodeStarter allows you to easily bring in code and alter it without having to worry about assembling internal packages.

![Run](./images/run.gif)

## Contents

- [Quickstart](#quickstart)
- [Extensions](#extensions)

## Quickstart

### Installation

```bash
pip install codestarter[cli,local,pythondep]
```

- `cli`: Install the CLI
- `local`: Install the local file system extension
- `pythondep`: Install the python dependency extension

### Create a Config

Add a `codestarter.json` config to your project (we recommend the root of your project, but you can technically put it anywhere).

```json
{
  "auto_overwrite": false, // If true, the output file will be overwritten if it already exists. If false, the system will not overwrite the existing file. This can be overridden by the auto_overwrite flag in the resource_configs. Default is Fa
  "global_variables": {
    "$new_project_name": "codestarter" // global variables can be referenced within the resource_configs. The key must start with $.
  },
  "dependency_configs": {
    "requirements_config": {
      // The key is the name of the dependency config that will be referenced in the resource_configs.
      "type": "requirements.txt", // The type of the dependency resolver.
      "output_file": "./requirements.txt" // The actual path to the file that contains the dependency
    }
  },
  "resource_configs": [
    {
      "input_path": "../old_repo/.vscode/", // path to the file or directory that will be copied. if it's a directory, the entire directory will be copied.
      "output_path": "./.vscode/", // path to the file or directory that the input will be copied to. If it's a directory, the input filenames will be used
      "replace_configs": [
        {
          "original_value": "old_repo", // the value to be replaced within the file, can reference global variables.
          "new_value": "$new_project_name" // the value to replace the original value with, can reference global variables.
        }
      ],
      "dependencies": { "requirements_config": ["pandas>=1.0", "httpx"] }, // The dependencies to be installed. The key is the name of the dependency config that will be referenced in the resource_configs.
      "auto_overwrite": false // [OPTIONAL] If true, the output file will be overwritten if it already exists. If false, the system will prompt or skip the overwrite. If not provided, the value of "auto_overwrite" at the top level will be used.
    }
  ],
  "commands": [
    {
      "command": "uv venv", // The command to run.
      "not_run_check": "[[ -d .venv ]] && exit 1 || exit 0" // The command to run to check if the command should be run. If the command returns 0, the command will be run. If the command returns any other value, the command will not be run.
    }
  ]
}
```

### Run

Run the following command to assemble your repo. If you don't provide any options, the command assumes that there is a `codestarter.json` in the current directory. See `codestarter --help` for more options.

```bash
codestarter
```

## Extensions

### File

CodeStarter provides a file extension that allows you to read and store your files in the storage provider of your choice. Currently only `local` is supported. You can add other file config types by:

1. Adding a item to the [FlieClientType](./src/codestarter/file/utils.py#L126) class.
1. Adding a new class that inherits from [FileClient](./src/codestarter/file/utils.py#L45). See [local.py](./src/codestarter/file/local.py) for an example.
1. Updating `_determine_file_client_from_path` and `get_file_client` in [\_\_init\_\_.py](./src/codestarter/file/__init__.py).

### Dependency Resolvers

CodeStarter provides a dependency resolver extension that allows you to update dependencies in the dependency file of your choice. Currently only `requirements_resolver` (for python requirements.txt files) is supported. You can add other dependency resolvers by:

1. Adding a item to the [DependencyType](./src/codestarter/dependency_resolvers/utils.py#L9) class.
1. Adding a new file with a `resolver` function that has the following signature `def resolver(new_dependencies: list[str], dependency_file: str) -> tuple[str, int]:`. See [requirements_resolver.py](./src/codestarter/dependency_resolvers/requirements_resolver.py#L22) for an example.
1. Updating `resolve_dependencies` in [\_\_init\_\_.py](./src/codestarter/dependency_resolvers/__init__.py).
