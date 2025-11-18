Notes

- For CI, this repository uses AWS CodeCommit + CodeBuild + CodePipeline. If you prefer another system, you can implement equivalent steps to build the Docker image and call CodeDeploy.
# Discord Link Bot — local deploy

This repo is set up to deploy the Discord bot to a single EC2 instance using CodeDeploy. Local deployment (via the included `pre-push` hook or CodeCommit + CodePipeline) is the recommended developer workflow.

Local deploy steps

1. Ensure these tools are installed on your machine:
   - aws-cli
   - docker
   - jq

2. Configure AWS credentials and region:

```bash
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_REGION=ap-south-1
```

3. Create or use an existing `ECR` repo and S3 bucket for CodeDeploy bundles (see infra/README.md for `terraform` option). Use `.env` to store these environment variables in the repo:

```
ECR_REPO=discord-link-bot
S3_BUCKET=discord-bot-deploy-471112640567
CODEDEPLOY_APP=discord-bot-app
CODEDEPLOY_GROUP=discord-bot-deployment-group
```

4. Enable the git hook:

```bash
cp .githooks/* .git/hooks/
chmod +x .git/hooks/*
```

You can enable the local deploy step performed by the hook by exporting the environment variable `LOCAL_DEPLOY=true`. Example:

```bash
export LOCAL_DEPLOY=true
# optional: change the remote name if you use a different remote for CodeCommit
export CODECOMMIT_REMOTE=codecommit
```

CodeCommit setup and mirror
---------------------------

We now use AWS CodeCommit as the primary remote for this repo. If you want to mirror the repository to AWS CodeCommit and push code there as well, you can run the setup script (or use it to switch to CodeCommit):

```bash
scripts/setup_codecommit.sh discord-link-bot
```

- Create a CodeCommit repo named `discord-link-bot` (if not exists)
- Configure the AWS CodeCommit credential helper for Git
- Add a Git remote called `codecommit` pointing at the AWS repo
This will:
- Create a CodeCommit repo named `discord-link-bot` (if not exists)
- Configure the AWS CodeCommit credential helper for Git
- Add a Git remote called `codecommit` pointing at the AWS repo

Continuous deployment (automated)
---------------------------------

Automated CI/CD (CodeCommit → CodeBuild → CodeDeploy) can be enabled by setting `codecommit_name` and `ecr_repo` in `infra/terraform.tfvars` or passing them via `-var-file` to `terraform`. The pipeline will watch the `main` branch of the CodeCommit repo and trigger a CodeBuild job which:

- Builds the Docker image and pushes it to ECR
- Produces a deployment artifact (appspec + scripts)
- Automatically triggers a CodeDeploy deployment using the artifact

This provides an automated push-to-deploy flow using CodeCommit → CodeBuild → CodeDeploy.
To make CodeCommit the canonical remote you push to (optional) you can run:

```bash
# rename the remote to origin (optional, sets CodeCommit as default remote)
git remote set-url origin $(terraform output -raw codecommit_clone_url_http)
```
- Create a CodeCommit repo named `discord-link-bot` (if not exists)
- Configure the AWS CodeCommit credential helper for Git
- Add a Git remote called `codecommit` pointing at the AWS repo

Push to CodeCommit with:

```bash
git push codecommit HEAD:refs/heads/main
```

If you renamed the CodeCommit remote to `origin` you can still use the pre-push hook — set `CODECOMMIT_REMOTE=origin` before pushing.

Note: for SSH clone/push, add your SSH public key to your IAM user in the AWS Console (or upload via CLI). Then change the remote to the SSH clone url shown by `terraform output codecommit_clone_url_ssh` (if using Terraform) or `aws codecommit get-repository ...`.

5. `git push` will trigger the pre-push hook that builds the docker image, pushes it to ECR, prepares the CodeDeploy bundle, uploads it to S3, and then triggers CodeDeploy.

Notes

- Protect secrets and never commit credentials.
- Protect secrets and never commit credentials.
