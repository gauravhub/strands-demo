# Quickstart: AgentCore Browser Integration

**Date**: 2026-03-17 | **Branch**: `013-agentcore-browser`

## Prerequisites

- Existing Streamlit app running with Strands agent
- AWS credentials configured for us-east-1
- `bedrock-agentcore` already installed (v0.1.7+)
- IAM permissions for `bedrock-agentcore:*Browser*` actions

## Steps

### 1. Install Additional Dependencies

```bash
pip install playwright nest-asyncio
```

Note: No `playwright install` needed — the browser runs in AgentCore's cloud, not locally.

### 2. Set Environment Variable

```bash
export RETAIL_STORE_URL="http://k8s-ui-ui-6353f3da9d-613966318.us-east-1.elb.amazonaws.com"
```

### 3. Run the App

```bash
streamlit run app.py
```

### 4. Test Browser Capability

In the chat interface, type:
```
Take a screenshot of the retail store
```

## Expected Result

- Agent starts a browser session
- Navigates to the retail store URL
- Takes a screenshot
- Displays the screenshot inline in the chat
- Describes what's visible on the page
- Stops the browser session

## SDK Reference

- **AgentCore Browser SDK**: https://github.com/aws/bedrock-agentcore-sdk-python
- **Strands Browser Tool**: `from strands_tools.browser import AgentCoreBrowser`
- **AgentCore Browser Quickstart**: https://aws.github.io/bedrock-agentcore-starter-toolkit/user-guide/builtin-tools/quickstart-browser.md
