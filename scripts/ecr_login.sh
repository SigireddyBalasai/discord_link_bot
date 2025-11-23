#!/bin/bash
set -e

# Login to AWS ECR using aws-cli
if ! [ -x /usr/bin/aws ]; then
  echo "aws-cli missing"
  exit 1
fi

# Read ECR_REPO from file
if [ -f ECR_REPO ]; then
  ECR_REPO=$(cat ECR_REPO)
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

aws ecr get-login-password --region us-east-1 | /usr/local/bin/docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com

echo "Logged into ECR"
exit 0
