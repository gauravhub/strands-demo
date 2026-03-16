# Research: AgentCore Gateway Integration

**Date**: 2026-03-16 | **Feature**: 010-agentcore-gateway

## R1: Gateway Authentication

- **Decision**: Use CustomJWTAuthorizer with the same Cognito User Pool as the Runtime
- **Rationale**: Single sign-on — user logs in once, same token works for both Runtime and Gateway
- **Alternatives**: Separate auth, IAM SigV4 — both add complexity

## R2: Tavily Gateway Target

- **Decision**: Use Tavily built-in integration template (no Lambda needed). The Gateway routes requests directly to `https://api.tavily.com` with outbound API key auth. Provides TavilySearchPost (/search) and TavilySearchExtract (/extract) tools.
- **Rationale**: Built-in templates are simpler than custom Lambda targets — no code to maintain. Tavily is natively supported.
- **Limitation**: Built-in templates can only be added via AWS Console, not CloudFormation. This is a manual post-deployment step.
- **Alternatives considered**: Lambda target (more complex, requires custom code), OpenAPI target (Tavily lacks suitable public spec)

## R3: Access Token Propagation in AgentCore Mode

- **Decision**: Configure `Authorization` header in the Runtime's request header allowlist so the JWT is available in `context.request_headers`. Decode to get the token, pass to Gateway MCPClient.
- **Rationale**: The JWT is already validated by the Runtime. We just need to forward it to the Gateway.
- **Alternatives**: Pass token in payload (simpler but less secure), use workload identity token (more complex)

## R4: Gateway URL Attribute

- **Decision**: Use `!GetAtt AgentCoreGateway.GatewayUrl` for the endpoint URL in CloudFormation
- **Rationale**: AWS CFN docs confirm GatewayUrl is a return attribute of the Gateway resource

## R5: Observability

- **Decision**: Configure via CloudWatch Logs APIs post-deployment (same pattern as Memory resource)
- **Rationale**: Vended log delivery is not configurable via CFN properties
