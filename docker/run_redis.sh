#!/usr/bin/env bash
# Run the redis container. If there is already a container running, then exec
# into a bash for that container. If the container is stopped, then start it

set -e

# No --rm because we want to save state
docker run -d --name redis -p 6379:6379 --user "$(id -u):$(id -g)" \
    -v /etc/passwd:/etc/passwd:ro \
    -v /home/banerjs/Documents/GT/Research/Data/arbitration/2019-12-09/db/redis:/data \
    redis:5 redis-server --appendonly yes \
|| docker exec -it redis redis-cli \
|| docker start redis
