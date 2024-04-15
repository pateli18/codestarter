from .utils import (
    DependencyConfig,
    DependencyConfigs,
    DependencyGroup,
    DependencyKey,
    DependencyType,
    DependencyValue,
)


def resolve_dependencies(
    dependency_group: DependencyGroup, file_str: str
) -> tuple[str, int]:
    if dependency_group.type == DependencyType.requirements:
        from .requirements_resolver import resolver

        new_file, packages_updated = resolver(
            dependency_group.dependency_values, file_str
        )
    else:
        raise ValueError(
            f"Unknown dependency resolver type {dependency_group.type}"
        )

    return new_file, packages_updated


__all__ = [
    "DependencyConfig",
    "DependencyConfigs",
    "DependencyGroup",
    "DependencyKey",
    "DependencyType",
    "DependencyValue",
    "resolve_dependencies",
]
