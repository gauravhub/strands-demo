# Research: Deploy Streamlit App to Streamlit Community Cloud

**Date**: 2026-03-10

## R1: Secrets Management — st.secrets vs os.environ

**Decision**: Use Streamlit Community Cloud's native secrets management with root-level TOML keys. No code changes required.

**Rationale**: Root-level secrets in Streamlit Community Cloud are automatically exposed as environment variables. The existing app code uses `os.environ.get()` / `os.environ[]` exclusively. By defining secrets as root-level TOML keys (not nested under sections), they become available as env vars automatically. The existing `load_dotenv()` call in `app.py` is harmless in SCC — it's a no-op when `.env` doesn't exist.

**Alternatives considered**:
- Rewrite config modules to use `st.secrets` directly: rejected because it would break local dev workflow and couples code to SCC.
- Use `.streamlit/secrets.toml` locally: possible for local dev but `.env` + `python-dotenv` is already working and well-established in the project.

## R2: App Entry Point

**Decision**: Keep `app.py` at repository root and specify it as the entry point in SCC deployment settings.

**Rationale**: SCC defaults to `streamlit_app.py` but allows specifying any file path during deployment. The project already uses `app.py` at root — renaming would break existing workflows. SCC's deployment form has a "Main file path" field where we specify `app.py`.

**Alternatives considered**:
- Rename `app.py` to `streamlit_app.py`: rejected because it breaks local dev conventions and existing documentation.
- Create a `streamlit_app.py` wrapper that imports `app.py`: rejected as unnecessary indirection violating Simplicity First principle.

## R3: Dependency Manifest

**Decision**: Generate a `requirements.txt` at repository root from `pyproject.toml`.

**Rationale**: SCC supports `requirements.txt` natively (processed with `uv`, fallback to `pip`). The project uses `pyproject.toml` with `uv`, but SCC's `pyproject.toml` support currently requires `[tool.poetry]` section. Generating `requirements.txt` from `pyproject.toml` dependencies ensures compatibility. The file can be generated with `uv pip compile pyproject.toml -o requirements.txt` or manually listing the dependencies from `pyproject.toml`.

**Alternatives considered**:
- Use `pyproject.toml` directly: rejected because SCC's pyproject.toml support requires Poetry metadata not present in our project.
- Add `[tool.poetry]` section: rejected because it adds an unnecessary dependency manager reference.

## R4: Python Version

**Decision**: Use Python 3.11 in SCC Advanced Settings to match local dev (`.python-version` file says 3.11).

**Rationale**: SCC defaults to Python 3.12 but allows selecting 3.11 in the Advanced Settings during deployment. The project targets 3.11+ per `.python-version` and `pyproject.toml`. Matching versions prevents compatibility surprises.

**Alternatives considered**:
- Use SCC default (3.12): possible since `requires-python = ">=3.11"` allows it, but increases risk of untested behavior.

## R5: GitHub Repository Setup

**Decision**: Create a public GitHub repository and push the existing code.

**Rationale**: SCC requires a GitHub repository to pull source code. Clarification session resolved: public repository (no sensitive source in repo; secrets in SCC secrets manager). The project currently has no git remote.

**Alternatives considered**:
- Private repo with GitHub OAuth grant to SCC: rejected per clarification — adds unnecessary setup step for a demo project.

## R6: Cognito Redirect URI

**Decision**: Add the SCC public URL as an additional callback URI in the Cognito App Client. Keep `localhost:8501` registered for local dev.

**Rationale**: FR-008 requires redirect URI to be environment-configurable via `COGNITO_REDIRECT_URI`. The SCC deployment will set `COGNITO_REDIRECT_URI` to the `*.streamlit.app` URL. The Cognito App Client must list both URIs (localhost for dev, SCC URL for production). This is an AWS console/CLI change, not a code change.

**Alternatives considered**:
- Remove localhost URI: rejected because local development must continue working.
