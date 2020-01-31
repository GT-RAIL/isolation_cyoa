#!/usr/bin/env bash
# Build the cyoa docker container. This will not work everywhere...

set -ex

# Get the current script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Build the docker file; make sure to set the context
cd ${DIR}/..

if [[ $1 == "web" ]]; then
    echo "Building $1"
    shift
    docker build -t banerjs/fault-isolation:cyoa_website -f docker/website.dockerfile --build-arg UID=$(id -u) $@ .
elif [[ $1 == "analysis" ]]; then
    echo "Building $1"
    shift
    docker build -t banerjs/fault-isolation:cyoa_analysis -f docker/analysis.dockerfile --build-arg UID=$(id -u) $@ .
else
    echo "Usage: build_docker.sh [web|analysis]"
    exit 1
fi
