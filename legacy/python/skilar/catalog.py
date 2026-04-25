"""Catalog loading and validation for clasing-skill."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import PackageDefinition


REQUIRED_PACKAGE_KEYS = {
    "displayName",
    "repoUrl",
    "adapter",
    "supportedTargets",
    "defaultVersion",
    "requiresNeurox",
    "installStrategy",
}


def load_catalog(path: Path) -> dict[str, PackageDefinition]:
    """Load and validate the package catalog from a JSON file.

    Args:
        path: Path to the catalog.json file.

    Returns:
        Dictionary mapping package IDs to PackageDefinition objects.

    Raises:
        ValueError: If the catalog is malformed or missing required keys.
        FileNotFoundError: If the catalog file does not exist.
    """
    with open(path, encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Catalog at {path} must be a JSON object")

    if "version" not in data:
        raise ValueError(f"Catalog at {path} missing required field: version")

    if "packages" not in data:
        raise ValueError(f"Catalog at {path} missing required field: packages")

    packages_data = data["packages"]
    if not isinstance(packages_data, dict):
        raise ValueError(f"Catalog at {path} 'packages' must be an object")

    result: dict[str, PackageDefinition] = {}

    for package_id, package_data in packages_data.items():
        if not isinstance(package_data, dict):
            raise ValueError(f"Package '{package_id}' must be an object")

        missing_keys = REQUIRED_PACKAGE_KEYS - set(package_data.keys())
        if missing_keys:
            raise ValueError(
                f"Package '{package_id}' missing required keys: {sorted(missing_keys)}"
            )

        supported_targets = package_data["supportedTargets"]
        if not isinstance(supported_targets, list):
            raise ValueError(
                f"Package '{package_id}' supportedTargets must be an array"
            )

        result[package_id] = PackageDefinition(
            id=package_id,
            display_name=package_data["displayName"],
            repo_url=package_data["repoUrl"],
            adapter=package_data["adapter"],
            supported_targets=tuple(supported_targets),
            default_version=package_data["defaultVersion"],
            requires_neurox=package_data["requiresNeurox"],
            install_strategy=package_data["installStrategy"],
        )

    return result
