#!/bin/bash
set -e

echo "Starting Discord bot container..."

# Read the ECR repo name
ECR_REPO=$(cat /tmp/deploy/ECR_REPO)
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
IMAGE_URI=$ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/$ECR_REPO:latest

echo "Pulling image: $IMAGE_URI"
docker pull $IMAGE_URI

echo "Starting container..."
docker run -d --name discord-bot --restart unless-stopped -p 80:80 $IMAGE_URI

echo "Container started."