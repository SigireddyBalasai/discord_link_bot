#!/bin/bash
set -e

# Login to AWS ECR using aws-cli
if ! command -v aws >/dev/null 2>&1 || ! command -v docker >/dev/null 2>&1; then
  echo "aws-cli or docker missing"
  exit 1
fi

REGION=$(curl -s 'http://169.254.169.254/latest/dynamic/instance-identity/document' | jq -r .region || echo "${AWS_REGION}")
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

if [ -z "$ECR_REPO" ]; then
  echo "ECR_REPO not set"
  exit 1
fi

aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com

echo "Logged into ECR"
exit 0
