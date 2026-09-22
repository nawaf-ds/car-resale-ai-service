from __future__ import annotations

import subprocess
import sys
from pathlib import Path

EXCLUDED_FILES = (
    r"(^|/)(artifacts/model\.joblib|data/snapshot/cars\.csv|reports/figures/.*\.png)$"
)
EXCLUDED_SECRETS = (
    r"^(25854afc3ef8b6c6a0349bf7f422c40dacb9bec60a8b318462737ebf9edcc5ea|"
    r"31aa9866a94fe07485025cadc715282484601ef0224f2d09ed8689116b95c005)$"
)


def run(command: list[str], input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        input=input_text,
        capture_output=True,
        check=False,
        text=True,
        encoding="utf-8",
    )


def scan_files(paths: list[str]) -> subprocess.CompletedProcess[str]:
    return run(
        [
            sys.executable,
            "-m",
            "detect_secrets.pre_commit_hook",
            "--json",
            "--cores",
            "1",
            "--no-verify",
            "--exclude-files",
            EXCLUDED_FILES,
            "--exclude-secrets",
            EXCLUDED_SECRETS,
            *paths,
        ]
    )


def scan_current_tree() -> None:
    listed = run(["git", "ls-files", "--cached", "--others", "--exclude-standard"])
    if listed.returncode != 0:
        raise RuntimeError(listed.stderr.strip() or "Unable to list repository files")
    repository_files = [
        path
        for path in listed.stdout.splitlines()
        if path
        and path != "artifacts/model.joblib"
        and path != "data/snapshot/cars.csv"
        and not path.startswith("reports/figures/")
    ]
    result = scan_files(repository_files)
    if result.returncode != 0:
        print(result.stdout)
        raise RuntimeError(result.stderr.strip() or "Potential secret in current tree")


def scan_git_history() -> None:
    history = run(
        [
            "git",
            "log",
            "-p",
            "--all",
            "--no-ext-diff",
            "--",
            ".",
            ":(exclude)artifacts/model.joblib",
            ":(exclude)data/snapshot/cars.csv",
            ":(exclude)reports/figures",
        ]
    )
    if history.returncode != 0:
        raise RuntimeError(history.stderr.strip() or "Unable to read Git history")
    history_path = Path("tmp") / "secret-history.patch"
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.write_text(history.stdout, encoding="utf-8")
    try:
        result = scan_files([str(history_path)])
    finally:
        history_path.unlink(missing_ok=True)
    if result.returncode != 0:
        print(result.stdout)
        raise RuntimeError(result.stderr.strip() or "Potential secret in Git history")


def main() -> None:
    scan_current_tree()
    print("current_tree_findings=0")
    scan_git_history()
    print("git_history_findings=0")


if __name__ == "__main__":
    main()
