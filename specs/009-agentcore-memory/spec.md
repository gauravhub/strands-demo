# Feature Specification: AgentCore Memory Integration

**Feature Branch**: `009-agentcore-memory`
**Created**: 2026-03-16
**Status**: Draft
**Input**: User description: "Integrate AgentCore Memory into Strands Demo agent for short-term and long-term memory"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Contextual Conversation Within a Session (Priority: P1)

A user logs into the Streamlit chatbot and has a multi-turn conversation. The agent remembers what was said earlier in the same session without the user repeating context. For example, the user says "I prefer us-west-2 for my deployments" and later asks "Which region should I deploy to?" — the agent recalls the preference from earlier in the conversation.

**Why this priority**: Short-term memory within a session is the foundational capability that makes the agent useful for multi-step tasks. Without it, each turn is isolated.

**Independent Test**: Can be fully tested by having a multi-turn conversation and verifying the agent references information from earlier turns.

**Acceptance Scenarios**:

1. **Given** a user is authenticated and starts a conversation, **When** they mention a preference ("I like us-west-2"), **Then** the agent acknowledges and remembers it.
2. **Given** the user previously stated a preference in the same session, **When** they ask a related question ("Which region should I use?"), **Then** the agent references the earlier preference without being reminded.
3. **Given** a user has an ongoing conversation with tool calls, **When** they ask a follow-up question about a previous tool result, **Then** the agent uses the prior context to answer.

---

### User Story 2 - Personalized Experience Across Sessions (Priority: P2)

A returning user starts a new conversation. The agent recalls their preferences, facts, and key insights from previous sessions, providing a personalized experience without the user having to re-state their context.

**Why this priority**: Cross-session memory is what differentiates a stateless chatbot from a truly intelligent assistant. It enables personalization and builds trust.

**Independent Test**: Can be tested by having a conversation where the user states preferences, starting a new session, and verifying the agent proactively uses those preferences.

**Acceptance Scenarios**:

1. **Given** a user stated "I prefer Python over JavaScript" in a previous session, **When** they start a new session and ask for code examples, **Then** the agent defaults to Python without being asked.
2. **Given** a user had multiple sessions, **When** they start a new session, **Then** the agent has access to summaries of prior sessions, extracted preferences, known facts, and episode reflections.
3. **Given** a user has no prior sessions (first-time user), **When** they start a conversation, **Then** the agent works normally without any memory context (graceful empty state).

---

### User Story 3 - Per-User Memory Isolation (Priority: P1)

Each authenticated user has their own isolated memory. User A's preferences and conversation history are never visible to User B. Memory is keyed by the user's Cognito identity.

**Why this priority**: Privacy and data isolation are non-negotiable in a multi-user system. Without per-user isolation, memory could leak sensitive information.

**Independent Test**: Can be tested by logging in as two different users, stating different preferences, and verifying each user only sees their own memory.

**Acceptance Scenarios**:

1. **Given** User A states "My favorite service is Lambda", **When** User B starts a conversation, **Then** User B's agent has no knowledge of User A's preference.
2. **Given** two users are using the system concurrently, **When** both have active sessions, **Then** their memory records are completely isolated.
3. **Given** a user logs out and logs back in, **When** they start a new session, **Then** their long-term memories from previous sessions are still accessible.

---

### User Story 4 - Infrastructure via CloudFormation (Priority: P1)

The memory resource and all associated permissions are provisioned through the existing CloudFormation template. No manual setup is required beyond deploying the stack.

**Why this priority**: Infrastructure as code ensures reproducibility and auditability, following the project's Security by Design principle.

**Independent Test**: Can be tested by deploying the updated CloudFormation stack and verifying the memory resource is created and the agent can access it.

**Acceptance Scenarios**:

1. **Given** the updated CloudFormation template, **When** the stack is deployed, **Then** a memory resource is created with all four long-term memory strategies enabled.
2. **Given** the stack is deployed, **When** the agent attempts to persist and retrieve memories, **Then** the requests succeed without permission errors.
3. **Given** the memory resource is created, **When** its configuration is inspected, **Then** it includes session summarization, preference learning, fact extraction, and episode tracking strategies.

---

### User Story 5 - Deployment and Runtime Update (Priority: P1)

The updated agent code is deployed to the AgentCore Runtime, and the Runtime is explicitly restarted to pick up the new container image. All existing configuration (including authentication) is preserved during the update.

**Why this priority**: Deployment must be reliable and non-breaking — losing authentication configuration would cause service outages.

**Independent Test**: Can be tested by deploying the update and confirming memory works in the deployed agent while authentication still functions.

**Acceptance Scenarios**:

1. **Given** the source code has been updated, **When** the deployment pipeline runs, **Then** the new container image is pulled and the agent starts successfully.
2. **Given** the Runtime has been updated, **When** a user has a multi-turn conversation, **Then** the agent remembers context from earlier turns (short-term memory works).
3. **Given** the Runtime update process, **When** the update is made, **Then** all existing configuration is preserved including authentication.

---

### Edge Cases

- What happens when the memory service is unavailable — does the agent still work without memory (graceful degradation)?
- How does the agent behave when long-term memory retrieval returns no results (new user, new topic)?
- What happens when the memory resource has not been created yet (AGENTCORE_MEMORY_ID not set)?
- How does the system handle concurrent sessions from the same user — are there race conditions in memory writes?
- What happens when the session manager fails to flush buffered messages — is data lost silently?
- How does the agent handle very long conversations that generate large amounts of short-term memory?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST persist every conversation turn (user messages, assistant responses, tool invocations) to short-term memory within the active session.
- **FR-002**: System MUST retrieve relevant long-term memories (preferences, facts, summaries, episodes) and make them available to the agent at the start of each turn.
- **FR-003**: System MUST isolate memory by user identity — each authenticated user's memories are keyed by their unique Cognito username as the actor identifier.
- **FR-004**: System MUST use the existing session identifier to scope short-term memory, ensuring conversation continuity within a session.
- **FR-005**: System MUST provision the memory resource via CloudFormation with all four long-term memory strategies: session summarization, preference learning, fact extraction, and episode tracking.
- **FR-006**: System MUST work without memory when the memory resource is not configured — the agent operates in a stateless mode as it does today (graceful degradation).
- **FR-007**: System MUST pass the authenticated user's identity from the Streamlit frontend to the AgentCore Runtime backend as part of the invocation payload.
- **FR-008**: System MUST ensure buffered messages are flushed before the session ends to prevent data loss.
- **FR-009**: The deployment process MUST include uploading source to the build pipeline, rebuilding the container image, updating the CloudFormation stack, and forcing the Runtime to pull the new image.
- **FR-010**: The Runtime update process MUST preserve all existing configuration including authentication when updating the agent.

### Key Entities

- **Memory Resource**: A managed memory store that holds both short-term events and long-term extracted memories for the agent.
- **Session**: A single conversation identified by a unique session ID, containing the sequence of turns between user and agent.
- **Actor**: The authenticated user, identified by their Cognito username, whose memories are isolated from other users.
- **Memory Strategy**: A configured algorithm that automatically extracts long-term insights (summaries, preferences, facts, episodes) from raw conversation turns.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can reference information from earlier in the same conversation and the agent responds correctly, demonstrating short-term memory retention.
- **SC-002**: Returning users experience personalized responses based on preferences and facts from prior sessions, without re-stating context.
- **SC-003**: Two different users' memories are completely isolated — no cross-user information leakage.
- **SC-004**: The CloudFormation stack deploys successfully with the memory resource and all four strategies on the first attempt.
- **SC-005**: The agent works correctly without memory when the memory resource is not configured — no errors, no degraded UI.
- **SC-006**: The deployed agent is verified end-to-end via the Streamlit app, confirming memory persists across turns within a session.
- **SC-007**: The Runtime update preserves all existing configuration — authenticated requests continue to work after deployment.

## Clarifications

### Session 2026-03-16

- No critical ambiguities detected. The integration pattern (AgentCoreMemorySessionManager), memory strategies (all 4 built-in), actor ID (Cognito username), session ID (existing UUID), and deployment process are all explicitly specified in the feature description.

## Assumptions

- The AgentCore Memory service is available in us-east-1 (the deployment region).
- The `bedrock-agentcore` Python SDK provides the `AgentCoreMemorySessionManager` and `AgentCoreMemoryConfig` classes in its `memory.integrations.strands` module.
- The `AWS::BedrockAgentCore::Memory` CloudFormation resource type is available and supports all four built-in strategies.
- The session manager automatically handles message persistence and long-term memory retrieval via Strands Agent hooks — no custom hook code is needed.
- Long-term memory extraction (summaries, preferences, facts, episodes) happens asynchronously in the background after messages are persisted — it is not immediate.
- The existing session UUID in `st.session_state` is suitable as the session identifier for memory scoping.
- The Cognito username is a stable, unique identifier suitable for use as the actor ID.
- The `bedrock-agentcore` package is already listed in `requirements-agent.txt`.
