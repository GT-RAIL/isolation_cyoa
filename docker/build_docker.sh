#!/usr/bin/env bash
# Build the cyoa docker container. This will not work everywhere...

set -ex

# Get the current script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Check that we have enough arguments
if [[ $# -eq 0 ]]; then
    echo "Usage: build_docker.sh [website|analysis]"
    exit 1
else
    MODE=$1
    shift
fi

# Build the docker file; make sure to set the context
cd ${DIR}/..

echo "Building $MODE"
docker build -t banerjs/fault-isolation:cyoa_${MODE} -f docker/${MODE}.dockerfile --build-arg UID=$(id -u) $@ .
