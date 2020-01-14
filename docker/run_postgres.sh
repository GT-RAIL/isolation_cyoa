#!/usr/bin/env bash
# Run the postgres container. If there is already a container running, then exec
# into a psql for that container. If the container is stopped, then start it

set -e

#

# No --rm because we want to save state
docker run -d --name postgres -p 5432:5432 --user "$(id -u):$(id -g)" \
    -v /etc/passwd:/etc/passwd:ro \
    -v /home/banerjs/Documents/GT/Research/Data/arbitration/2019-12-09/postgres/data:/var/lib/postgresql/data \
    postgres:11 \
|| docker exec -it postgres psql -U banerjs -d cyoa \
|| docker exec -it postgres psql -U postgres \
|| docker start postgres
