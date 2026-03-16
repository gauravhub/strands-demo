# Data Model: AgentCore Memory Integration

**Date**: 2026-03-16 | **Feature**: 009-agentcore-memory

## Entities

### Memory Resource (CloudFormation-managed)

- **Type**: `AWS::BedrockAgentCore::Memory` — provisioned once per stack
- **Attributes**:
  - `Name`: `strands-demo-memory`
  - `Description`: Long-term memory for Strands Demo agent
  - `Strategies`: 4 built-in strategies (see below)
- **Lifecycle**: Created with stack, deleted with stack

### Memory Strategies (configured on Memory Resource)

| Strategy | Name | Namespace | What It Extracts |
|----------|------|-----------|-----------------|
| `summaryMemoryStrategy` | SessionSummarizer | `/summaries/{actorId}/{sessionId}/` | Session summaries |
| `userPreferenceMemoryStrategy` | PreferenceLearner | `/preferences/{actorId}/` | User preferences & choices |
| `semanticMemoryStrategy` | FactExtractor | `/facts/{actorId}/` | Facts & knowledge |
| `episodicMemoryStrategy` | EpisodeTracker | `/episodes/{actorId}/` | Structured episodes + reflections |

### Short-Term Memory Event (per conversation turn)

- **Type**: Ephemeral event stored in AgentCore Memory per session
- **Attributes**:
  - `session_id`: UUID — scopes events to a single conversation
  - `actor_id`: Cognito username — isolates per user
  - `message`: The conversation turn (user/assistant/tool)
  - `event_id`: Assigned by AgentCore Memory API
  - `timestamp`: When the event was created
- **Lifecycle**: Created per turn, retained for session duration, used as input for long-term extraction

### Long-Term Memory Record (extracted asynchronously)

- **Type**: Persistent record extracted by strategies from raw events
- **Attributes**:
  - `namespace`: Strategy-specific path (e.g., `/preferences/{actorId}/`)
  - `content`: Extracted insight (preference, fact, summary, or episode)
  - `relevance_score`: Semantic similarity score for retrieval
- **Lifecycle**: Created asynchronously by AgentCore Memory, persists across sessions

## CloudFormation Additions

### New Resource

- `AgentCoreMemory` (`AWS::BedrockAgentCore::Memory`) with all 4 strategies

### New Environment Variable (on AgentRuntime)

- `AGENTCORE_MEMORY_ID` — references the Memory resource ID

### New IAM Permissions (on AgentExecutionRole)

- AgentCore Memory API actions (create events, list events, retrieve memory records, etc.)

### New Output

- `AgentCoreMemoryId` — exported for reference
