#!/bin/bash
set -e

# Stop and remove the running container if exists
if docker ps -q --filter "name=discord-bot" | grep -q .; then
  docker stop discord-bot || true
  docker rm discord-bot || true
fi

exit 0
