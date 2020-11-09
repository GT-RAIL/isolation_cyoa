#!/usr/bin/env bash
# Run the website docker container. If there is already a container running,
# then exec into the container

set -e

# Get the current script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Run the docker container
cd ${DIR}/..


# Create the container OR exec into it
docker run -d --rm --gpus all --privileged --name isolation_cyoa --net=host \
    -v $(pwd):/home/banerjs/website \
    -v $CODEBASE_DIR/isolation/models:/notebooks \
    -v $DATABASE_DIR/arbitration:/home/banerjs/data \
    banerjs/fault-isolation:cyoa_analysis jupyter notebook --ip=0.0.0.0 --port=9000 \
|| docker exec -it isolation_cyoa "$@"

# Recommended command to run visdom
# docker exec -d isolation_cyoa /bin/bash -c 'source /venv_entrypoint.sh && python -m visdom.server -port 8080'
