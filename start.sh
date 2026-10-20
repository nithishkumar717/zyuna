#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════════╗
# ║                  Zyuna - Auto-Update & Startup                   ║
# ╚══════════════════════════════════════════════════════════════════╝

set -e

# Pull latest updates from GitHub with self-healing fallback
if command -v git &> /dev/null; then
    if [ -d ".git" ] || [ -d "../.git" ]; then
        echo "◈ Pulling latest updates from GitHub..."
        git fetch origin main --quiet || true
        git merge --abort 2>/dev/null || true
        git reset --hard origin/main 2>/dev/null || git pull origin main || echo "◈ Warning: Git pull failed, starting with current files..."
    fi
fi

# Run Zyuna
echo "◈ Starting Zyuna..."
python zyuna.py
