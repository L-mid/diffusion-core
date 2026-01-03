<!-- docs/index.md -->
# diffusion-core

Docs build gate is live.


# Full repo layout:


# might not be accurate later, remeber to update.


diffusion-core/
├─ .github/
│  ├─ CODEOWNERS
│  ├─ pull_request_template.md
│  └─ workflows/
│     ├─ ci.yml                      # lint/type/test/docs-sync/artifact-blocker
│     ├─ docs.yml                    # docs build (warnings-as-errors)
│     └─ release.yml                 # optional: validate release gates on tag
│
├─ docs/        # will be nested differently.
│  ├─ index.md
│  ├─ quickstart.md
│  ├─ repo_layout.md
│  ├─ ssot.md
│  ├─ problems_log.md
│  ├─ decisions_log.md
│  ├─ docstring_contract.md
│  ├─ artifacts_policy.md
│  ├─ run_layout_contract.md
│  ├─ provenance_spec.md
│  ├─ determinism.md
│  ├─ checkpointing.md
│  ├─ export_run.md
│  ├─ smoke_test.md
│  ├─ debugging_workflow.md
│  ├─ add_a_metric.md                # “do these exact steps” doc
│  ├─ safe_experiment_tweaks.md       # “safe lanes” doc
│  ├─ releasing.md
│  ├─ release_notes/
│  │  ├─ v0.1.0.md
│  │  └─ v1.0.0.md
│  └─ assets/
│     └─ (exported runs live here; never raw runs/)
│
├─ tools/
│  ├─ export_run.py                  # copies portable bits → docs/assets/<run_id>/
│  ├─ block_artifacts.py             # fails if forbidden files are staged/PR’d
│  └─ docs_sync_check.py             # verifies docs match SSOT (schema/CLI/registry)
│
├─ configs/
│  ├─ schema_examples/
│  │  ├─ minimal_train.yaml
│  │  ├─ eval_only.yaml
│  │  └─ metrics_demo.yaml
│  └─ studies/
│     ├─ e01_baseline.yaml
│     └─ e02_minsnr_sweep.yaml
│
├─ src/
│  └─ minsnr_lab/
│     ├─ __init__.py                 # defines public surface (exported APIs only)
│     ├─ api/
│     │  ├─ __init__.py
│     │  ├─ train_api.py             # stable entrypoints (thin wrappers)
│     │  └─ eval_api.py
│     │
│     ├─ cli/
│     │  ├─ __init__.py
│     │  ├─ main.py                  # entrypoint + top-level error UX
│     │  ├─ train_cmd.py
│     │  ├─ eval_cmd.py
│     │  └─ utils.py
│     │
│     ├─ config/
│     │  ├─ __init__.py
│     │  ├─ schema.py                # strict schema (dataclass/pydantic)
│     │  ├─ load.py                  # strict load + unknown key rejection
│     │  └─ resolve.py               # merges defaults, writes resolved snapshot
│     │
│     ├─ runs/
│     │  ├─ __init__.py
│     │  ├─ layout.py                # run dir contract (meta/logs/ckpts/artifacts)
│     │  ├─ provenance.py            # stamps git/cli/env/hashes
│     │  └─ io.py                    # safe writers (atomic writes, jsonl helpers)
│     │
│     ├─ logging/
│     │  ├─ __init__.py
│     │  ├─ jsonl_logger.py          # structured logging + collision checks
│     │  └─ formats.py
│     │
│     ├─ callbacks/
│     │  ├─ __init__.py
│     │  ├─ base.py                  # Callback protocol + lifecycle hooks
│     │  ├─ registry.py              # callback registry, config-driven construction
│     │  └─ builtins/
│     │     ├─ __init__.py
│     │     ├─ timing.py
│     │     ├─ grad_norm.py
│     │     └─ sample_grid.py
│     │
│     ├─ metrics/
│     │  ├─ __init__.py              # optional: metric registry re-export
│     │  ├─ registry.py              # “add a metric” touches this + new file only
│     │  └─ builtin/
│     │     ├─ __init__.py
│     │     ├─ loss_scalar.py
│     │     ├─ fid.py                # if present; otherwise stubbed behind deps
│     │     └─ kid.py
│     │
│     ├─ data/
│     │  ├─ __init__.py
│     │  ├─ loaders.py
│     │  └─ transforms.py
│     │
│     ├─ models/
│     │  ├─ __init__.py
│     │  ├─ unet_cifar32.py
│     │  └─ wrappers/
│     │     ├─ __init__.py
│     │     └─ ema.py                # safe tweak lane: model wrappers
│     │
│     ├─ diffusion/
│     │  ├─ __init__.py
│     │  ├─ q_schedule.py
│     │  ├─ ddpm.py
│     │  ├─ ddim.py
│     │  └─ samplers/                # safe tweak lane: samplers
│     │     ├─ __init__.py
│     │     ├─ registry.py
│     │     ├─ ddpm_sampler.py
│     │     └─ ddim_sampler.py
│     │
│     ├─ losses/                     # safe tweak lane: loss variants
│     │  ├─ __init__.py
│     │  ├─ registry.py
│     │  ├─ base.py
│     │  ├─ constant.py
│     │  └─ minsnr.py
│     │
│     ├─ train/
│     │  ├─ __init__.py
│     │  ├─ loop.py                  # minimal core loop: step + callback dispatch
│     │  ├─ checkpointing.py
│     │  └─ determinism.py
│     │
│     ├─ eval/
│     │  ├─ __init__.py
│     │  ├─ runner.py                # eval command driver (uses callbacks/metrics)
│     │  └─ recon.py                 # optional: recon metrics path
│     │
│     └─ util/
│        ├─ __init__.py
│        ├─ hashing.py
│        ├─ exceptions.py
│        └─ typing.py
│
├─ tests/
│  ├─ unit/
│  │  ├─ test_config_strict_load.py
│  │  ├─ test_run_layout_contract.py
│  │  ├─ test_provenance_schema.py
│  │  ├─ test_metrics_registry.py
│  │  ├─ test_metric_collision.py
│  │  ├─ test_samplers_registry.py
│  │  └─ test_losses_registry.py
│  ├─ cli/
│  │  ├─ test_smoke_train_cpu.py
│  │  ├─ test_smoke_eval_cpu.py
│  │  └─ test_resume_continuity.py
│  └─ fixtures/
│     ├─ tiny_config.yaml
│     └─ expected_run_layout.json
│
├─ .pre-commit-config.yaml
├─ pyproject.toml
├─ README.md
├─ CHANGELOG.md
├─ LICENSE
└─ mkdocs.yml (or docs/conf.py if Sphinx)
