#!/usr/bin/env bash
# Setup CodeCommit remote in this repo.
# Usage: scripts/setup_codecommit.sh <repo-name> [<remote-name>=codecommit]

set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "USAGE: $0 <codecommit_repo_name> [remote-name]"
  exit 2
fi

REPO_NAME=$1
REMOTE_NAME=${2:-codecommit}

AWS_REGION=${AWS_REGION:-ap-south-1}

# create the repo if it doesn't exist
if ! aws codecommit get-repository --repository-name ${REPO_NAME} --region ${AWS_REGION} >/dev/null 2>&1; then
  echo "Creating CodeCommit repository ${REPO_NAME} in ${AWS_REGION}"
  aws codecommit create-repository --repository-name ${REPO_NAME} --repository-description "CodeCommit repo for ${REPO_NAME}" --region ${AWS_REGION}
fi

# fetch clone url
CLONE_URL_HTTP=$(aws codecommit get-repository --repository-name ${REPO_NAME} --region ${AWS_REGION} --query repositoryMetadata.cloneUrlHttp --output text)
CLONE_URL_SSH=$(aws codecommit get-repository --repository-name ${REPO_NAME} --region ${AWS_REGION} --query repositoryMetadata.cloneUrlSsh --output text)

# configure git credential helper for HTTP (recommended)
git config --global credential.helper '!aws codecommit credential-helper $@'
git config --global credential.UseHttpPath true

# add remote if missing
if git remote get-url ${REMOTE_NAME} >/dev/null 2>&1; then
  echo "Remote ${REMOTE_NAME} already exists: $(git remote get-url ${REMOTE_NAME})"
else
  git remote add ${REMOTE_NAME} ${CLONE_URL_HTTP}
  echo "Added remote ${REMOTE_NAME} -> ${CLONE_URL_HTTP}"
fi

# show remotes
git remote -v

echo "To push current branch to CodeCommit: git push ${REMOTE_NAME} HEAD:refs/heads/main"

echo "If you prefer SSH, add your public key to IAM user and set the remote to the SSH clone URL."

exit 0
