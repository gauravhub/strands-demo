# Feature Specification: AWS API MCP Server Integration

**Feature Branch**: `008-aws-api-mcp-server`
**Created**: 2026-03-16
**Status**: Draft
**Input**: User description: "Integrate AWS API MCP Server into my Strands Agent alongside the existing EKS MCP Server"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Query AWS Resources via Chat (Priority: P1)

A user logs into the Streamlit chatbot and asks questions about AWS resources in their account. The agent connects to the AWS-managed AWS API MCP Server and uses its tools to retrieve resource information across AWS services, returning answers in natural language alongside any EKS-specific queries handled by the existing EKS MCP Server.

**Why this priority**: This is the core value proposition -- enabling users to interact with their broader AWS infrastructure through natural language, extending the agent beyond EKS-only queries.

**Independent Test**: Can be fully tested by asking the agent "What S3 buckets do I have?" or "Describe my Lambda functions" and verifying it returns accurate resource information from the user's AWS account.

**Acceptance Scenarios**:

1. **Given** a user is authenticated and has AWS resources in their account, **When** they ask "What S3 buckets do I have?", **Then** the agent uses AWS API MCP tools to list S3 buckets with their names and creation dates.
2. **Given** a user is authenticated, **When** they ask "Describe my Lambda functions", **Then** the agent returns function details using AWS API MCP tools.
3. **Given** a user is authenticated, **When** they ask about both EKS clusters and S3 buckets in the same conversation, **Then** the agent uses EKS MCP tools for cluster queries and AWS API MCP tools for S3 queries -- both tool sets work together.
4. **Given** a user is authenticated but the queried service has no resources, **When** they ask about those resources, **Then** the agent responds that no resources were found.

---

### User Story 2 - Combined Multi-Service Queries (Priority: P2)

A user asks the agent cross-service questions that may require both AWS API MCP tools and existing EKS MCP tools. The agent selects the appropriate tools for each part of the query.

**Why this priority**: Cross-service queries demonstrate the value of having multiple MCP servers integrated -- users get a unified interface to their entire AWS environment.

**Independent Test**: Can be tested by asking the agent a question that spans multiple AWS services and verifying it uses the correct tool set for each part.

**Acceptance Scenarios**:

1. **Given** a user has both EKS clusters and other AWS resources, **When** they ask "Give me an overview of my AWS infrastructure", **Then** the agent uses both AWS API MCP and EKS MCP tools to provide a comprehensive answer.
2. **Given** a user asks "What IAM roles are associated with my EKS clusters?", **When** the agent processes the query, **Then** it uses the appropriate combination of tools to answer.

---

### User Story 3 - Infrastructure Permissions via CloudFormation (Priority: P1)

All IAM permissions required for the AgentCore Runtime to access the AWS API MCP Server are managed through the existing CloudFormation template. No manual IAM changes are needed.

**Why this priority**: Security and reproducibility are critical -- all infrastructure changes must be declarative and auditable via CloudFormation, following the project's Security by Design principle.

**Independent Test**: Can be tested by deploying the updated CloudFormation stack and verifying the agent can successfully connect to the AWS API MCP Server.

**Acceptance Scenarios**:

1. **Given** the updated CloudFormation template, **When** the stack is deployed, **Then** the AgentCore Runtime's IAM role includes permissions to invoke the AWS API MCP Server.
2. **Given** the stack is deployed, **When** the agent attempts to query AWS resources via the AWS API MCP Server, **Then** the request succeeds without permission errors.
3. **Given** the stack is deployed, **When** the permissions are reviewed, **Then** only the necessary AWS API MCP permissions are granted (least-privilege).

---

### User Story 4 - Deployment and Runtime Update (Priority: P1)

The updated agent code is deployed to the AgentCore Runtime through the existing CI/CD pipeline (S3 upload, CodeBuild rebuild, CloudFormation update), and the Runtime is explicitly restarted to pick up the new container image. All existing Runtime configuration (including authentication) is preserved during the update.

**Why this priority**: Deployment must be reliable and non-breaking -- losing authentication configuration would cause service outages for all users.

**Independent Test**: Can be tested by deploying the update and confirming the agent responds to requests with AWS API MCP tools available alongside EKS MCP and Tavily tools, and that authentication still works.

**Acceptance Scenarios**:

1. **Given** the source code has been updated, **When** the deployment pipeline runs (S3 upload, CodeBuild rebuild, CloudFormation update, Runtime restart), **Then** the new container image is pulled and the agent starts successfully.
2. **Given** the Runtime has been updated, **When** a user invokes the agent, **Then** AWS API MCP tools appear in the response alongside EKS MCP and Tavily tools.
3. **Given** the Runtime update process, **When** the update-agent-runtime call is made, **Then** all existing configuration is preserved including the Cognito JWT authorizer configuration.
4. **Given** the Runtime has been updated, **When** an unauthenticated request is made, **Then** the Runtime correctly returns a 403 error (auth config was not lost).

---

### Edge Cases

- What happens when the AWS API MCP Server endpoint is unreachable or the service is unavailable?
- How does the agent handle AWS credential/permission errors when connecting to the AWS API MCP Server?
- What happens when both the EKS MCP Server and AWS API MCP Server are unavailable -- does the agent still work with Tavily?
- How does the agent behave when the AWS API MCP Server returns rate-limited or throttled responses?
- What happens when the update-agent-runtime call fails to preserve existing configuration?
- How does the agent behave when running in local mode -- can it still connect to the AWS API MCP Server using local AWS credentials?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST connect to the AWS-managed AWS API MCP Server using SigV4-authenticated requests via the mcp-proxy-for-aws library, with `aws_service` set to `"aws-api"`.
- **FR-002**: System MUST integrate AWS API MCP tools into the existing Strands agent so they are available alongside existing tools (Tavily web search and EKS MCP tools).
- **FR-003**: System MUST extend the mcp_tools.py module with a new function to load AWS API MCP tools, following the same pattern as the existing EKS MCP tool loader.
- **FR-004**: System MUST update the CloudFormation template to grant the AgentCore Runtime IAM role permissions to invoke the AWS API MCP Server.
- **FR-005**: System MUST work in both local mode (using local AWS credentials) and AgentCore mode (using the Runtime's IAM role).
- **FR-006**: System MUST auto-detect the AWS API MCP Server region, following the same region resolution pattern as the EKS MCP Server (explicit override env var, then deployment region, then default region).
- **FR-007**: System MUST gracefully handle AWS API MCP Server connection failures -- if unavailable, the agent continues with remaining tools (EKS MCP, Tavily).
- **FR-008**: System MUST include AWS API MCP tool invocations in the existing OTEL observability pipeline so they appear in traces alongside other agent activity.
- **FR-009**: The deployment process MUST include uploading the source zip to S3, triggering CodeBuild to rebuild the container image, updating the CloudFormation stack, and forcing the AgentCore Runtime to pull the new container image.
- **FR-010**: The Runtime update process MUST preserve all existing configuration including the Cognito JWT authorizer configuration when calling update-agent-runtime.

### Key Entities

- **AWS API MCP Client**: A connection to the AWS-managed AWS API MCP Server that provides tools to interact with AWS APIs across multiple services.
- **MCP Tool**: An individual capability exposed by the AWS API MCP Server for querying and interacting with AWS resources.
- **AgentCore Execution Role**: The IAM role assumed by the AgentCore Runtime, which must be extended with AWS API MCP permissions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can ask natural language questions about AWS resources (beyond EKS) and receive accurate answers within 15 seconds.
- **SC-002**: AWS API MCP tools are available to the agent alongside EKS MCP tools and Tavily -- all three tool sets appear in agent responses.
- **SC-003**: The CloudFormation stack deploys successfully with the updated IAM permissions on the first attempt.
- **SC-004**: The agent handles AWS API MCP Server connection failures gracefully -- if unavailable, the agent still works with remaining tools.
- **SC-005**: No manual IAM changes are required -- all permissions are managed through CloudFormation.
- **SC-006**: The deployed agent is verified end-to-end by invoking it via the Streamlit app and confirming all three tool sets (AWS API MCP, EKS MCP, Tavily) are available.
- **SC-007**: The Runtime update preserves all existing configuration -- authenticated requests continue to work after deployment.

## Clarifications

### Session 2026-03-16

- No critical ambiguities detected. The integration pattern, endpoint, SigV4 service name, deployment process, and failure handling are all explicitly specified. The feature mirrors the proven 007-eks-mcp-server pattern.

## Assumptions

- The AWS-managed AWS API MCP Server is available in the user's AWS region.
- The AWS API MCP Server endpoint follows the pattern `https://aws-api.{region}.api.aws/mcp`.
- The `aws_service` parameter for SigV4 signing is `"aws-api"`.
- The mcp-proxy-for-aws library handles SigV4 signing transparently (same as EKS MCP).
- The integration pattern (MCPClient factory lambda, list_tools_sync, tool merging) is identical to the EKS MCP Server integration.
- Local mode uses the default AWS credential chain (environment variables, ~/.aws/credentials, instance profile).
- The ContainerUri in the CloudFormation template uses a `latest` tag that doesn't change, so a separate update-agent-runtime call is required to force the container restart.
- The update-agent-runtime CLI call must explicitly include all existing Runtime configuration (including authorizerConfiguration) to avoid losing settings.
