# The Artifacts Polity:

## Summary:
No training artifacts (runs, checkpoints, datasets, archives) should ever enter git history.
Git contains only: source code, small text fixtures, and small documentation assets (images/graphs/samples are ok).
**Please do not** attempt to add anything else into the repository (see "referencing artifacts in PRs" below). 


## Forbidden in git (will be ingored):
### These directories
- `runs/`, `checkpoints/`, `ckpts/`
- `data/`, `datasets/` (etc, more added if convenient)

### These file types
- Model checkpoints/weights: `.pt`, `.pth`, `.ckpt`, `.safetensors`, `.onnx`
- Binary blobs: `.npz`, `.npy`, `.pkl`, `.pickle`, `.joblib`
- Archives: `.zip`, `.tar`, `.tgz`, `.gz`, `.7z`, `.rar`
- Large cache/log dirs: `wandb/`, `lightning_logs/`, `.cache/`, etc.
- Large files in general (anything over 20 mb == hard fail).

If you commit any of the above, CI will either ingore them (before commit), or will fail. 
Please do not attempt to modify/bypass this behaviour.


## How PRs **should** reference artifacts
Please use an external storage location (e.g: github lfs).
#### more on this later

PR description must include:
- A link to the Release or external storage location
- The exact filename(s)
- SHA256 checksum(s)


### Checksums
**Linux/macOS:**
`sha256sum path/to/file`

**Windows PowerShell:**
`Get-FileHash -Algorithm SHA256 path\to\file`

Example PR in snippet:

Artifacts (not in git):
- Release: <link>
- seed_2222_last.pt — SHA256: <hash>
- seed_3333_last.pt — SHA256: <hash>


## Allowed in git (small, reviewable)
- Source code, configs, docs
- Small doc assets (e.g., png/svg) under `docs/`
- Small text data for tests (tiny `.json`, `.txt`, `.csv`) only
- Never commit portable exports (tar/zips/etc) that are/contain archives, model weights, or heavy evaluation data.


## Enforcements
This repo enforces this in two ways:
1) Local pre-commit hook: blocks forbidden files/too large data in staged changes
2) CI: blocks forbidden files/too large data anywhere in the PR branch

If enforcement triggers, please move the artifact to Releases/external storage and link it. 
You should be good to link that to docs or reports within the repo using that method.


**If something large somehow goes through and you're aware**: please notify the owner at <midjourney4321@gmail.com>, or any name on this repo's `.github/CODEOWNERS` list immediatly. 