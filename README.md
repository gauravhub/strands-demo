# Strands Demo

An AWS Strands Agents demo application with a Streamlit frontend and AWS Cognito authentication.

## Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) installed:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- Python 3.11+ (uv will manage this automatically)
- AWS account with Cognito User Pool configured

## Setup

```bash
# 1. Clone the repository
git clone <repo-url>
cd strands-demo

# 2. Install all dependencies
uv sync

# 3. Configure environment variables
cp .env.example .env
# Edit .env and fill in your AWS credentials and Cognito config
```

## Verify Installation

```bash
uv run python -c "import strands; import streamlit; import boto3; print('OK')"
```

Expected output: `OK`

## Run the App

```bash
uv run streamlit run app.py
```

## Managing Dependencies

Add a new runtime dependency:
```bash
uv add <package-name>
```

Add a development-only dependency:
```bash
uv add --dev <package-name>
```

After adding dependencies, commit both `pyproject.toml` and `uv.lock`:
```bash
git add pyproject.toml uv.lock
git commit -m "chore: add <package-name> dependency"
```

## Project Structure

```text
strands-demo/
├── app.py              # Streamlit application entry point
├── pyproject.toml      # Project metadata and dependencies
├── uv.lock             # Pinned dependency versions (committed)
├── .python-version     # Python version pin (committed)
├── .env.example        # Environment variable template (committed)
├── .env                # Your local secrets (gitignored — never commit)
└── specs/              # Feature specifications and implementation plans
```
