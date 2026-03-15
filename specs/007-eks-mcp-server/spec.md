# Feature Specification: EKS MCP Server Integration

**Feature Branch**: `007-eks-mcp-server`
**Created**: 2026-03-14
**Status**: Draft
**Input**: User description: "Integrate EKS MCP Server into my Strands Agent. I should be able to invoke my Agent and ask questions about EKS clusters in my AWS Account. Ensure all of the changes are done using CloudFormation including any permissions changes to the IAM Role for the AgentCore Runtime that may have to be done to allow it to interact with EKS clusters through this MCP Server."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Query EKS Clusters via Chat (Priority: P1)

A user logs into the Streamlit chatbot and asks questions about their EKS clusters in their AWS account. The agent connects to the AWS-managed EKS MCP Server and uses its tools to retrieve cluster information, returning answers in natural language.

**Why this priority**: This is the core value proposition -- enabling users to interact with their EKS infrastructure through natural language without needing kubectl or the AWS console.

**Independent Test**: Can be fully tested by asking the agent "List my EKS clusters" or "Describe cluster X" and verifying it returns accurate cluster information from the user's AWS account.

**Acceptance Scenarios**:

1. **Given** a user is authenticated and has EKS clusters in their account, **When** they ask "What EKS clusters do I have?", **Then** the agent lists all EKS clusters with their names and status.
2. **Given** a user is authenticated and has an EKS cluster named "my-cluster", **When** they ask "Describe my-cluster", **Then** the agent returns cluster details (version, status, endpoint, node groups).
3. **Given** a user is authenticated but has no EKS clusters, **When** they ask about clusters, **Then** the agent responds that no clusters were found in the account.
4. **Given** a user is authenticated, **When** they ask "What Kubernetes version is my-cluster running?", **Then** the agent returns the specific Kubernetes version.

---

### User Story 2 - Troubleshoot EKS Clusters via Chat (Priority: P2)

A user asks the agent to help troubleshoot issues with their EKS clusters -- checking pod logs, Kubernetes events, CloudWatch metrics, and cluster insights.

**Why this priority**: Troubleshooting is a high-value use case that builds on cluster querying and provides significant operational value.

**Independent Test**: Can be tested by asking the agent to retrieve pod logs or Kubernetes events from a running cluster.

**Acceptance Scenarios**:

1. **Given** a user has a cluster with running pods, **When** they ask "Show me recent events in my-cluster", **Then** the agent retrieves and displays Kubernetes events.
2. **Given** a user has a cluster with running pods, **When** they ask "Get logs for pod X in namespace Y", **Then** the agent retrieves and displays the pod logs.
3. **Given** a user has a cluster, **When** they ask "Are there any insights or recommendations for my-cluster?", **Then** the agent returns EKS insights and optimization recommendations.

---

### User Story 3 - Infrastructure Permissions via CloudFormation (Priority: P1)

All IAM permissions required for the AgentCore Runtime to access the EKS MCP Server are managed through the existing CloudFormation template. No manual IAM changes are needed.

**Why this priority**: Security and reproducibility are critical -- all infrastructure changes must be declarative and auditable via CloudFormation, following the project's Security by Design principle.

**Independent Test**: Can be tested by deploying the updated CloudFormation stack and verifying the agent can successfully connect to the EKS MCP Server.

**Acceptance Scenarios**:

1. **Given** the updated CloudFormation template, **When** the stack is deployed, **Then** the AgentCore Runtime's IAM role includes permissions to invoke the EKS MCP Server.
2. **Given** the stack is deployed, **When** the agent attempts to list EKS clusters, **Then** the request succeeds without permission errors.
3. **Given** the stack is deployed, **When** the permissions are reviewed, **Then** only read-only EKS MCP permissions are granted (least-privilege).

---

### Edge Cases

- What happens when the EKS MCP Server endpoint is unreachable or the service is unavailable?
- How does the agent handle AWS credential/permission errors when connecting to the MCP server?
- What happens when the user asks about a cluster that doesn't exist?
- How does the agent behave when EKS MCP Server tools return rate-limited or throttled responses?
- What happens when the agent is running locally (non-AgentCore mode) -- can it still connect to the EKS MCP Server using local AWS credentials?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST connect to the AWS-managed EKS MCP Server using SigV4-authenticated requests via the mcp-proxy-for-aws library.
- **FR-002**: System MUST support all read-only EKS MCP Server tools (list clusters, describe resources, get pod logs, get events, get insights, search documentation, get metrics).
- **FR-003**: System MUST integrate EKS MCP tools into the existing Strands agent so they are available alongside existing tools (e.g., Tavily web search).
- **FR-004**: System MUST update the CloudFormation template to grant the AgentCore Runtime IAM role permissions to invoke the EKS MCP Server (eks-mcp:InvokeMcp, eks-mcp:CallReadOnlyTool).
- **FR-005**: System MUST update the CloudFormation template to grant the AgentCore Runtime IAM role permissions to perform underlying EKS read operations (eks:DescribeCluster, eks:ListClusters, etc.).
- **FR-006**: System MUST work in both local mode (using local AWS credentials) and AgentCore mode (using the Runtime's IAM role).
- **FR-007**: System MUST auto-detect the EKS MCP Server region from the AgentCore deployment region, falling back to AWS_DEFAULT_REGION. An explicit EKS_MCP_REGION environment variable MAY override the auto-detected value.
- **FR-008**: System MUST gracefully handle EKS MCP Server connection failures with user-friendly error messages.
- **FR-009**: System MUST restrict access to read-only tools only -- no write/privileged EKS MCP tools.
- **FR-010**: System MUST include EKS MCP tool invocations in the existing OTEL observability pipeline so they appear in traces alongside other agent activity.

### Key Entities

- **EKS MCP Client**: A connection to the AWS-managed EKS MCP Server that provides EKS-related tools to the agent.
- **MCP Tool**: An individual capability exposed by the EKS MCP Server (e.g., list_eks_resources, describe_eks_resource, get_pod_logs).
- **AgentCore Execution Role**: The IAM role assumed by the AgentCore Runtime, which must be extended with EKS MCP permissions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can ask natural language questions about their EKS clusters and receive accurate answers within 10 seconds.
- **SC-002**: All EKS MCP read-only tools (16 tools) are available to the agent.
- **SC-003**: The CloudFormation stack deploys successfully with the updated IAM permissions on the first attempt.
- **SC-004**: The agent handles EKS MCP Server connection failures gracefully -- users see a clear error message, not a stack trace.
- **SC-005**: No manual IAM changes are required -- all permissions are managed through CloudFormation.

## Clarifications

### Session 2026-03-14

- Q: What should the default EKS MCP Server region be when no explicit region is configured? → A: Auto-detect from AgentCore deployment region, fall back to AWS_DEFAULT_REGION.
- Q: Should EKS MCP tool invocations be included in the existing OTEL observability pipeline (feature 006)? → A: Yes, leverage existing OTEL instrumentation so MCP calls appear in traces automatically.

## Assumptions

- The AWS-managed EKS MCP Server (preview) is available in the user's AWS region.
- The user's AWS account has EKS clusters for testing (or the agent gracefully handles empty results).
- Read-only access is sufficient for the initial integration -- write tools can be added in a future feature.
- The EKS MCP Server endpoint follows the pattern `https://eks-mcp.{region}.api.aws/mcp`.
- The mcp-proxy-for-aws library handles SigV4 signing transparently.
- Local mode uses the default AWS credential chain (environment variables, ~/.aws/credentials, instance profile).
