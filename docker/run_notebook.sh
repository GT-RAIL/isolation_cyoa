#!/usr/bin/env bash
# Run the website docker container. If there is already a container running,
# then exec into the container

set -e

# Get the current script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Run the docker container
cd ${DIR}/..


# Create the container OR exec into it
docker run -d --rm --runtime=nvidia --privileged --name analysis --net=host \
    -v $(pwd):/home/banerjs/website \
    -v $CODEBASE_DIR/isolation/models:/notebooks \
    -v $DATABASE_DIR/arbitration:/home/banerjs/data \
    banerjs/fault-isolation:cyoa_analysis \
|| docker exec -it analysis "$@"

# Recommended command to run visdom
# docker exec -d analysis /bin/bash -c 'source /venv_entrypoint.sh && python -m visdom.server -port 8080'
