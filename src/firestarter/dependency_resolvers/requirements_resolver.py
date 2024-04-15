import logging
import re
from collections import defaultdict

from packaging.specifiers import SpecifierSet

logger = logging.getLogger("firestarter")


def _parse_dependency(dependency: str) -> tuple[str, SpecifierSet]:
    """
    Parse a dependency string into a package name and its version specifier.
    If no version specifier is provided, return an empty SpecifierSet.
    """
    match = re.match(r"([^=<>!~]+)(.*)", dependency)
    if match:
        package_name, version_spec = match.groups()
        return (package_name.strip(), SpecifierSet(version_spec.strip()))
    return (dependency, SpecifierSet())


def resolver(
    new_dependencies: list[str], dependency_file: str
) -> tuple[str, int]:
    """
    Update the dependency file to include all deduped requirements,
    choosing the most restrictive requirement in the case of collisions.
    """
    packages_updated = 0

    # Parse existing dependencies from the file
    existing_dependencies = defaultdict(SpecifierSet)
    for line in dependency_file.splitlines():
        package, specifiers = _parse_dependency(line)
        existing_dependencies[package] = specifiers

    # Update with new dependencies
    for dep in new_dependencies:
        package, new_specifiers = _parse_dependency(dep)
        if package not in existing_dependencies:
            existing_dependencies[package] = new_specifiers
            packages_updated += 1
        else:
            logger.debug(
                f"Skipping {package} because it already exists in the file"
            )

    # Generate the updated dependency file content
    updated_dependencies = [
        f"{pkg}{ver}" for pkg, ver in existing_dependencies.items()
    ]
    return "\n".join(updated_dependencies), packages_updated
