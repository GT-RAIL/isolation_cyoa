#!/usr/bin/env bash
# Run the website docker container. If there is already a container running,
# then exec into the container

set -e

# Get the current script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Run the docker container
cd ${DIR}/..


# Create the container OR exec into it
docker run -it --rm --privileged --name website --net=host \
    -v $(pwd):/home/banerjs/website \
    -v $HOME/Documents/GT/Research/Data/arbitration:/home/banerjs/data \
    banerjs/fault-isolation:cyoa_website bash \
|| docker exec -it website bash
