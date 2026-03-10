# Agent container image for Amazon Bedrock AgentCore Runtime.
# Build context: repository root (.)
# Target architecture: linux/arm64 (required by AgentCore)
#
# Build with:
#   docker buildx build --platform linux/arm64 \
#     -f infra/agentcore/Dockerfile \
#     -t <ecr-uri>:latest .

FROM public.ecr.aws/docker/library/python:3.11-slim

WORKDIR /app

# Install container-only dependencies (includes aws-opentelemetry-distro for OTEL)
COPY infra/agentcore/requirements-agent.txt ./requirements-agent.txt
RUN pip install --no-cache-dir -r requirements-agent.txt

# Copy agent source package
COPY src/ ./src/

# Copy the AgentCore entrypoint as the container's main module
COPY src/agentcore/app.py ./app.py

# Ensure src/ is importable as a package
ENV PYTHONPATH=/app

# OTEL auto-instrumentation wraps the agent process.
# Emits X-Ray traces and CloudWatch metrics with zero code changes.
CMD ["opentelemetry-instrument", "python", "app.py"]
