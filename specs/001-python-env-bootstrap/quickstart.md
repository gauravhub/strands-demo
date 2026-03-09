# Quickstart: Python Environment Bootstrap

**Feature**: `001-python-env-bootstrap`
**Validates**: FR-001 through FR-008, SC-001 through SC-004

---

## Prerequisites

- `uv` installed: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Python 3.11+ available (uv will manage this automatically if not present)
- AWS credentials configured (see Step 3)

---

## Step 1: Clone and Sync Dependencies

```bash
git clone <repo-url>
cd strands-demo
uv sync
```

Expected output: uv resolves and installs all dependencies into `.venv/`. No errors.

---

## Step 2: Verify Installation

```bash
uv run python -c "import strands; import streamlit; import boto3; print('OK')"
```

Expected output: `OK`

This verifies SC-001 and SC-002 — all packages importable, no missing dependencies.

---

## Step 3: Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

```dotenv
AWS_ACCESS_KEY_ID=<your-access-key>
AWS_SECRET_ACCESS_KEY=<your-secret-key>
AWS_REGION=us-east-1
COGNITO_USER_POOL_ID=us-east-1_XXXXXXXXX
COGNITO_APP_CLIENT_ID=<your-client-id>
```

The `.env` file is gitignored and never committed.

---

## Step 4: Verify Idempotency (SC-004)

Run `uv sync` a second time — it MUST complete without errors:

```bash
uv sync
```

Expected output: `All packages already installed` or similar no-op message.

---

## Step 5: Adding a New Dependency (US2 validation)

```bash
uv add requests
```

Verify `pyproject.toml` and `uv.lock` are both updated:

```bash
grep requests pyproject.toml
grep requests uv.lock
```

On another machine, `uv sync` will install the same version automatically (SC-003).

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `uv: command not found` | Install uv: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Wrong Python version | Run `uv python install 3.11` then `uv sync` |
| `ModuleNotFoundError` after sync | Run `uv sync --reinstall` |
| AWS credential errors | Verify `.env` values and that `python-dotenv` loads it at startup |
