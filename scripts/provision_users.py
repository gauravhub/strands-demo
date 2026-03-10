"""
Provision two demo users in the Cognito User Pool.

Run after deploying the CloudFormation stack:
    uv run python scripts/provision_users.py

Requires .env to be populated from CloudFormation stack outputs.
This script is idempotent — safe to re-run.
"""

import os
import sys

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

# ── Config ─────────────────────────────────────────────────────────────────────

REGION = os.environ.get("AWS_REGION", "us-east-1")
USER_POOL_ID = os.environ.get("COGNITO_USER_POOL_ID")

DEMO_USERS = [
    {"username": "demo_user_1", "password": "DemoPass1!", "email": "demo1@example.com"},
    {"username": "demo_user_2", "password": "DemoPass2!", "email": "demo2@example.com"},
]

# ── Validation ─────────────────────────────────────────────────────────────────

if not USER_POOL_ID:
    print("ERROR: COGNITO_USER_POOL_ID is not set in .env", file=sys.stderr)
    print("Run: aws cloudformation describe-stacks --stack-name strands-demo-cognito", file=sys.stderr)
    sys.exit(1)

# ── Provisioning ───────────────────────────────────────────────────────────────

client = boto3.client("cognito-idp", region_name=REGION)


def provision_user(username: str, password: str, email: str) -> None:
    """Create user and set a permanent password. Idempotent."""
    # Step 1: Create user (suppress welcome email)
    try:
        client.admin_create_user(
            UserPoolId=USER_POOL_ID,
            Username=username,
            TemporaryPassword=password,
            UserAttributes=[{"Name": "email", "Value": email}],
            MessageAction="SUPPRESS",
        )
        print(f"  Created user: {username}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "UsernameExistsException":
            print(f"  User already exists: {username} (skipping create)")
        else:
            raise

    # Step 2: Set permanent password — transitions user from FORCE_CHANGE_PASSWORD to CONFIRMED
    client.admin_set_user_password(
        UserPoolId=USER_POOL_ID,
        Username=username,
        Password=password,
        Permanent=True,
    )
    print(f"  Password set (permanent): {username}")


def main() -> None:
    print(f"Provisioning demo users in User Pool: {USER_POOL_ID}\n")
    for user in DEMO_USERS:
        print(f"→ {user['username']}")
        provision_user(user["username"], user["password"], user["email"])
        print(f"  ✓ Ready — username: {user['username']}  password: {user['password']}\n")
    print("Done. Both users are in CONFIRMED state and ready to log in.")


if __name__ == "__main__":
    main()
