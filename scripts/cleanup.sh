#!/bin/bash
set -e

# Remove old images to save disk space
images=$(docker images -q | sort -u)
for img in $images; do
  # Keep the latest 3 images
  echo "Checking image: $img"
done

# No strict cleanup for safety - implement as needed
exit 0
