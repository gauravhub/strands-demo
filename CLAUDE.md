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
- Python 3.11+ + strands-agents>=0.1.0, bedrock-agentcore>=0.1.0, mcp (for streamablehttp_client), tavily-python (Lambda) (010-agentcore-gateway)
- N/A — no application code; Kubernetes YAML manifests only + kubectl (with built-in Kustomize), GitHub API (for fetching upstream files) (011-eks-retail-store-deploy)
- N/A — manifests stored as files in repo; application data in-cluster (DynamoDB-local, MySQL, PostgreSQL, Redis) (011-eks-retail-store-deploy)
- N/A — no application code; AWS CLI commands + Kubernetes YAML manifests + AWS CLI v2, kubectl (with built-in Kustomize) (012-alb-ingress-ui)
- N/A — infrastructure resources only (012-alb-ingress-ui)
- Python 3.11+ + `strands-agents-tools>=0.1.0` (includes `AgentCoreBrowser`), `bedrock-agentcore>=0.1.0` (already installed), `playwright`, `nest-asyncio`, `streamlit>=1.35.0` (013-agentcore-browser)
- N/A — ephemeral browser sessions only (013-agentcore-browser)
- N/A — AWS CLI commands + Kubernetes YAML manifests + AWS CLI v2, kubectl (with Kustomize) (014-cloudfront-private-alb)
- Bash (shell script), JSON (evaluator config) — no Python code changes + `bedrock-agentcore-starter-toolkit` CLI (`agentcore` command, already installed) (015-agentcore-evaluations)
- CloudWatch Logs (evaluation results written to `/aws/bedrock-agentcore/evaluations/results/{config-id}`) (015-agentcore-evaluations)
- Python 3.11+ + `strands-agents` (AnthropicModel), `anthropic` SDK (already installed) (016-prompt-caching)

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
- 016-prompt-caching: Added Python 3.11+ + `strands-agents` (AnthropicModel), `anthropic` SDK (already installed)
- 015-agentcore-evaluations: Added Bash (shell script), JSON (evaluator config) — no Python code changes + `bedrock-agentcore-starter-toolkit` CLI (`agentcore` command, already installed)
- 014-cloudfront-private-alb: Added N/A — AWS CLI commands + Kubernetes YAML manifests + AWS CLI v2, kubectl (with Kustomize)


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
