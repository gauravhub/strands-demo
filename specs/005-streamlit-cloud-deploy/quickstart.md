# Quickstart: Deploy to Streamlit Community Cloud

**Deployed URL**: https://agentcore-demo.streamlit.app/
**GitHub Repo**: https://github.com/gauravhub/strands-demo

## Prerequisites

- GitHub account
- Streamlit Community Cloud account (sign up at share.streamlit.io)
- All secrets from `.env.example` available
- Cognito App Client deployed (feature 002)
- AgentCore Runtime deployed (feature 004)

## Step 1: Generate requirements.txt

```bash
# From repo root — extract runtime dependencies from uv.lock
uv export --no-dev --no-hashes > requirements.txt
```

## Step 2: Push to GitHub

```bash
# Create public repo on GitHub (via gh CLI or web UI)
gh repo create strands-demo --public --source=. --remote=origin

# Push all branches
git push -u origin --all
```

## Step 3: Deploy on Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Select your GitHub repo: `gauravhub/strands-demo`
4. Set **Branch**: `main`
5. Set **Main file path**: `app.py`
6. Open **Advanced settings**:
   - Set Python version to **3.11**
7. Click "Deploy"

## Step 4: Configure Secrets

1. In SCC app dashboard, click **Settings** → **Secrets**
2. Paste TOML-format secrets (see `.streamlit/secrets.toml.example`):

```toml
COGNITO_USER_POOL_ID = "us-east-1_XXXXXXXXX"
COGNITO_CLIENT_ID = "your-client-id"
COGNITO_CLIENT_SECRET = "your-client-secret"
COGNITO_DOMAIN = "https://strands-demo-dhamijag.auth.us-east-1.amazoncognito.com"
COGNITO_REDIRECT_URI = "https://agentcore-demo.streamlit.app"
ANTHROPIC_API_KEY = "sk-ant-..."
TAVILY_API_KEY = "tvly-..."
AGENTCORE_RUNTIME_ARN = "arn:aws:bedrock-agentcore:us-east-1:ACCOUNT:runtime/ID"
AWS_REGION = "us-east-1"
LOG_LEVEL = "INFO"
```

3. Click **Save** — app will reboot with secrets loaded.

## Step 5: Update Cognito Redirect URIs

```bash
# First read existing settings
aws cognito-idp describe-user-pool-client \
  --user-pool-id YOUR_POOL_ID \
  --client-id YOUR_CLIENT_ID

# Then update with both localhost and SCC URLs
aws cognito-idp update-user-pool-client \
  --user-pool-id YOUR_POOL_ID \
  --client-id YOUR_CLIENT_ID \
  --callback-urls '["http://localhost:8501","https://agentcore-demo.streamlit.app"]' \
  --logout-urls '["http://localhost:8501","https://agentcore-demo.streamlit.app"]' \
  --allowed-o-auth-flows code \
  --allowed-o-auth-scopes openid email profile \
  --allowed-o-auth-flows-user-pool-client \
  --supported-identity-providers COGNITO
```

## Step 6: Smoke Test

1. Visit https://agentcore-demo.streamlit.app
2. Verify landing page renders with Login button
3. Click Login → redirects to Cognito hosted UI
4. Authenticate → redirects back to SCC URL
5. Send a chat message → receives AgentCore response
