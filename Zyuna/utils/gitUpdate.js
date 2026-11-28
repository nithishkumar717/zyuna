const { execFileSync, spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const DEFAULT_BRANCH = 'main';
const GIT_TIMEOUT_MS = 60_000;
const DEFAULT_INTERVAL_MS = 30 * 60 * 1000; // 30 minutes
const DEFAULT_INITIAL_DELAY_MS = 5 * 60 * 1000; // 5 minutes

let isUpdating = false;
let watchdogTimer = null;
let initialDelayTimer = null;

function findRepositoryRoot(startDir = __dirname) {
    let current = path.resolve(startDir);
    while (true) {
        if (fs.existsSync(path.join(current, '.git'))) {
            return current;
        }
        const parent = path.dirname(current);
        if (parent === current) {
            return null;
        }
        current = parent;
    }
}

function runGit(repoDir, args) {
    try {
        const output = execFileSync('git', args, {
            cwd: repoDir,
            encoding: 'utf8',
            timeout: GIT_TIMEOUT_MS,
            stdio: ['ignore', 'pipe', 'pipe'],
            env: {
                ...process.env,
                GIT_TERMINAL_PROMPT: '0',
                GIT_PAGER: 'cat',
                GIT_EDITOR: 'true'
            }
        });
        return (output || '').trim();
    } catch (error) {
        if (error.code === 'ENOENT') {
            throw new Error('Git is not installed or is not available on PATH.');
        }
        const stderr = error.stderr ? String(error.stderr).trim() : '';
        const stdout = error.stdout ? String(error.stdout).trim() : '';
        throw new Error(stderr || stdout || error.message || `git ${args.join(' ')} failed.`);
    }
}

function getDirtyProjectFiles(repoDir) {
    const status = runGit(repoDir, ['status', '--porcelain=v1', '--untracked-files=all']);
    if (!status) return [];
    const dirty = [];
    for (const line of status.split(/\r?\n/)) {
        let filePath = line.length > 3 ? line.slice(3).trim() : '';
        if (filePath.includes(' -> ')) {
            filePath = filePath.split(' -> ').pop().trim();
        }
        if (filePath) dirty.push(filePath);
    }
    return dirty;
}

function getConflictedFiles(repoDir) {
    const status = runGit(repoDir, ['status', '--porcelain=v1', '--untracked-files=all']);
    if (!status) return [];
    const conflictCodes = new Set(['AA', 'AU', 'DD', 'DU', 'UA', 'UD', 'UU']);
    return status
        .split(/\r?\n/)
        .filter((line) => conflictCodes.has(line.slice(0, 2)))
        .map((line) => line.slice(3).trim());
}

function applyStash(repoDir, stashHash) {
    runGit(repoDir, ['stash', 'apply', '--index', stashHash]);
}

function dropStash(repoDir, stashHash) {
    try {
        const entries = runGit(repoDir, ['stash', 'list', '--format=%gd %H']).split(/\r?\n/);
        for (const entry of entries) {
            const spaceIdx = entry.indexOf(' ');
            if (spaceIdx === -1) continue;
            const selector = entry.slice(0, spaceIdx);
            const commit = entry.slice(spaceIdx + 1).trim();
            if (commit === stashHash) {
                runGit(repoDir, ['stash', 'drop', selector]);
                return true;
            }
        }
    } catch {
        // Restored edits are safe even if Git cannot drop the backup stash.
    }
    return false;
}

function stashChanges(repoDir, dirtyFiles) {
    if (!dirtyFiles.length) return null;

    const previousStashes = runGit(repoDir, ['stash', 'list', '--format=%H']).split(/\r?\n/).filter(Boolean);
    runGit(repoDir, ['stash', 'push', '--include-untracked', '--message', 'Zyuna automatic update backup']);
    const currentStashes = runGit(repoDir, ['stash', 'list', '--format=%H']).split(/\r?\n/).filter(Boolean);

    const newStash =
        currentStashes.length &&
        (currentStashes.length > previousStashes.length || currentStashes[0] !== (previousStashes[0] || ''))
            ? currentStashes[0]
            : null;

    if (getDirtyProjectFiles(repoDir).length > 0 && newStash) {
        try {
            applyStash(repoDir, newStash);
            dropStash(repoDir, newStash);
        } catch (restoreError) {
            throw new Error(
                `Git could not safely stash all local edits; backup ${newStash.slice(0, 10)} retained. Detail: ${restoreError.message}`
            );
        }
        return null;
    }

    return newStash;
}

function syncRepository(branch = DEFAULT_BRANCH) {
    if (isUpdating) {
        return { success: false, updated: false, message: 'Another Git update is already running.', commit: '' };
    }
    isUpdating = true;

    try {
        const repoDir = findRepositoryRoot();
        if (!repoDir) {
            return { success: false, updated: false, message: 'No Git checkout found; automatic update skipped.', commit: '' };
        }

        const currentBranch = runGit(repoDir, ['branch', '--show-current']);
        if (currentBranch !== branch) {
            return {
                success: false,
                updated: false,
                message: `Update skipped: checkout is on '${currentBranch || 'detached HEAD'}', expected '${branch}'.`,
                commit: ''
            };
        }

        runGit(repoDir, ['remote', 'get-url', 'origin']);
        runGit(repoDir, ['fetch', '--quiet', 'origin', branch]);

        const counts = runGit(repoDir, ['rev-list', '--left-right', '--count', `HEAD...origin/${branch}`]).split(/\s+/);
        if (counts.length !== 2) {
            return { success: false, updated: false, message: `Could not determine whether origin/${branch} has updates.`, commit: '' };
        }

        const localCommits = Number(counts[0]);
        const incomingCommits = Number(counts[1]);

        if (localCommits > 0) {
            return {
                success: false,
                updated: false,
                message: `Update skipped: checkout has ${localCommits} local commit(s) not on origin/${branch}.`,
                commit: ''
            };
        }

        if (incomingCommits === 0) {
            const commit = runGit(repoDir, ['log', '-1', '--format=%h - %s']);
            return { success: true, updated: false, message: 'Already up to date.', commit };
        }

        const dirtyFiles = getDirtyProjectFiles(repoDir);
        const stashHash = stashChanges(repoDir, dirtyFiles);
        if (dirtyFiles.length && !stashHash) {
            return {
                success: false,
                updated: false,
                message: 'Could not create a temporary backup of local changes; no update was applied.',
                commit: ''
            };
        }

        const previousCommit = runGit(repoDir, ['rev-parse', 'HEAD']);
        let mergeOutput = '';
        try {
            mergeOutput = runGit(repoDir, ['merge', '--ff-only', `origin/${branch}`]);
        } catch (mergeError) {
            if (stashHash) {
                try {
                    applyStash(repoDir, stashHash);
                    dropStash(repoDir, stashHash);
                } catch (restoreError) {
                    return {
                        success: false,
                        updated: false,
                        message: `Update failed: ${mergeError.message}. Stash ${stashHash.slice(0, 10)} restoration failed: ${restoreError.message}`,
                        commit: ''
                    };
                }
            }
            return { success: false, updated: false, message: mergeError.message, commit: '' };
        }

        let stashRemoved = true;
        if (stashHash) {
            try {
                applyStash(repoDir, stashHash);
                stashRemoved = dropStash(repoDir, stashHash);
            } catch (restoreError) {
                const conflicts = getConflictedFiles(repoDir);
                const conflictPreview = conflicts.slice(0, 5).join(', ') || restoreError.message;
                try {
                    runGit(repoDir, ['reset', '--hard', previousCommit]);
                    applyStash(repoDir, stashHash);
                    dropStash(repoDir, stashHash);
                } catch (rollbackError) {
                    return {
                        success: false,
                        updated: false,
                        message: `Update conflicted (${conflictPreview}); rollback failed: ${rollbackError.message}`,
                        commit: ''
                    };
                }
                return {
                    success: false,
                    updated: false,
                    message: `Update rolled back due to conflicts with local files: ${conflictPreview}.`,
                    commit: ''
                };
            }
        }

        const currentCommit = runGit(repoDir, ['rev-parse', 'HEAD']);
        const commit = runGit(repoDir, ['log', '-1', '--format=%h - %s']);
        const updated = currentCommit !== previousCommit;

        if (updated) {
            try {
                const changedFiles = runGit(repoDir, ['diff', '--name-only', previousCommit, currentCommit]).split(/\r?\n/);
                if (changedFiles.includes('package.json') || changedFiles.includes('package-lock.json')) {
                    const npmCmd = process.platform === 'win32' ? 'npm.cmd' : 'npm';
                    execFileSync(npmCmd, ['install', '--omit=dev'], {
                        cwd: repoDir,
                        stdio: 'inherit',
                        timeout: 120_000
                    });
                }
            } catch (npmError) {
                console.warn(`\x1b[93m◈ [Git Watcher] npm install warning: ${npmError.message}\x1b[0m`);
            }
        }

        let message = mergeOutput || 'Updated to the latest commit.';
        if (stashHash) {
            message += ' Local changes were restored after the update.';
            if (!stashRemoved) {
                message += ` Safety backup remains in Git stash ${stashHash.slice(0, 10)}.`;
            }
        }

        return { success: true, updated, message, commit };
    } catch (error) {
        return { success: false, updated: false, message: error.message || String(error), commit: '' };
    } finally {
        isUpdating = false;
    }
}

function restartBot(client = null, reason = 'git-update') {
    process.env.ZYUNA_RESTART_REASON = reason;
    try {
        if (client) {
            client.destroy();
        }
    } catch {
        // Ignore cleanup errors during restart
    }

    // Under PM2 or systemd (Restart=always), exiting cleanly triggers an automatic restart.
    if (process.env.pm_id !== undefined || process.env.INVOCATION_ID !== undefined) {
        process.exit(0);
        return;
    }

    const child = spawn(process.execPath, process.argv.slice(1), {
        cwd: process.cwd(),
        stdio: 'inherit',
        detached: true,
        env: process.env
    });
    child.unref();
    process.exit(0);
}

function runStartupAutoPull() {
    if ((process.env.AUTO_GIT_WATCHER || 'true').trim().toLowerCase() !== 'true') {
        return;
    }

    const result = syncRepository();
    if (!result.success) {
        console.log(`\x1b[93m◈ Auto-Update skipped: ${result.message}\x1b[0m`);
    } else if (result.updated) {
        console.log(`\x1b[92m◈ Auto-Update: ${result.message} (${result.commit})\x1b[0m`);
        console.log('\x1b[93m◈ Restarting to load the updated code...\x1b[0m');
        restartBot(null, 'git-startup-update');
    } else {
        console.log(`\x1b[96m◈ Auto-Update: ${result.message}\x1b[0m`);
    }
}

function startGitWatchdog(client, options = {}) {
    if ((process.env.AUTO_GIT_WATCHER || 'true').trim().toLowerCase() !== 'true') {
        console.log('\x1b[90m◈ [Git Watcher] Disabled via AUTO_GIT_WATCHER.\x1b[0m');
        return;
    }

    stopGitWatchdog();

    const intervalMs = Number(process.env.GIT_WATCHER_INTERVAL_MS) || options.intervalMs || DEFAULT_INTERVAL_MS;
    const initialDelayMs = Number(process.env.GIT_WATCHER_INITIAL_DELAY_MS) || options.initialDelayMs || DEFAULT_INITIAL_DELAY_MS;

    const runCheck = () => {
        try {
            const result = syncRepository();
            if (result.success && result.updated) {
                console.log(`\x1b[96m◈ [Git Watcher] Pulled GitHub update: ${result.commit}\x1b[0m`);
                console.log('\x1b[92m✓ [Git Watcher] Code updated! Restarting bot to apply changes...\x1b[0m');
                restartBot(client, 'git-update');
            } else if (!result.success) {
                console.log(`\x1b[93m◈ [Git Watcher] Update skipped: ${result.message}\x1b[0m`);
            }
        } catch (error) {
            console.error(`\x1b[91m✗ [Git Watcher] Unexpected error: ${error.message}\x1b[0m`);
        }
    };

    initialDelayTimer = setTimeout(() => {
        runCheck();
        watchdogTimer = setInterval(runCheck, intervalMs);
        if (typeof watchdogTimer.unref === 'function') {
            watchdogTimer.unref();
        }
    }, initialDelayMs);

    if (typeof initialDelayTimer.unref === 'function') {
        initialDelayTimer.unref();
    }

    console.log(`\x1b[92m✓\x1b[0m Git Watchdog armed (every ${Math.round(intervalMs / 60000)}m)`);
}

function stopGitWatchdog() {
    if (initialDelayTimer) {
        clearTimeout(initialDelayTimer);
        initialDelayTimer = null;
    }
    if (watchdogTimer) {
        clearInterval(watchdogTimer);
        watchdogTimer = null;
    }
}

module.exports = {
    DEFAULT_BRANCH,
    findRepositoryRoot,
    syncRepository,
    restartBot,
    runStartupAutoPull,
    startGitWatchdog,
    stopGitWatchdog
};
