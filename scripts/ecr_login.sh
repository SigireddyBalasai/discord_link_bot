#!/bin/bash
set -e

# Login to AWS ECR using aws-cli
if ! command -v aws >/dev/null 2>&1 || ! command -v docker >/dev/null 2>&1; then
  echo "aws-cli or docker missing"
  exit 1
fi

# Read ECR_REPO from file
if [ -f ECR_REPO ]; then
  ECR_REPO=$(cat ECR_REPO)
fi

REGION=us-east-1

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com

echo "Logged into ECR"
exit 0
