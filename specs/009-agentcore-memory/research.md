# Research: AgentCore Memory Integration

**Date**: 2026-03-16 | **Feature**: 009-agentcore-memory

## R1: AgentCoreMemorySessionManager Integration Pattern

- **Decision**: Use `AgentCoreMemorySessionManager` from `bedrock_agentcore.memory.integrations.strands.session_manager` as the `session_manager` parameter on the Strands `Agent()` constructor
- **Rationale**: SDK-provided integration handles all hook registration automatically — `MessageAddedEvent` for persistence and retrieval, `AfterInvocationEvent` for flush. No custom hook code needed.
- **Alternatives considered**: Custom session manager extending `SessionManager` base class — rejected per Simplicity First principle

## R2: Actor ID Source

- **Decision**: Pass Cognito username in the invocation payload from Streamlit UI
- **Rationale**: Simplest approach — username already available in `st.session_state["user"]["username"]`. Alternative (decoding JWT in agent code) would require `PyJWT` dependency and `Authorization` header allowlist configuration.
- **Alternatives considered**: (1) Decode JWT token in `app.py` — more secure (tamper-proof) but adds complexity. (2) Use `sub` claim instead of `username` — more stable but less human-readable in logs.

## R3: CloudFormation Memory Resource

- **Decision**: Use `AWS::BedrockAgentCore::Memory` resource type with all 4 built-in strategies
- **Rationale**: CloudFormation manages the lifecycle. Memory ID is exported and injected as env var.
- **Alternatives considered**: Creating memory via SDK/CLI at deploy time — rejected because CloudFormation is the project standard for all infrastructure.

## R4: Session Manager Lifecycle in AgentCore Mode

- **Decision**: Use context manager (`with` block) for session manager in `app.py` to ensure flush
- **Rationale**: The `AgentCoreMemorySessionManager` supports context manager protocol (`__enter__`/`__exit__`). Using `with` ensures buffered messages are flushed even if an error occurs. Default `batch_size=1` means each message is sent immediately, but the `with` block is a safety net.
- **Alternatives considered**: Manual `close()` call in `finally` — works but `with` block is more Pythonic.

## R5: Graceful Degradation

- **Decision**: When `AGENTCORE_MEMORY_ID` is not set (empty string or missing), skip session manager creation entirely — agent works without memory as it does today
- **Rationale**: Allows the same code to run in environments where memory is not configured (e.g., Streamlit Cloud local mode without AgentCore Memory).
- **Alternatives considered**: Raise error when memory not configured — rejected because it would break existing deployments.
