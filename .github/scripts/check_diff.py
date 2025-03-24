import glob
import json
import os
import sys
from collections import defaultdict
from typing import Dict, List, Set
from pathlib import Path
import tomllib

from get_min_versions import get_min_version_from_toml


# Updated for langchain-couchbase structure
LANGCHAIN_DIRS = [
    ".",  # Root directory containing the main package
]

# when set to True, we are ignoring core dependents
# in order to be able to get CI to pass for each individual
# package that depends on core
# e.g. if you touch core, we don't then add textsplitters/etc to CI
IGNORE_CORE_DEPENDENTS = False

# ignored partners are removed from dependents
# but still run if directly edited
IGNORED_PARTNERS = []

PY_312_MAX_PACKAGES = []


def all_package_dirs() -> Set[str]:
    # For langchain-couchbase, we only have the main package
    return {"."}


def dependents_graph() -> dict:
    """
    Construct a mapping of package -> dependents, such that we can
    run tests on all dependents of a package when a change is made.
    """
    # For langchain-couchbase, we only have the main package
    dependents = defaultdict(set)
    dependents["langchain-couchbase"] = {"."}
    return dependents


def add_dependents(dirs_to_eval: Set[str], dependents: dict) -> List[str]:
    # For langchain-couchbase, we just return the main directory
    return ["."]


def _get_configs_for_single_dir(job: str, dir_: str) -> List[Dict[str, str]]:
    if job == "test-pydantic":
        return _get_pydantic_test_configs(dir_)

    # For langchain-couchbase, use Python versions that should be supported
    py_versions = ["3.9", "3.10", "3.11"]
    
    return [{"working-directory": dir_, "python-version": py_v} for py_v in py_versions]


def _get_pydantic_test_configs(
    dir_: str, *, python_version: str = "3.11"
) -> List[Dict[str, str]]:
    import os.path

    # For langchain-couchbase, just check the main poetry.lock
    poetry_lock_path = "./poetry.lock"
    if not os.path.exists(poetry_lock_path):
        # If the poetry.lock file doesn't exist, use default values
        max_pydantic_minor = "0"
    else:
        with open(poetry_lock_path, "rb") as f:
            poetry_lock_data = tomllib.load(f)
        for package in poetry_lock_data["package"]:
            if package["name"] == "pydantic":
                max_pydantic_minor = package["version"].split(".")[1]
                break
        else:
            max_pydantic_minor = "0"  # Default if pydantic not found in lock

    # Check for pydantic in pyproject.toml
    pyproject_path = "./pyproject.toml"
    if os.path.exists(pyproject_path):
        try:
            min_pydantic_version = get_min_version_from_toml(
                pyproject_path, "release", python_version, include=["pydantic"]
            ).get("pydantic", "0.0.0")
        except:
            # If get_min_version_from_toml fails, use default
            min_pydantic_version = "0.0.0"
    else:
        min_pydantic_version = "0.0.0"
    
    min_pydantic_minor = (
        min_pydantic_version.split(".")[1]
        if "." in min_pydantic_version
        else "0"
    )

    # Convert to integers for comparison
    try:
        max_pydantic_minor_int = int(max_pydantic_minor)
    except ValueError:
        max_pydantic_minor_int = 0
        
    try:
        min_pydantic_minor_int = int(min_pydantic_minor)
    except ValueError:
        min_pydantic_minor_int = 0

    # Ensure min is not greater than max
    if min_pydantic_minor_int > max_pydantic_minor_int:
        min_pydantic_minor_int = max_pydantic_minor_int

    configs = [
        {
            "working-directory": dir_,
            "pydantic-version": f"2.{v}.0",
            "python-version": python_version,
        }
        for v in range(min_pydantic_minor_int, max_pydantic_minor_int + 1)
    ]
    
    # If no configs were generated, add at least one
    if not configs:
        configs = [
            {
                "working-directory": dir_,
                "pydantic-version": "2.0.0",
                "python-version": python_version,
            }
        ]
    
    return configs


def _get_configs_for_multi_dirs(
    job: str, dirs_to_run: Dict[str, Set[str]], dependents: dict
) -> List[Dict[str, str]]:
    # For langchain-couchbase, we just use the main directory
    return _get_configs_for_single_dir(job, ".")


if __name__ == "__main__":
    files = sys.argv[1:]

    dirs_to_run: Dict[str, set] = {
        "lint": {"."},  # Always run lint on the main directory
        "test": {"."},  # Always run tests on the main directory
        "extended-test": set(),  # No extended tests for now
    }
    docs_edited = False

    # For langchain-couchbase, run tests on main directory for any file changes
    if files:
        for file in files:
            if file.startswith("docs/"):
                docs_edited = True
    
    dependents = dependents_graph()

    # we now have dirs_by_job
    map_job_to_configs = {
        job: _get_configs_for_multi_dirs(job, dirs_to_run, dependents)
        for job in [
            "lint",
            "test",
            "extended-tests",
            "compile-integration-tests",
            "dependencies",
            "test-pydantic",
        ]
    }
    # No doc imports test for now
    map_job_to_configs["test-doc-imports"] = []

    for key, value in map_job_to_configs.items():
        json_output = json.dumps(value)
        print(f"{key}={json_output}")
