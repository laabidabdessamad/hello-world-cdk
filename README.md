# hello-world-cdk

A minimal FastAPI "hello world" endpoint, deployed to AWS Lambda (with a public
Function URL — no API Gateway) via AWS CDK, automatically on every push to
`main` via GitHub Actions.

**Why this architecture:** Lambda's free tier covers 1M requests/month, and
you pay nothing while the endpoint is idle. A Lambda Function URL is a
built-in HTTPS endpoint on the function itself, so there's no API Gateway
cost or extra CDK resource to manage.

```
.
├── app/
│   ├── main.py          # FastAPI app + Mangum Lambda handler
│   └── requirements.txt # fastapi, mangum (installed into app/ before packaging)
├── cdk/
│   ├── app.py            # CDK entrypoint
│   ├── stack.py           # Lambda + Function URL
│   ├── cdk.json
│   └── requirements.txt  # aws-cdk-lib, constructs
└── .github/workflows/deploy.yml
```

---

## One-time AWS setup

You only need to do this once per AWS account. Everything after this is
automatic.

### 1. Create the GitHub OIDC identity provider (if you don't already have one)

Most accounts only ever need one of these, total, no matter how many repos
deploy from GitHub. Check first in the AWS Console under
**IAM → Identity providers**. If `token.actions.githubusercontent.com` isn't
listed, create it:

```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

### 2. Create the deploy role

Replace `YOUR_GITHUB_USERNAME/YOUR_REPO_NAME` and `ACCOUNT_ID` below.

**Trust policy** (`trust-policy.json`) — only allows this specific repo's
`main` branch to assume the role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:YOUR_GITHUB_USERNAME/YOUR_REPO_NAME:ref:refs/heads/main"
        }
      }
    }
  ]
}
```

```bash
aws iam create-role \
  --role-name github-actions-hello-world-deploy \
  --assume-role-policy-document file://trust-policy.json
```

**Permissions policy** — broad enough for CDK to manage this stack
(CloudFormation, Lambda, IAM role creation for the function, and the S3/SSM
resources CDK's bootstrap uses). It's scoped to actions rather than
`*:*`/AdministratorAccess, but feel free to tighten further once things work.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:*",
        "lambda:*",
        "iam:CreateRole",
        "iam:DeleteRole",
        "iam:GetRole",
        "iam:PassRole",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:PutRolePolicy",
        "iam:DeleteRolePolicy",
        "iam:GetRolePolicy",
        "iam:TagRole",
        "s3:*",
        "ssm:GetParameter",
        "ssm:GetParameters",
        "logs:*",
        "ecr:*"
      ],
      "Resource": "*"
    }
  ]
}
```

```bash
aws iam put-role-policy \
  --role-name github-actions-hello-world-deploy \
  --policy-name cdk-deploy-permissions \
  --policy-document file://permissions-policy.json
```

Note the role's ARN from the output (or `aws iam get-role --role-name
github-actions-hello-world-deploy`) — you'll need it in step 4.

### 3. Bootstrap CDK in your account/region (one-time per account+region)

```bash
npx aws-cdk@2 bootstrap aws://ACCOUNT_ID/eu-west-3
```

(Change the region if you edit `AWS_REGION` in the workflow file.)

### 4. Add the role ARN to GitHub

In your repo: **Settings → Secrets and variables → Actions → New repository
secret**

- Name: `AWS_DEPLOY_ROLE_ARN`
- Value: the role ARN from step 2, e.g.
  `arn:aws:iam::ACCOUNT_ID:role/github-actions-hello-world-deploy`

---

## Deploying

Push to `main`:

```bash
git add .
git commit -m "Deploy hello world API"
git push origin main
```

Open the **Actions** tab in GitHub to watch the workflow run. When it
finishes, check the job's last step ("Print the Function URL") for your
live endpoint, or find it in the CloudFormation console under the
`HelloWorldStack` stack's **Outputs** tab.

Visiting that URL should return:

```json
{"message": "hello world"}
```

---

## Local development

```bash
cd app
pip install -r requirements.txt fastapi[standard]
fastapi dev main.py
```

Then visit `http://localhost:8000`.

## Cost

At hobby/learning traffic levels this should cost **$0/month** — you're well
within the Lambda free tier (1M requests + 400,000 GB-seconds of compute per
month, always free). The only things that could ever cost money: the small
S3 bucket CDK's bootstrap creates for deployment assets (negligible, a few
KB), and Lambda usage beyond the free tier.
