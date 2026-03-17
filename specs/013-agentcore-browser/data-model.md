# Data Model: AgentCore Browser Integration

**Date**: 2026-03-17 | **Branch**: `013-agentcore-browser`

## Entities

### Browser Session (ephemeral)

| Attribute | Description |
|-----------|-------------|
| session_id | Unique identifier assigned by AgentCore when session starts |
| region | AWS region (us-east-1) |
| identifier | Browser resource identifier (default: `aws.browser.v1`) |
| status | ACTIVE / TERMINATED |
| lifecycle | Created on-demand per user request, destroyed after tool completes |

### Tool Result (in-memory)

| Attribute | Description |
|-----------|-------------|
| tool_use_id | Strands tool invocation ID |
| name | Tool name (e.g., `browser`) |
| input | Tool input parameters (URL, action) |
| result | Tool output — text content or base64 PNG screenshot |

## Configuration

| Variable | Source | Default |
|----------|--------|---------|
| `RETAIL_STORE_URL` | Environment variable | `http://k8s-ui-ui-6353f3da9d-613966318.us-east-1.elb.amazonaws.com` |
| `AWS_REGION` | Environment variable | `us-east-1` |

## Flow

```
User message → Agent reasons about tools
  │
  ├─ Non-browser request → existing tools (Tavily, EKS, AWS API)
  │
  └─ Browser request → AgentCoreBrowser.browser tool
       │
       ├─ Starts session (BrowserClient.start)
       ├─ Connects via Playwright CDP WebSocket
       ├─ Navigates to URL
       ├─ Takes screenshot / reads content
       ├─ Returns result (base64 PNG or text)
       └─ Stops session (BrowserClient.stop)
            │
            ▼
       Chat UI renders result
         ├─ Text → markdown (existing)
         └─ Image → st.image() (new)
```
