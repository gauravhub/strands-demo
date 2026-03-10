"""Cognito configuration — loaded from environment variables at app startup."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class CognitoConfig:
    region: str
    user_pool_id: str
    client_id: str
    client_secret: str
    domain: str          # e.g. https://my-app.auth.us-east-1.amazoncognito.com
    redirect_uri: str    # e.g. http://localhost:8501

    @property
    def token_endpoint(self) -> str:
        return f"{self.domain}/oauth2/token"

    @property
    def authorize_endpoint(self) -> str:
        return f"{self.domain}/oauth2/authorize"

    @property
    def logout_endpoint(self) -> str:
        return f"{self.domain}/logout"


def load_config() -> CognitoConfig:
    """Load and validate Cognito configuration from environment variables.

    Raises:
        EnvironmentError: If one or more required variables are missing.
    """
    required = {
        "AWS_REGION": "COGNITO_USER_POOL_ID",
        "COGNITO_USER_POOL_ID": None,
        "COGNITO_CLIENT_ID": None,
        "COGNITO_CLIENT_SECRET": None,
        "COGNITO_DOMAIN": None,
        "COGNITO_REDIRECT_URI": None,
    }
    # Build list of exactly the 6 required var names
    var_names = [
        "AWS_REGION",
        "COGNITO_USER_POOL_ID",
        "COGNITO_CLIENT_ID",
        "COGNITO_CLIENT_SECRET",
        "COGNITO_DOMAIN",
        "COGNITO_REDIRECT_URI",
    ]

    missing = [name for name in var_names if not os.environ.get(name)]
    if missing:
        raise EnvironmentError(
            f"Missing required environment variable(s): {', '.join(missing)}.\n"
            "Copy .env.example to .env and populate from CloudFormation stack outputs."
        )

    return CognitoConfig(
        region=os.environ["AWS_REGION"],
        user_pool_id=os.environ["COGNITO_USER_POOL_ID"],
        client_id=os.environ["COGNITO_CLIENT_ID"],
        client_secret=os.environ["COGNITO_CLIENT_SECRET"],
        domain=os.environ["COGNITO_DOMAIN"].rstrip("/"),
        redirect_uri=os.environ["COGNITO_REDIRECT_URI"],
    )
