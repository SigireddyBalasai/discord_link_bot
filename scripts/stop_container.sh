#!/bin/bash
set -e

# Read ECR_REPO from file to derive container name
if [ -f ECR_REPO ]; then
  ECR_REPO=$(cat ECR_REPO)
  BOT_NAME=$(echo $ECR_REPO | sed 's/-ecr_repository$//')
else
  BOT_NAME="discord-bot"
fi

CONTAINER_NAME=${CONTAINER_NAME:-$BOT_NAME}

# Stop and remove the running container if exists
if docker ps -q --filter "name=${CONTAINER_NAME}" | grep -q .; then
  docker stop ${CONTAINER_NAME} || true
  docker rm ${CONTAINER_NAME} || true
fi

exit 0
