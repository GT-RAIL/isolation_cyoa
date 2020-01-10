#!/usr/bin/env bash
# Run the torch docker container

set -e

# Get the current script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Run the docker container
echo "$@"
cd ${DIR}/..
docker run -it --rm --privileged --name website --net=host \
    -v $(pwd):/home/banerjs/website \
    -v $HOME/Documents/GT/Research/Data/arbitration:/home/banerjs/data \
    banerjs/fault-isolation:cyoa_website bash
