# Repository Guidelines

## Project Structure & Module Organization
- `mtga_gui.py` hosts the Tkinter UI, certificate workflow, and proxy threads; treat it as the orchestration layer.
- `modules/` provides import-safe helpers for certificates, hosts entries, resource lookup, and the Flask-based proxy server.
- Documentation sits in `docs/`; packaging assets in `mac/`, `helper-tool/`, and `icons/`. Diagnostic scripts (`test_*.py`, `debug_test.py`) remain in the repo root.

## Build, Test, and Development Commands
- `uv sync` installs runtime dependencies; append `--extra win-build` or `--extra mac-build` before invoking Nuitka packaging scripts.
- `uv run python mtga_gui.py --debug` starts the GUI with verbose logs; `./run_mtga_gui.sh` (macOS) and `run_mtga_gui.bat` (Windows) wrap dependency syncing and privilege elevation.
- `./build_mac_app.sh` yields a `.app` bundle in `dist-onefile/`, while `build_onefile.bat` and `build_standalone.bat` produce Windows distributables.

## Coding Style & Naming Conventions
- Target Python 3.13, four-space indentation, and PEP 8 naming (`snake_case` functions, `CamelCase` classes, uppercase constants).
- Keep module imports at the top and guard platform-specific logic as in `setup_environment()` to avoid startup regressions.
- Update YAML schema changes in the localized docs and preserve backward compatibility for existing `config_groups`.

## Testing Guidelines
- `uv run python test_target_api.py` validates remote API compatibility; replace placeholders locally and avoid committing secrets.
- GUI checks live in `test_clipboard.py` and `test_tkinter_gui.py`. Run them on the OS you modify and summarize anomalies in the pull request.
- Before publishing installers, launch the generated `.exe` or `.app` to confirm bundled resources, TLS materials, and host edits still apply.

## Commit & Pull Request Guidelines
- Follow the `type(scope): summary` style seen in history (`feat(mac):`, `ci(workflow):`, `docs:`). Keep each commit focused and omit generated binaries unless the release is intentional.
- Pull requests should explain the user impact, list manual or automated tests, link related issues, and include screenshots for GUI updates or installer flows.
- Flag security-sensitive modifications (certificate handling, proxy routing, entitlements) and describe mitigations so reviewers can reason about risk quickly.

## Security & Configuration Tips
- Do not commit CA keys, user certificates, or `~/.mtga/` artifacts; rely on helper scripts for per-machine setup.
- Example configurations belong in `docs/` with redacted tokens. Encourage contributors to map models through proxy settings instead of hard-coding IDs.
- When changing ports or sandbox entitlements, update the shell launchers and `mac/entitlements.plist` together to keep notarization aligned.
