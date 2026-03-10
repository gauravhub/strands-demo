# Quickstart: Strands Reasoning Chatbot

**Branch**: `003-strands-reasoning-chatbot`

## Prerequisites

- Python 3.11+
- `uv` installed
- Existing Cognito environment variables from feature 002 (see `.env.example`)
- An Anthropic API key (https://console.anthropic.com)
- A Tavily API key (https://app.tavily.com — free tier available)

## Setup

```bash
# 1. Clone and activate environment
cd strands-demo
uv sync

# 2. Create/update .env with new keys
cat >> .env << 'EOF'
ANTHROPIC_API_KEY=sk-ant-...
TAVILY_API_KEY=tvly-...
EOF

# 3. Run the app
streamlit run app.py
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Direct Anthropic API key for Claude Sonnet 4.6 |
| `TAVILY_API_KEY` | Yes | Tavily web search API key |
| `COGNITO_CLIENT_ID` | Yes | From feature 002 Cognito setup |
| `COGNITO_CLIENT_SECRET` | Yes | From feature 002 Cognito setup |
| `COGNITO_DOMAIN` | Yes | From feature 002 Cognito setup |
| `REDIRECT_URI` | Yes | From feature 002 Cognito setup |
| `LOG_LEVEL` | No | `INFO` (default) or `DEBUG` for verbose agent logging |

## What to Expect

1. Open `http://localhost:8501` in your browser
2. Log in with your Cognito credentials
3. You'll see the chatbot interface with three sections per response:
   - **Reasoning** — Claude's internal thinking (streaming)
   - **Tools Used** — Tavily web search calls (if triggered)
   - **Response** — The final answer (streaming)
4. Try asking: *"What happened in AI news today?"* to trigger a web search

## Running Tests

```bash
cd src
pytest ../tests/ -v
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `ANTHROPIC_API_KEY not set` error | Add key to `.env` and restart |
| `TAVILY_API_KEY not set` error | Add key to `.env` and restart |
| No reasoning section appearing | Model may not be emitting thinking tokens for simple queries; try a complex multi-step question |
| Login redirect fails | Verify Cognito env vars from feature 002 are still set |
