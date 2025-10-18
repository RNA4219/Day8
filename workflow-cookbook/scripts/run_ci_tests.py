#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
LOG_DIR = Path("workflow-cookbook/logs")
LOG_FILE = LOG_DIR / "test.jsonl"


def write_output(had_failures: bool) -> None:
    output = os.environ.get("GITHUB_OUTPUT")
    if not output:
        return
    with open(output, "a", encoding="utf-8") as handle:
        handle.write(f"had_failures={'true' if had_failures else 'false'}\n")


def log_entry(name: str, status: str, duration_ms: int) -> None:
    entry = {"name": name, "status": status, "duration_ms": duration_ms}
    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, separators=(",", ":")))
        handle.write("\n")


def ensure_log(reset: bool) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    if reset:
        LOG_FILE.write_text("", encoding="utf-8")
    else:
        LOG_FILE.touch()


def gather_node_suites() -> list[tuple[str, Path]]:
    suites: list[tuple[str, Path]] = []
    if Path("package.json").is_file():
        suites.append(("node::root", Path(".")))
    frontend = Path("frontend/package.json")
    if frontend.is_file():
        suites.append(("node::frontend", frontend.parent))
    packages_root = Path("packages")
    if packages_root.is_dir():
        for pkg_json in sorted(packages_root.glob("*/package.json")):
            suite_dir = pkg_json.parent
            suites.append((f"node::{suite_dir.as_posix()}", suite_dir))
    return suites


def run_node() -> bool:
    suites = gather_node_suites()
    if not suites:
        log_entry("node::noop", "pass", 0)
        return False

    had_failures = False
    env = os.environ.copy()
    env.setdefault("CI", "true")

    for name, path in suites:
        print(f"::group::npm test ({path.as_posix()})")
        start = time.monotonic()
        ci_result = subprocess.run(["npm", "ci"], cwd=str(path), env=env, check=False)
        test_ok = False
        if ci_result.returncode == 0:
            test_result = subprocess.run(["npm", "test"], cwd=str(path), env=env, check=False)
            test_ok = test_result.returncode == 0
        duration_ms = int(round((time.monotonic() - start) * 1000))
        status = "pass" if ci_result.returncode == 0 and test_ok else "fail"
        log_entry(name, status, duration_ms)
        print("::endgroup::")
        if status == "fail":
            had_failures = True
    return had_failures


def has_python_target(directory: Path) -> bool:
    if not directory.exists():
        return False
    if (directory / "pyproject.toml").is_file():
        return True
    return any(directory.glob("requirements*.txt"))


def gather_python_suites() -> list[tuple[str, Path]]:
    suites: list[tuple[str, Path]] = []
    root_dir = Path(".")
    if has_python_target(root_dir):
        suites.append(("python::root", root_dir))
    backend_dir = Path("backend")
    if has_python_target(backend_dir):
        suites.append(("python::backend", backend_dir))
    return suites


def install_python_deps(directory: Path) -> bool:
    ok = True
    for req in sorted(directory.glob("requirements*.txt")):
        result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(req)], check=False)
        ok = ok and result.returncode == 0
    if (directory / "pyproject.toml").is_file():
        result = subprocess.run([sys.executable, "-m", "pip", "install", str(directory.resolve())], check=False)
        ok = ok and result.returncode == 0
    return ok


def run_python() -> bool:
    suites = gather_python_suites()
    if not suites:
        log_entry("python::noop", "pass", 0)
        return False

    had_failures = False
    for name, path in suites:
        print(f"::group::pytest ({path.as_posix()})")
        start = time.monotonic()
        deps_ok = install_python_deps(path)
        test_result = subprocess.run([sys.executable, "-m", "pytest"], cwd=str(path), check=False)
        status = "pass" if deps_ok and test_result.returncode == 0 else "fail"
        duration_ms = int(round((time.monotonic() - start) * 1000))
        log_entry(name, status, duration_ms)
        print("::endgroup::")
        if status == "fail":
            had_failures = True
    return had_failures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("node", "python"), required=True)
    parser.add_argument("--reset-log", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ensure_log(args.reset_log)
    if args.mode == "node":
        failures = run_node()
    else:
        failures = run_python()
    write_output(failures)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
