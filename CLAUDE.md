# strands-demo Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-09

## Active Technologies
- Python 3.11+ + `streamlit>=1.35.0`, `boto3>=1.34.0`, `python-dotenv>=1.0.0`, `authlib>=1.3.2` (new) (002-cognito-login)
- None — session tokens held in `st.session_state` (in-memory, per tab) (002-cognito-login)
- Python 3.11+ + `strands-agents>=0.1.0` (includes `AnthropicModel`), `strands-agents-tools>=0.1.0` (includes `tavily`), `streamlit>=1.35.0`, `python-dotenv>=1.0.0` (003-strands-reasoning-chatbot)
- None — all state held in `st.session_state` (in-memory, per tab) (003-strands-reasoning-chatbot)
- None — all session state in `st.session_state` (ephemeral, per browser tab) (004-agentcore-deploy)

- Python 3.11+ + `strands-agents`, `strands-agents-tools`, `streamlit`, `boto3`, (001-python-env-bootstrap)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.11+: Follow standard conventions

## Recent Changes
- 004-agentcore-deploy: Added Python 3.11+
- 003-strands-reasoning-chatbot: Added Python 3.11+ + `strands-agents>=0.1.0` (includes `AnthropicModel`), `strands-agents-tools>=0.1.0` (includes `tavily`), `streamlit>=1.35.0`, `python-dotenv>=1.0.0`
- 002-cognito-login: Added Python 3.11+ + `streamlit>=1.35.0`, `boto3>=1.34.0`, `python-dotenv>=1.0.0`, `authlib>=1.3.2` (new)


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
