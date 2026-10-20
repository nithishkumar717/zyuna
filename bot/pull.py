#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════════╗
# ║                  Zyuna - Standalone Updater                      ║
# ╚══════════════════════════════════════════════════════════════════╝

import os
import sys
import subprocess

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

REPO_URL = "https://github.com/nithishkumar717/zyuna.git"

def main():
    print("\033[36m==================================================\033[0m")
    print("\033[36m* Zyuna Standalone Updater / Git Sync Utility\033[0m")
    print("\033[36m==================================================\033[0m")

    # Locate repo directory (.git)
    repo_dir = None
    candidates = [
        os.getcwd(),
        os.path.dirname(os.path.abspath(__file__)),
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ]
    for d in candidates:
        if os.path.isdir(os.path.join(d, ".git")):
            repo_dir = d
            break

    if not repo_dir:
        repo_dir = os.getcwd()
        print(f"\033[33m* Initializing git repo in {repo_dir}...\033[0m")
        subprocess.run(["git", "init"], cwd=repo_dir, check=False)
        subprocess.run(["git", "remote", "add", "origin", REPO_URL], cwd=repo_dir, check=False)

    print(f"\033[34m* Repository directory: {repo_dir}\033[0m")
    print(f"\033[34m* Fetching latest changes from origin/main...\033[0m")

    # Abort any merge in progress to resolve unmerged files
    subprocess.run(["git", "merge", "--abort"], cwd=repo_dir, capture_output=True, text=True)

    # Fetch latest main from GitHub
    fetch = subprocess.run(["git", "fetch", "origin", "main"], cwd=repo_dir, capture_output=True, text=True)
    if fetch.returncode != 0:
        print(f"\033[31m* Git fetch failed: {fetch.stderr.strip()}\033[0m")
        sys.exit(1)

    # Force reset to origin/main (clears all conflict markers and unmerged files)
    reset = subprocess.run(["git", "reset", "--hard", "origin/main"], cwd=repo_dir, capture_output=True, text=True)
    if reset.returncode == 0:
        print(f"\033[32m* Successfully updated to latest origin/main:\033[0m")
        print(f"  {reset.stdout.strip()}")
    else:
        print(f"\033[31m* Reset failed: {reset.stderr.strip()}\033[0m")
        sys.exit(1)

    # Show current commit
    log = subprocess.run(["git", "log", "-1", "--oneline"], cwd=repo_dir, capture_output=True, text=True)
    print(f"\033[36m* Current Head: {log.stdout.strip()}\033[0m")
    print("\033[32m* Done! Your files are completely synchronized and ready to run.\033[0m")

if __name__ == "__main__":
    main()
