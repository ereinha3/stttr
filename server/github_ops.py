"""Git operations for committing and pushing generated artifacts."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Iterable

from server.settings import REPO_ROOT


class GitError(RuntimeError):
    pass


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise GitError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def configure_user() -> None:
    name = os.getenv("GIT_AUTHOR_NAME")
    email = os.getenv("GIT_AUTHOR_EMAIL")
    if name:
        _git("config", "user.name", name)
    if email:
        _git("config", "user.email", email)


def add_files(paths: Iterable[Path]) -> None:
    rel_paths = [str(path.relative_to(REPO_ROOT)) for path in paths]
    if rel_paths:
        _git("add", *rel_paths)


def commit(message: str) -> None:
    try:
        _git("commit", "-m", message)
    except GitError as exc:
        if "nothing to commit" not in str(exc).lower():
            raise


def push(remote: str | None = None, branch: str | None = None) -> None:
    remote = remote or os.getenv("GIT_REMOTE", "origin")
    branch = branch or os.getenv("GIT_BRANCH", "main")
    _git("push", remote, branch)


__all__ = ["configure_user", "add_files", "commit", "push", "GitError"]

