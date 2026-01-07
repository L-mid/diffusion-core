# Decisions Log (mini-ADRs)

## Template
- Date:
- Decision:
- Context:
- Consequences:
- Links (PR/commit): 
    


05-01-2026
Turn this into the above format.
Links (PR/commit): will find later.
What we're doing with the lockfile (decision)
use uv's lockfile: uv.lock.
Local/dev installs run from the lock (not whatever’s newest today).
CI enforces:
lock is up-to-date: uv lock --check
installs do not modify the lock: uv sync --locked
This is exactly what uv documents --check for (lock freshness) and --locked for (error instead of updating the lock)


