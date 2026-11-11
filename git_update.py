"""Safe fast-forward updater shared by startup, watchdog, and CLI entry points."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from threading import Lock


DEFAULT_BRANCH = "main"
GIT_TIMEOUT_SECONDS = 60
_UPDATE_LOCK = Lock()


@dataclass(frozen=True)
class GitUpdateResult:
    success: bool
    updated: bool
    message: str
    commit: str = ""


def find_repository_root() -> Path | None:
    """Find the checkout containing this project, independent of launch CWD."""
    project_dir = Path(__file__).resolve().parent
    for candidate in (project_dir, *project_dir.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def _run_git(repo_dir: Path, *args: str) -> str:
    env = os.environ.copy()
    env.update({
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_PAGER": "cat",
        "GIT_EDITOR": "true",
    })
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            timeout=GIT_TIMEOUT_SECONDS,
            env=env,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("Git is not installed or is not available on PATH.") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"Git command timed out after {GIT_TIMEOUT_SECONDS} seconds.") from exc

    output = result.stdout.strip()
    if result.returncode != 0:
        detail = result.stderr.strip() or output or f"git {' '.join(args)} failed."
        raise RuntimeError(detail)
    return output


def _dirty_project_files(repo_dir: Path) -> list[str]:
    """Return tracked and untracked, non-ignored changes without touching them."""
    status = _run_git(repo_dir, "status", "--porcelain=v1", "--untracked-files=all")
    dirty = []
    for line in status.splitlines():
        path = line[3:].strip() if len(line) > 3 else ""
        if " -> " in path:  # Rename entries include both paths in porcelain output.
            path = path.split(" -> ", 1)[-1]
        if path:
            dirty.append(path)
    return dirty


def _stash_changes(repo_dir: Path, dirty_files: list[str]) -> str | None:
    """Stash local tracked/untracked edits, leaving ignored files (such as .env) alone."""
    if not dirty_files:
        return None

    previous_stashes = _run_git(repo_dir, "stash", "list", "--format=%H").splitlines()
    _run_git(
        repo_dir,
        "stash",
        "push",
        "--include-untracked",
        "--message",
        "Zyuna automatic update backup",
    )
    current_stashes = _run_git(repo_dir, "stash", "list", "--format=%H").splitlines()
    new_stash = current_stashes[0] if current_stashes and (
        len(current_stashes) > len(previous_stashes)
        or current_stashes[0] != (previous_stashes[0] if previous_stashes else "")
    ) else None

    if _dirty_project_files(repo_dir):
        if new_stash:
            try:
                _apply_stash(repo_dir, new_stash)
                _drop_stash(repo_dir, new_stash)
            except RuntimeError as exc:
                raise RuntimeError(
                    f"Git could not safely stash all local edits; backup {new_stash[:10]} "
                    f"was retained. Recovery detail: {exc}"
                ) from exc
        return None

    if new_stash:
        return new_stash
    return None


def _apply_stash(repo_dir: Path, stash_hash: str) -> None:
    _run_git(repo_dir, "stash", "apply", "--index", stash_hash)


def _drop_stash(repo_dir: Path, stash_hash: str) -> bool:
    """Drop only the stash created by this update, if it still exists."""
    try:
        entries = _run_git(repo_dir, "stash", "list", "--format=%gd %H").splitlines()
        for entry in entries:
            selector, _, commit = entry.partition(" ")
            if commit == stash_hash:
                _run_git(repo_dir, "stash", "drop", selector)
                return True
    except RuntimeError:
        # Restored edits are safe even if Git cannot remove their backup entry.
        pass
    return False


def _conflicted_files(repo_dir: Path) -> list[str]:
    status = _run_git(repo_dir, "status", "--porcelain=v1", "--untracked-files=all")
    return [line[3:].strip() for line in status.splitlines() if line[:2] in ("AA", "AU", "DD", "DU", "UA", "UD", "UU")]


def _sync_repository_locked() -> GitUpdateResult:
    repo_dir = find_repository_root()
    if repo_dir is None:
        return GitUpdateResult(False, False, "No Git checkout found; automatic update skipped.")

    try:
        branch = _run_git(repo_dir, "branch", "--show-current")
        if branch != DEFAULT_BRANCH:
            return GitUpdateResult(
                False,
                False,
                f"Update skipped: this checkout is on '{branch or 'detached HEAD'}', expected '{DEFAULT_BRANCH}'.",
            )

        _run_git(repo_dir, "remote", "get-url", "origin")
        _run_git(repo_dir, "fetch", "--quiet", "origin", DEFAULT_BRANCH)

        ahead_behind = _run_git(
            repo_dir,
            "rev-list",
            "--left-right",
            "--count",
            f"HEAD...origin/{DEFAULT_BRANCH}",
        ).split()
        if len(ahead_behind) != 2:
            return GitUpdateResult(False, False, "Could not determine whether origin/main has updates.")
        local_commits, incoming_commits = map(int, ahead_behind)
        if local_commits:
            return GitUpdateResult(
                False,
                False,
                "Update skipped: this checkout has local commits that are not on origin/main. "
                "Fast-forward updates cannot safely combine diverged commits.",
            )
        if incoming_commits == 0:
            commit = _run_git(repo_dir, "log", "-1", "--format=%h - %s")
            return GitUpdateResult(True, False, "Already up to date.", commit)

        dirty_files = _dirty_project_files(repo_dir)
        stash_hash = _stash_changes(repo_dir, dirty_files)
        if dirty_files and stash_hash is None:
            return GitUpdateResult(
                False,
                False,
                "Could not create a temporary backup of local changes; no update was applied.",
            )

        previous_commit = _run_git(repo_dir, "rev-parse", "HEAD")
        try:
            output = _run_git(repo_dir, "merge", "--ff-only", f"origin/{DEFAULT_BRANCH}")
        except RuntimeError as exc:
            if stash_hash:
                try:
                    _apply_stash(repo_dir, stash_hash)
                    _drop_stash(repo_dir, stash_hash)
                except RuntimeError as restore_error:
                    return GitUpdateResult(
                        False,
                        False,
                        f"Update failed: {exc}. Local changes remain backed up in Git stash "
                        f"{stash_hash[:10]}, but automatic restoration failed: {restore_error}",
                    )
            return GitUpdateResult(False, False, str(exc))

        if stash_hash:
            try:
                _apply_stash(repo_dir, stash_hash)
            except RuntimeError as restore_error:
                conflicts = _conflicted_files(repo_dir)
                conflict_preview = ", ".join(conflicts[:5]) or str(restore_error)
                if len(conflicts) > 5:
                    conflict_preview += f", and {len(conflicts) - 5} more"

                # The original changes are safely in the stash. Roll back only the
                # fast-forward just made, then restore them against their original base.
                try:
                    _run_git(repo_dir, "reset", "--hard", previous_commit)
                    _apply_stash(repo_dir, stash_hash)
                    _drop_stash(repo_dir, stash_hash)
                except RuntimeError as rollback_error:
                    return GitUpdateResult(
                        False,
                        False,
                        f"The update conflicted with local files ({conflict_preview}). The update "
                        f"was rolled back where possible; local changes are backed up in Git stash "
                        f"{stash_hash[:10]}. Recovery error: {rollback_error}",
                    )

                return GitUpdateResult(
                    False,
                    False,
                    f"Update not applied because incoming changes conflict with local files: "
                    f"{conflict_preview}. The update was rolled back and local changes restored. "
                    "Commit/push the local edits or use a clean checkout, then retry.",
                )

            stash_removed = _drop_stash(repo_dir, stash_hash)

        current_commit = _run_git(repo_dir, "rev-parse", "HEAD")
        commit = _run_git(repo_dir, "log", "-1", "--format=%h - %s")
        updated = current_commit != previous_commit
        message = output or "Updated to the latest commit."
        if stash_hash:
            message += " Local changes were restored after the update."
            if not stash_removed:
                message += f" Safety backup remains in Git stash {stash_hash[:10]}."
        return GitUpdateResult(True, updated, message, commit)
    except RuntimeError as exc:
        return GitUpdateResult(False, False, str(exc))
    except OSError as exc:
        return GitUpdateResult(False, False, f"Could not run Git: {exc}")


def sync_repository() -> GitUpdateResult:
    """Fast-forward the main checkout while preserving local changes."""
    if not _UPDATE_LOCK.acquire(blocking=False):
        return GitUpdateResult(False, False, "Another Git update is already running.")
    try:
        return _sync_repository_locked()
    finally:
        _UPDATE_LOCK.release()


def main() -> int:
    result = sync_repository()
    prefix = "Updated" if result.success and result.updated else "Up to date" if result.success else "Update skipped/failed"
    print(f"{prefix}: {result.message}")
    if result.commit:
        print(f"Current commit: {result.commit}")
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
