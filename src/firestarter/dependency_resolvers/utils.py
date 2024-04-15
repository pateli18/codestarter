from enum import Enum

from pydantic import BaseModel

DependencyKey = str
DependencyValue = str


class DependencyType(str, Enum):
    requirements = "requirements.txt"
    pyproject = "pyproject.toml"
    package = "package.json"


class DependencyConfig(BaseModel):
    output_file: str
    type: DependencyType


DependencyConfigs = dict[DependencyKey, DependencyConfig]


class DependencyGroup(DependencyConfig):
    dependency_values: list[DependencyValue]
