# Quickstart: Cognito Login (002)

**Branch**: `002-cognito-login`

---

## Prerequisites

- Python 3.11+, `uv` installed
- AWS CLI configured with credentials that have permissions to deploy CloudFormation stacks and manage Cognito

---

## 1. Deploy AWS Infrastructure (CloudFormation)

All Cognito resources (User Pool, App Client, Hosted UI domain) are provisioned via CloudFormation:

```bash
aws cloudformation deploy \
  --template-file infra/cognito.yaml \
  --stack-name strands-demo-cognito \
  --capabilities CAPABILITY_IAM \
  --region us-east-1
```

After deploy, fetch the stack outputs:

```bash
aws cloudformation describe-stacks \
  --stack-name strands-demo-cognito \
  --query "Stacks[0].Outputs" \
  --output table
```

---

## 2. Configure Environment

Copy the example env file and populate it from CloudFormation outputs:

```bash
cp .env.example .env
```

Edit `.env` using the stack output values:

```ini
AWS_REGION=us-east-1
COGNITO_USER_POOL_ID=<UserPoolId output>
COGNITO_CLIENT_ID=<UserPoolClientId output>
COGNITO_CLIENT_SECRET=<UserPoolClientSecret output>
COGNITO_DOMAIN=https://<UserPoolDomain output>.auth.us-east-1.amazoncognito.com
COGNITO_REDIRECT_URI=http://localhost:8501
```

---

## 3. Install Dependencies

```bash
uv sync
```

---

## 4. Provision Test Users (one-time, post-deploy)

```bash
uv run python scripts/provision_users.py
```

This creates two users (`demo_user_1` and `demo_user_2`) in the Cognito User Pool with permanent simple passwords. Credentials are printed to the console. Safe to re-run (idempotent).

---

## 5. Run the Application

```bash
uv run streamlit run app.py
```

Open `http://localhost:8501` in your browser. Click **Login** to authenticate via Cognito Hosted UI.

---

## 6. Verify Login Works

1. Click **Login** → you are redirected to the Cognito Hosted UI.
2. Enter credentials for `demo_user_1` or `demo_user_2`.
3. You are redirected back to the app and see your username displayed.
4. Click **Logout** → you are returned to the login screen.

---

## Troubleshooting

| Problem | Likely Cause | Fix |
|---|---|---|
| CloudFormation deploy fails | IAM permissions | Ensure AWS CLI credentials have `cognito-idp:*` and `cloudformation:*` permissions |
| `redirect_uri_mismatch` error on Cognito | Callback URL not registered in CFN template | Check `CallbackURLs` in `infra/cognito.yaml` and redeploy stack |
| `Missing environment variable` on startup | `.env` not populated | Check all 6 env vars are set in `.env` |
| User login fails with "User does not exist" | Provisioning script not run | Run `uv run python scripts/provision_users.py` |
| `FORCE_CHANGE_PASSWORD` error | User created without `Permanent=True` | Re-run provisioning script (it will call `admin_set_user_password` again) |
| Page shows login after hard refresh | Expected — session is in-memory only | Log in again; this is by design for this demo |
