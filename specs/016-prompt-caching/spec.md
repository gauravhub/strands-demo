# Feature Specification: Anthropic Prompt Caching

**Feature Branch**: `016-prompt-caching`
**Created**: 2026-03-18
**Status**: Draft
**Input**: User description: "Enable Anthropic prompt caching for the strands-demo agent to reduce latency and cost on repeated system prompt and tool definition tokens"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reduced Cost on Repeated Prompts (Priority: P1)

A developer deploys the strands-demo agent and notices that every API call sends the same large system prompt and tool definitions (thousands of tokens) to Anthropic. By enabling prompt caching, these repeated tokens are cached for 1 hour, significantly reducing per-request input token costs on subsequent turns within and across sessions.

**Why this priority**: Cost reduction is the primary business value. The system prompt and 50+ tool schemas are sent on every single turn, making them the largest source of redundant token usage. Caching eliminates re-processing these tokens on cache hits.

**Independent Test**: Can be tested by invoking the agent twice within a few minutes. The second invocation should show cache read tokens in the response metadata, confirming the cache was hit and tokens were not re-processed.

**Acceptance Scenarios**:

1. **Given** the agent is configured with prompt caching, **When** a user sends the first message in a session, **Then** the system creates a cache entry for the system prompt and tool definitions (cache_creation_input_tokens > 0).
2. **Given** a cache entry exists from a recent request, **When** a user sends a subsequent message within the cache TTL period, **Then** the system reads from cache instead of re-processing (cache_read_input_tokens > 0).
3. **Given** prompt caching is enabled, **When** the agent processes requests, **Then** the agent's behavior, response quality, and tool usage are identical to non-cached operation.

---

### User Story 2 - Cache Performance Observability (Priority: P2)

A developer wants to verify that prompt caching is working and monitor its effectiveness. They check the application logs and see cache performance metrics (creation tokens, read tokens) for each request, allowing them to confirm cache hits are occurring and estimate cost savings.

**Why this priority**: Without observability, developers cannot verify caching is working or diagnose issues. This complements the cost reduction story by providing transparency into cache behavior.

**Independent Test**: Can be tested by invoking the agent and checking application logs for cache metric entries. Logs should show cache_creation_input_tokens on first request and cache_read_input_tokens on subsequent requests.

**Acceptance Scenarios**:

1. **Given** prompt caching is enabled, **When** a request completes, **Then** cache performance metrics are logged with each response (cache creation tokens, cache read tokens).
2. **Given** a developer is reviewing logs, **When** they filter for cache-related entries, **Then** they can distinguish between cache misses (creation) and cache hits (reads).
3. **Given** caching is enabled but the cache entry has expired, **When** the next request is processed, **Then** the logs show a new cache creation event (not a read), confirming the TTL expired.

---

### Edge Cases

- What happens when the total cacheable content is below the minimum token threshold? The system should still function normally without caching — no errors or degraded behavior.
- What happens when the cache TTL expires mid-conversation? The next request creates a new cache entry transparently — no user-visible impact.
- What happens when the Anthropic API does not support caching for the selected model? The system should fall back to normal (uncached) operation without errors.
- What happens when extended thinking/reasoning is enabled alongside caching? Both features must coexist — caching applies to system prompt and tools, thinking applies to the model's reasoning process.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST mark the system prompt for caching with a 1-hour (3600 second) TTL so that repeated requests reuse cached tokens.
- **FR-002**: System MUST mark tool definitions for caching so that the tool schemas (50+ tools, thousands of tokens) are cached alongside the system prompt.
- **FR-003**: Prompt caching MUST be configured in the model configuration layer, not in the application entrypoint, to maintain separation of concerns.
- **FR-004**: Prompt caching MUST NOT alter the agent's behavior, response quality, or tool usage — it is a transparent optimization.
- **FR-005**: Prompt caching MUST coexist with extended thinking/reasoning tokens without conflicts.
- **FR-006**: System MUST log cache performance metrics (cache creation tokens, cache read tokens) with each response for observability.
- **FR-007**: System MUST NOT require any changes to the system prompt content or tool definitions — only metadata annotations for caching.
- **FR-008**: The cache TTL MUST be configurable (defaulting to 1 hour / 3600 seconds) to allow adjustment based on usage patterns.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Subsequent requests within the cache TTL period show cache read tokens greater than zero, confirming cache hits are occurring.
- **SC-002**: The agent's response quality and behavior are identical with and without caching enabled — no regressions in helpfulness, correctness, or tool usage.
- **SC-003**: Cache performance metrics appear in application logs for every request, enabling developers to calculate cache hit rates.
- **SC-004**: Cost per request decreases by at least 50% on cache hits (measured by comparing total input tokens billed on cached vs uncached requests of similar length).

## Clarifications

### Session 2026-03-18

- No critical ambiguities detected. Feature scope is small and well-defined (model configuration + logging). All requirements are clear.

## Assumptions

- The Anthropic API supports prompt caching for the model in use (claude-sonnet-4-6).
- The combined system prompt and tool definitions exceed the minimum token threshold (1024 tokens) required for caching.
- The agent framework (strands-agents AnthropicModel) supports passing cache_control metadata through to the Anthropic API.
- The ANTHROPIC_API_KEY is already configured as an environment variable.
- Extended thinking is already enabled and will continue to work alongside caching.
- Cache metrics (cache_creation_input_tokens, cache_read_input_tokens) are returned in the Anthropic API response usage field, including in streaming mode.
