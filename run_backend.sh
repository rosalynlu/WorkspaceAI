#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="workspaceai-backend"
CONTAINER_NAME="workspaceai-backend"

docker build -t "$IMAGE_NAME" .

if docker ps -a --format '{{.Names}}' | grep -qx "$CONTAINER_NAME"; then
  docker rm -f "$CONTAINER_NAME" >/dev/null
fi

docker run --name "$CONTAINER_NAME" -p 8000:8000 "$IMAGE_NAME"
