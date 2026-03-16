# strands-demo Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-09

## Active Technologies
- Python 3.11+ + `streamlit>=1.35.0`, `boto3>=1.34.0`, `python-dotenv>=1.0.0`, `authlib>=1.3.2` (new) (002-cognito-login)
- None — session tokens held in `st.session_state` (in-memory, per tab) (002-cognito-login)
- Python 3.11+ + `strands-agents>=0.1.0` (includes `AnthropicModel`), `strands-agents-tools>=0.1.0` (includes `tavily`), `streamlit>=1.35.0`, `python-dotenv>=1.0.0` (003-strands-reasoning-chatbot)
- None — all state held in `st.session_state` (in-memory, per tab) (003-strands-reasoning-chatbot)
- None — all session state in `st.session_state` (ephemeral, per browser tab) (004-agentcore-deploy)
- Python 3.11 (match `.python-version`; set in SCC Advanced Settings) + streamlit, strands-agents, boto3, authlib, python-dotenv, anthropic, bedrock-agentcore, requests (all from `pyproject.toml`) (005-streamlit-cloud-deploy)
- N/A — stateless frontend, all state in `st.session_state` (005-streamlit-cloud-deploy)
- Python 3.11+ + `strands-agents[otel]>=0.1.0`, `aws-opentelemetry-distro>=0.10.1`, `boto3>=1.34.0`, AWS CLI v2 (006-agentcore-observability)
- CloudWatch Logs (log groups for traces, application logs, usage logs) (006-agentcore-observability)
- Python 3.11+ + strands-agents>=0.1.0, mcp-proxy-for-aws (new), strands-agents-tools>=0.1.0 (007-eks-mcp-server)
- N/A — stateless, no persistent data (007-eks-mcp-server)
- Python 3.11+ + strands-agents>=0.1.0, strands-agents-tools>=0.1.0, mcp-proxy-for-aws>=1.0.0, bedrock-agentcore>=0.1.0, anthropic>=0.40.0, boto3 (008-aws-api-mcp-server)
- Python 3.11+ + strands-agents>=0.1.0, bedrock-agentcore>=0.1.0 (already in requirements-agent.txt), boto3 (009-agentcore-memory)
- AgentCore Memory (managed service) — short-term events + long-term extracted records (009-agentcore-memory)

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
- 009-agentcore-memory: Added Python 3.11+ + strands-agents>=0.1.0, bedrock-agentcore>=0.1.0 (already in requirements-agent.txt), boto3
- 008-aws-api-mcp-server: Added Python 3.11+ + strands-agents>=0.1.0, strands-agents-tools>=0.1.0, mcp-proxy-for-aws>=1.0.0, bedrock-agentcore>=0.1.0, anthropic>=0.40.0, boto3
- 007-eks-mcp-server: Added Python 3.11+ + strands-agents>=0.1.0, mcp-proxy-for-aws (new), strands-agents-tools>=0.1.0


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
